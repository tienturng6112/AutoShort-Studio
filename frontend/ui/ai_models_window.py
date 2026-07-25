import qasync
from backend.services.localization_service import LocalizationService
loc = LocalizationService()

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView, 
    QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
import os

class AIModelsTableModel(QAbstractTableModel):
    def __init__(self, models, parent=None):
        super().__init__(parent)
        self.models = models
        self.headers = ["Name", "ID", "Engine", "Version", "Size (MB)"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.models)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        m = self.models[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0: return m.get("name", "Unknown")
            if col == 1: return m.get("id", "Unknown")
            if col == 2: return m.get("engine", "Unknown").capitalize()
            if col == 3: return m.get("version", "1.0.0")
            if col == 4: return f"{m.get('size_bytes', 0) / (1024*1024):.1f}"
            
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def update_data(self, new_models):
        self.beginResetModel()
        self.models = new_models
        self.endResetModel()

class AIModelsWindow(QWidget):
    def __init__(self):
        super().__init__()
        from backend.models.model_manager import ModelManager
        self.model_manager = ModelManager("models/omnivoice")
        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("<h2>" + loc.translate("ai_models_workspace") + "</h2>")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton(loc.translate("btn_force_refresh"))
        self.refresh_btn.clicked.connect(self.refresh_table)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.model = AIModelsTableModel([])
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        # Actions
        actions_layout = QHBoxLayout()
        self.delete_btn = QPushButton(loc.translate("btn_delete_model"))
        self.delete_btn.setStyleSheet("color: red;")
        self.delete_btn.clicked.connect(self.delete_model)
        
        self.update_btn = QPushButton(loc.translate("btn_update_model"))
        
        self.download_btn = QPushButton(loc.translate("btn_download_model"))
        self.download_btn.clicked.connect(self.download_model)
        
        self.import_btn = QPushButton(loc.translate("btn_import"))
        self.export_btn = QPushButton(loc.translate("btn_export"))
        
        actions_layout.addWidget(self.import_btn)
        actions_layout.addWidget(self.export_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.delete_btn)
        actions_layout.addWidget(self.update_btn)
        actions_layout.addWidget(self.download_btn)
        
        layout.addLayout(actions_layout)

    def refresh_table(self):
        installed = self.model_manager.detect_installed_models()
        self.model.update_data(installed)

    def delete_model(self):
        idx = self.table.currentIndex()
        if not idx.isValid(): return
        mid = self.model.models[idx.row()].get("id")
        
        if QMessageBox.question(self, loc.translate("confirm_delete"), f"Delete model {mid}?") == QMessageBox.Yes:
            if self.model_manager.delete_model(mid):
                self.refresh_table()

    @qasync.asyncSlot()
    async def download_model(self):
        import asyncio
        mid = "omnivoice-base-v1"
        self.download_btn.setEnabled(False)
        self.download_btn.setText(loc.translate("status_downloading"))
        
        await self.model_manager.download_model(mid, "http://example.com/model")
        
        self.refresh_table()
        self.download_btn.setEnabled(True)
        self.download_btn.setText(loc.translate("btn_download_model"))
        QMessageBox.information(self, loc.translate("success"), f"Model {mid} downloaded successfully.")
