from backend.services.localization_service import LocalizationService

loc = LocalizationService()

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QTableView, QHeaderView, QPushButton, QLabel, QLineEdit,
    QComboBox, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
from PySide6.QtGui import QAction, QColor

from backend.translation.review_manager import ReviewManager, ReviewSegment
from backend.translation.translation_memory import TranslationMemory
from backend.translation.history_manager import HistoryManager
from backend.translation.glossary import GlossaryManager, GlossaryEntry

class ReviewTableModel(QAbstractTableModel):
    def __init__(self, segments, parent=None):
        super().__init__(parent)
        self.segments = segments
        self.headers = ["ID", "Start", "End", "Speaker", "Original", "Translated", "Status", "Freeze", "Comment"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.segments)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        seg = self.segments[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if col == 0: return seg.segment_id
            if col == 1: return f"{seg.start_time:.2f}"
            if col == 2: return f"{seg.end_time:.2f}"
            if col == 3: return seg.speaker
            if col == 4: return seg.original
            if col == 5: return seg.translated
            if col == 6: return seg.status
            if col == 7: return "Yes" if seg.is_frozen else "No"
            if col == 8: return seg.comment
            
        if role == Qt.BackgroundRole:
            if seg.is_frozen:
                return QColor("#E5E7EB")
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def flags(self, index):
        flags = super().flags(index)
        col = index.column()
        if col in [5, 8]:
            flags |= Qt.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
            
        seg = self.segments[index.row()]
        col = index.column()
        
        if role == Qt.EditRole:
            if col == 5:
                seg.translated = value
                seg.status = "Reviewed"
                self.dataChanged.emit(index, index, [Qt.DisplayRole])
                return True
            if col == 8:
                seg.comment = value
                self.dataChanged.emit(index, index, [Qt.DisplayRole])
                return True
        return False


class TranslationReviewWindow(QWidget):
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        
        self.review_manager = ReviewManager(project_id)
        self.memory_manager = TranslationMemory(project_id)
        self.history_manager = HistoryManager(project_id)
        self.glossary_manager = GlossaryManager(project_id)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        
        self.review_tab = QWidget()
        self.init_review_tab()
        self.tabs.addTab(self.review_tab, loc.translate("tab_review_center"))
        
        self.tm_tab = QWidget()
        self.init_tm_tab()
        self.tabs.addTab(self.tm_tab, loc.translate("tab_translation_memory"))
        
        self.glossary_tab = QWidget()
        self.init_glossary_tab()
        self.tabs.addTab(self.glossary_tab, loc.translate("title_glossary_manager"))
        
        layout.addWidget(self.tabs)
        
        action_layout = QHBoxLayout()
        self.render_all_btn = QPushButton(loc.translate("btn_render_all"))
        self.render_all_btn.clicked.connect(self.on_render_all)
        
        self.render_selected_btn = QPushButton(loc.translate("btn_render_selected"))
        self.render_selected_btn.clicked.connect(self.on_render_selected)
        
        action_layout.addStretch()
        action_layout.addWidget(self.render_selected_btn)
        action_layout.addWidget(self.render_all_btn)
        
        layout.addLayout(action_layout)

    def init_review_tab(self):
        layout = QVBoxLayout(self.review_tab)
        
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(loc.translate("placeholder_search"))
        filter_layout.addWidget(QLabel(loc.translate("lbl_search")))
        filter_layout.addWidget(self.search_input)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        self.review_table = QTableView()
        self.review_model = ReviewTableModel(self.review_manager.get_all_segments())
        self.review_model.dataChanged.connect(self.on_review_data_changed)
        
        self.review_table.setModel(self.review_model)
        self.review_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.review_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.review_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.review_table.customContextMenuRequested.connect(self.show_review_context_menu)
        
        layout.addWidget(self.review_table)

    def on_review_data_changed(self, top_left, bottom_right, roles):
        row = top_left.row()
        seg = self.review_model.segments[row]
        self.review_manager.update_segment(seg)
        self.memory_manager.add_term(seg.original, seg.translated, source_type="User Edited")
        self.history_manager.log_event(seg.segment_id, "", seg.translated, "User")
        
    def show_review_context_menu(self, pos):
        menu = QMenu(self)
        toggle_freeze_action = QAction(loc.translate("btn_toggle_freeze"), self)
        toggle_freeze_action.triggered.connect(self.toggle_freeze_selected)
        menu.addAction(toggle_freeze_action)
        
        set_approved_action = QAction(loc.translate("btn_mark_approved"), self)
        set_approved_action.triggered.connect(self.mark_approved_selected)
        menu.addAction(set_approved_action)
        
        menu.exec(self.review_table.viewport().mapToGlobal(pos))
        
    def toggle_freeze_selected(self):
        indexes = self.review_table.selectionModel().selectedRows()
        for idx in indexes:
            seg = self.review_model.segments[idx.row()]
            seg.is_frozen = not seg.is_frozen
            self.review_manager.update_segment(seg)
        self.review_model.layoutChanged.emit()
        
    def mark_approved_selected(self):
        indexes = self.review_table.selectionModel().selectedRows()
        for idx in indexes:
            seg = self.review_model.segments[idx.row()]
            seg.status = "Approved"
            self.review_manager.update_segment(seg)
        self.review_model.layoutChanged.emit()

    def init_tm_tab(self):
        layout = QVBoxLayout(self.tm_tab)
        layout.addWidget(QLabel(loc.translate("desc_translation_memory")))
        
    def init_glossary_tab(self):
        layout = QVBoxLayout(self.glossary_tab)
        layout.addWidget(QLabel(loc.translate("title_glossary_manager")))
        
    def on_render_all(self):
        QMessageBox.information(self, loc.translate("btn_render_all"), "Saved all translations and resuming pipeline rendering...")
        self.close()
        
    def on_render_selected(self):
        QMessageBox.information(self, loc.translate("btn_render_selected"), "Render Selected feature not fully hooked up in backend yet.")
