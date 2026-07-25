from backend.services.localization_service import LocalizationService

loc = LocalizationService()

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QLineEdit, QComboBox, QMessageBox, QSplitter, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from backend.template.template_manager import TemplateManager

class TemplateBrowserWindow(QWidget):
    template_selected = Signal(str)

    def __init__(self, template_manager: TemplateManager):
        super().__init__()
        self.tm = template_manager
        self.init_ui()
        self.refresh_list()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(loc.translate("placeholder_search_templates"))
        self.search_edit.textChanged.connect(self.refresh_list)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Podcast", "TikTok", "YouTube", "Custom"])
        self.category_combo.currentTextChanged.connect(self.refresh_list)
        
        self.fav_checkbox = QCheckBox(loc.translate("cb_favorites_only"))
        self.fav_checkbox.stateChanged.connect(self.refresh_list)
        
        toolbar.addWidget(self.search_edit)
        toolbar.addWidget(self.category_combo)
        toolbar.addWidget(self.fav_checkbox)
        layout.addLayout(toolbar)
        
        # Splitter for Master-Detail view
        splitter = QSplitter(Qt.Horizontal)
        
        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        splitter.addWidget(self.list_widget)
        
        # Detail Panel
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        self.detail_title = QLabel(loc.translate("placeholder_select_template"))
        self.detail_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.detail_desc = QLabel("")
        self.detail_desc.setWordWrap(True)
        
        self.use_btn = QPushButton(loc.translate("btn_use_template"))
        self.use_btn.setStyleSheet("background-color: #4F46E5; color: white; font-weight: bold;")
        self.use_btn.clicked.connect(self.use_selected_template)
        
        self.delete_btn = QPushButton(loc.translate("btn_delete"))
        self.delete_btn.clicked.connect(self.delete_template)
        
        detail_layout.addWidget(self.detail_title)
        detail_layout.addWidget(self.detail_desc)
        detail_layout.addStretch()
        
        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self.use_btn)
        actions_layout.addWidget(self.delete_btn)
        detail_layout.addLayout(actions_layout)
        
        splitter.addWidget(detail_widget)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)


    def retranslate_ui(self):
        loc = LocalizationService()
        if hasattr(self, 'new_btn'): self.new_btn.setText(loc.translate("btn_new_template"))
        if hasattr(self, 'delete_btn'): self.delete_btn.setText(loc.translate("btn_delete_template"))

    def refresh_list(self):
        self.list_widget.clear()
        search_text = self.search_edit.text().lower()
        cat_filter = self.category_combo.currentText()
        fav_filter = self.fav_checkbox.isChecked()
        
        templates = self.tm.list_templates()
        for tpl in templates:
            # Filters
            if cat_filter != "All" and tpl.metadata.category != cat_filter:
                continue
            if fav_filter and not tpl.metadata.favorite:
                continue
            if search_text and search_text not in tpl.metadata.name.lower() and search_text not in tpl.metadata.description.lower():
                continue
                
            item = QListWidgetItem(f"{tpl.metadata.name} (v{tpl.metadata.version})")
            item.setData(Qt.UserRole, tpl.metadata.template_id)
            self.list_widget.addItem(item)

    def on_selection_changed(self):
        items = self.list_widget.selectedItems()
        if not items:
            self.detail_title.setText(loc.translate("placeholder_select_template"))
            self.detail_desc.setText("")
            return
            
        tpl_id = items[0].data(Qt.UserRole)
        tpl = self.tm.load_template(tpl_id)
        if tpl:
            self.detail_title.setText(tpl.metadata.name)
            desc_text = f"<b>Author:</b> {tpl.metadata.author}<br/><br/>"
            desc_text += f"{tpl.metadata.description}<br/><br/>"
            
            # Payload summary
            has_chars = len(tpl.payload.character_profiles) > 0
            has_pipe = len(tpl.payload.pipeline_options) > 0
            
            desc_text += "<b>Includes:</b><ul>"
            if has_chars: desc_text += "<li>Character Profiles</li>"
            if has_pipe: desc_text += "<li>Pipeline Overrides</li>"
            desc_text += "</ul>"
            
            self.detail_desc.setText(desc_text)

    def use_selected_template(self):
        items = self.list_widget.selectedItems()
        if not items: return
        tpl_id = items[0].data(Qt.UserRole)
        self.template_selected.emit(tpl_id)
        self.close()

    def delete_template(self):
        items = self.list_widget.selectedItems()
        if not items: return
        tpl_id = items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(self, loc.translate("msg_confirm_delete"), loc.translate("msg_delete_template_confirm"), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.tm.delete_template(tpl_id)
            self.refresh_list()
