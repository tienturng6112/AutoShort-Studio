import qasync
from backend.services.localization_service import LocalizationService
loc = LocalizationService()

import asyncio
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView, 
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal, QThread
from backend.voice.voice_manager import VoiceManager
import traceback

class AsyncPreviewThread(QThread):
    finished_preview = Signal(bytes)
    error_occurred = Signal(str)

    def __init__(self, voice_manager, text, voice_id, provider_id):
        super().__init__()
        self.vm = voice_manager
        self.text = text
        self.voice_id = voice_id
        self.provider_id = provider_id

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.vm.preview(self.text, self.voice_id, self.provider_id)
            )
            loop.close()
            self.finished_preview.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

class VoiceTableModel(QAbstractTableModel):
    def __init__(self, voices, parent=None):
        super().__init__(parent)
        self.voices = voices
        self.headers = ["Fav", "Name", "Provider", "Lang", "Gender", "ID"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.voices)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        voice = self.voices[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0: return "★" if voice.favorite else "☆"
            if col == 1: return voice.display_name
            if col == 2: return voice.provider_id
            if col == 3: return voice.language
            if col == 4: return voice.gender
            if col == 5: return voice.voice_id
            
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def update_data(self, new_voices):
        self.beginResetModel()
        self.voices = new_voices
        self.endResetModel()

class VoiceBrowserWindow(QWidget):
    voice_assigned = Signal(str, str) # voice_id, provider_id

    def __init__(self, voice_manager: VoiceManager):
        super().__init__()
        
        self.vm = voice_manager
        self._preview_thread = None
        
        from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        
        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left Sidebar (Filters)
        sidebar = QVBoxLayout()
        sidebar.addWidget(QLabel("<b>" + loc.translate("lbl_filters") + "</b>"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(loc.translate("placeholder_search_voices"))
        self.search_input.textChanged.connect(self.refresh_table)
        sidebar.addWidget(self.search_input)
        
        self.provider_filter = QComboBox()
        self.provider_filter.addItem(loc.translate("all_providers"), "")
        for p in self.vm.registry.list_providers():
            if p.provider_type == "tts":
                self.provider_filter.addItem(p.provider_id, p.provider_id)
        self.provider_filter.currentIndexChanged.connect(self.refresh_table)
        sidebar.addWidget(QLabel(loc.translate("lbl_provider")))
        sidebar.addWidget(self.provider_filter)
        
        self.gender_filter = QComboBox()
        self.gender_filter.addItems(["All", "Male", "Female", "Neutral"])
        self.gender_filter.currentIndexChanged.connect(self.refresh_table)
        sidebar.addWidget(QLabel(loc.translate("lbl_gender")))
        sidebar.addWidget(self.gender_filter)
        
        self.refresh_btn = QPushButton(loc.translate("btn_force_refresh"))
        self.refresh_btn.clicked.connect(self.force_refresh)
        sidebar.addStretch()
        sidebar.addWidget(self.refresh_btn)
        
        # Right Side (Tabs)
        right_panel = QVBoxLayout()
        
        self.tabs = QTabWidget()
        
        # Sub-widgets for tabs
        self.tab_preset = QWidget()
        self.tab_designed = QWidget()
        self.tab_cloned = QWidget()
        self.tab_favorites = QWidget()
        
        self.tabs.addTab(self.tab_preset, loc.translate("tab_preset_voices"))
        self.tabs.addTab(self.tab_designed, loc.translate("tab_designed_voices"))
        self.tabs.addTab(self.tab_cloned, loc.translate("tab_cloned_voices"))
        self.tabs.addTab(self.tab_favorites, loc.translate("tab_favorites"))
        
        self.tabs.currentChanged.connect(self.refresh_table)
        
        # Common Table
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.model = VoiceTableModel([])
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        # Action Buttons
        actions_layout = QHBoxLayout()
        self.preview_btn = QPushButton(loc.translate("btn_play_preview"))
        self.preview_btn.clicked.connect(self.play_preview)
        
        self.delete_btn = QPushButton(loc.translate("btn_delete_voice"))
        self.delete_btn.setVisible(False)
        
        self.duplicate_btn = QPushButton(loc.translate("btn_duplicate"))
        self.duplicate_btn.setVisible(False)
        
        self.export_btn = QPushButton(loc.translate("btn_export"))
        self.export_btn.setVisible(False)
        
        self.import_btn = QPushButton(loc.translate("btn_import"))
        self.import_btn.setVisible(False)
        
        self.assign_btn = QPushButton(loc.translate("btn_assign_selected"))
        self.assign_btn.setStyleSheet("background-color: #10B981; color: white; font-weight: bold;")
        self.assign_btn.clicked.connect(self.assign_voice)
        
        actions_layout.addWidget(self.import_btn)
        actions_layout.addWidget(self.export_btn)
        actions_layout.addWidget(self.duplicate_btn)
        actions_layout.addWidget(self.delete_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.preview_btn)
        actions_layout.addWidget(self.assign_btn)
        
        right_panel.addWidget(self.tabs)
        right_panel.addWidget(self.table)
        right_panel.addLayout(actions_layout)
        
        main_layout.addLayout(sidebar, 1)
        main_layout.addLayout(right_panel, 4)

    def refresh_table(self):
        query = self.search_input.text()
        filters = {}
        
        prov = self.provider_filter.currentData()
        if prov:
            filters["provider_id"] = prov
            
        gen = self.gender_filter.currentText()
        if gen != "All":
            filters["gender"] = gen
            
        # Handle active tab filtering
        active_tab = self.tabs.currentIndex()
        if active_tab == 3: # Favorites
            filters["favorite"] = True
            self.delete_btn.setVisible(False)
            self.duplicate_btn.setVisible(False)
            self.export_btn.setVisible(False)
            self.import_btn.setVisible(False)
        elif active_tab == 0: # Presets
            self.delete_btn.setVisible(False)
            self.duplicate_btn.setVisible(False)
            self.export_btn.setVisible(False)
            self.import_btn.setVisible(False)
        elif active_tab == 1: # Designed
            self.delete_btn.setVisible(True)
            self.duplicate_btn.setVisible(True)
            self.export_btn.setVisible(True)
            self.import_btn.setVisible(True)
        elif active_tab == 2: # Cloned
            self.delete_btn.setVisible(True)
            self.duplicate_btn.setVisible(True)
            self.export_btn.setVisible(True)
            self.import_btn.setVisible(True)
            
        voices = self.vm.search(query, **filters)
        
        # Local UI-side filtering for voice ID prefixes since backend search doesn't support regex/prefixes yet
        if active_tab == 0:
            voices = [v for v in voices if not (v.voice_id.startswith("clone:") or v.voice_id.startswith("design:"))]
        elif active_tab == 1:
            voices = [v for v in voices if v.voice_id.startswith("design:")]
        elif active_tab == 2:
            voices = [v for v in voices if v.voice_id.startswith("clone:")]
            
        self.model.update_data(voices)

    @qasync.asyncSlot()
    async def force_refresh(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText(loc.translate("status_refreshing"))
        await self.vm.refresh()
        
        self.refresh_table()
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText(loc.translate("btn_force_refresh"))

    def play_preview(self):
        idx = self.table.currentIndex()
        if not idx.isValid():
            return
            
        voice = self.model.voices[idx.row()]
        self.preview_btn.setEnabled(False)
        self.preview_btn.setText(loc.translate("status_generating"))
        
        self._preview_thread = AsyncPreviewThread(self.vm, "This is a preview of my voice.", voice.voice_id, voice.provider_id)
        self._preview_thread.finished_preview.connect(self.on_preview_ready)
        self._preview_thread.error_occurred.connect(self.on_preview_error)
        self._preview_thread.start()

    def on_preview_ready(self, audio_bytes):
        from PySide6.QtCore import QBuffer, QByteArray
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText(loc.translate("btn_play_preview"))
        
        if audio_bytes:
            self._buffer = QBuffer(QByteArray(audio_bytes))
            self._buffer.open(QBuffer.ReadOnly)
            self.player.setSourceDevice(self._buffer)
            self.player.play()

    def on_preview_error(self, err):
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText(loc.translate("btn_play_preview"))
        QMessageBox.warning(self, loc.translate("msg_preview_error"), f"Could not generate preview: {err}")

    def assign_voice(self):
        idx = self.table.currentIndex()
        if not idx.isValid():
            return
            
        voice = self.model.voices[idx.row()]
        self.voice_assigned.emit(voice.voice_id, voice.provider_id)
        self.close()
