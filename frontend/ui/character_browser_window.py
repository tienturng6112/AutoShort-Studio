from backend.services.localization_service import LocalizationService

loc = LocalizationService()

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView, 
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QMessageBox, QDialog, QFormLayout
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
from backend.character.character_manager import CharacterManager
from backend.character.metadata import CharacterProfile

class CharacterTableModel(QAbstractTableModel):
    def __init__(self, characters, parent=None):
        super().__init__(parent)
        self.characters = characters
        self.headers = [loc.translate("col_name"), loc.translate("col_aliases"), loc.translate("speaker_voices"), loc.translate("col_provider"), loc.translate("col_gender"), loc.translate("col_emotion")]

    def rowCount(self, parent=QModelIndex()):
        return len(self.characters)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        char = self.characters[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0: return char.display_name
            if col == 1: return ", ".join(char.aliases)
            if col == 2: return char.preferred_voice or "None"
            if col == 3: return char.preferred_provider or "None"
            if col == 4: return char.gender
            if col == 5: return char.emotion_profile
            
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def update_data(self, new_chars):
        self.beginResetModel()
        self.characters = new_chars
        self.endResetModel()

class EditCharacterDialog(QDialog):
    def __init__(self, char_mgr: CharacterManager, profile: CharacterProfile, parent=None):
        super().__init__(parent)
        self.char_mgr = char_mgr
        self.profile = profile
        self.init_ui()
        
    def init_ui(self):
        layout = QFormLayout(self)
        
        self.name_edit = QLineEdit(self.profile.display_name)
        layout.addRow(loc.translate("lbl_name"), self.name_edit)
        
        self.aliases_edit = QLineEdit(", ".join(self.profile.aliases))
        layout.addRow(loc.translate("lbl_aliases"), self.aliases_edit)
        
        self.gender_combo = QComboBox()
        for gk, gv in [("gender_unknown", "Unknown"), ("gender_male", "Male"), ("gender_female", "Female"), ("gender_neutral", "Neutral")]:
            self.gender_combo.addItem(loc.translate(gk), gv)
        self.gender_combo.setCurrentText(self.profile.gender)
        self.lbl_gender = QLabel(loc.translate("lbl_gender"))
        layout.addRow(self.lbl_gender, self.gender_combo)
        
        self.emotion_combo = QComboBox()
        for ek, ev in [("emotion_neutral", "Neutral"), ("emotion_happy", "Happy"), ("emotion_serious", "Serious"), ("emotion_angry", "Angry"), ("emotion_calm", "Calm"), ("emotion_energetic", "Energetic")]:
            self.emotion_combo.addItem(loc.translate(ek), ev)
        self.emotion_combo.setCurrentText(self.profile.emotion_profile)
        layout.addRow(loc.translate("lbl_emotion_preset"), self.emotion_combo)
        
        self.save_btn = QPushButton(loc.translate("btn_save"))
        self.save_btn.clicked.connect(self.save)
        layout.addRow(save_btn)
        
    def save(self):
        aliases = [a.strip() for a in self.aliases_edit.text().split(",") if a.strip()]
        self.char_mgr.update_character(
            self.profile.character_id,
            display_name=self.name_edit.text().strip(),
            aliases=aliases,
            gender=self.gender_combo.currentData() or self.gender_combo.currentText(),
            emotion_profile=self.emotion_combo.currentData() or self.emotion_combo.currentText()
        )
        self.accept()

class CharacterBrowserWindow(QWidget):
    character_assigned = Signal(str) # character_id

    def __init__(self, char_mgr: CharacterManager, voice_manager=None):
        super().__init__()
        
        self.cm = char_mgr
        self.vm = voice_manager
        
        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(loc.translate("placeholder_search_characters"))
        self.search_input.textChanged.connect(self.refresh_table)
        
        self.new_btn = QPushButton(loc.translate("btn_new_character"))
        self.new_btn.clicked.connect(self.new_character)
        
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.new_btn)
        
        # Main Table
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.model = CharacterTableModel([])
        self.table.setModel(self.model)
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Action Buttons
        actions_layout = QHBoxLayout()
        self.edit_btn = QPushButton(loc.translate("btn_edit_profile"))
        self.edit_btn.clicked.connect(self.edit_character)
        
        self.assign_voice_btn = QPushButton(loc.translate("assign_voice"))
        self.assign_voice_btn.clicked.connect(self.assign_voice)
        
        self.assign_char_btn = QPushButton(loc.translate("btn_link_speaker"))
        self.assign_char_btn.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold;")
        self.assign_char_btn.clicked.connect(self.link_speaker)
        
        actions_layout.addWidget(self.edit_btn)
        actions_layout.addWidget(self.assign_voice_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.assign_char_btn)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.table)
        layout.addLayout(actions_layout)


    def retranslate_ui(self):
        loc = LocalizationService()
        if hasattr(self, 'new_btn'):
            self.new_btn.setText(loc.translate("btn_new_character"))
        if hasattr(self, 'edit_btn'):
            self.edit_btn.setText(loc.translate("btn_edit_profile"))
        if hasattr(self, 'assign_voice_btn'):
            self.assign_voice_btn.setText(loc.translate("assign_voice"))
        if hasattr(self, 'assign_char_btn'):
            self.assign_char_btn.setText(loc.translate("btn_link_speaker"))
        if hasattr(self, 'search_input'):
            self.search_input.setPlaceholderText(loc.translate("placeholder_search_characters"))
        # Update gender combo texts
        if hasattr(self, 'gender_combo'):
            for i in range(self.gender_combo.count()):
                code = self.gender_combo.itemData(i)
                if code:
                    self.gender_combo.setItemText(i, loc.translate(f"gender_{code.lower()}"))
        # Update emotion combo texts
        if hasattr(self, 'emotion_combo'):
            for i in range(self.emotion_combo.count()):
                code = self.emotion_combo.itemData(i)
                if code:
                    self.emotion_combo.setItemText(i, loc.translate(f"emotion_{code.lower()}"))

    def refresh_table(self):
        query = self.search_input.text().lower()
        chars = self.cm.list_characters()
        
        if query:
            filtered = []
            for c in chars:
                if query in c.display_name.lower() or any(query in a.lower() for a in c.aliases):
                    filtered.append(c)
            chars = filtered
            
        self.model.update_data(chars)

    def new_character(self):
        profile = self.cm.create_character(loc.translate("btn_new_character"))
        self.refresh_table()
        
        # Auto open edit
        idx = len(self.model.characters) - 1
        dlg = EditCharacterDialog(self.cm, profile, self)
        if dlg.exec():
            self.refresh_table()

    def edit_character(self):
        idx = self.table.currentIndex()
        if not idx.isValid(): return
        
        profile = self.model.characters[idx.row()]
        dlg = EditCharacterDialog(self.cm, profile, self)
        if dlg.exec():
            self.refresh_table()

    def assign_voice(self):
        idx = self.table.currentIndex()
        if not idx.isValid(): return
        
        profile = self.model.characters[idx.row()]
        if not self.vm:
            QMessageBox.warning(self, loc.translate("msg_error"), loc.translate("msg_voicemgr_not_init"))
            return
            
        from frontend.ui.voice_browser_window import VoiceBrowserWindow
        self.voice_browser = VoiceBrowserWindow(self.vm)
        
        def on_voice_assigned(voice_id, provider_id):
            self.cm.assign_voice(profile.character_id, voice_id, provider_id)
            self.refresh_table()
            
        self.voice_browser.voice_assigned.connect(on_voice_assigned)
        self.voice_browser.show()

    def link_speaker(self):
        idx = self.table.currentIndex()
        if not idx.isValid(): return
        profile = self.model.characters[idx.row()]
        self.character_assigned.emit(profile.character_id)
        self.close()
