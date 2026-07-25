from backend.services.localization_service import LocalizationService

loc = LocalizationService()

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTableView, QHeaderView, QLabel
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
import os

class DiagnosticsTableModel(QAbstractTableModel):
    def __init__(self, diagnostics_data, parent=None):
        super().__init__(parent)
        self.diagnostics = diagnostics_data
        self.headers = ["ID", "Name", "Type", "Version", "Reachable", "Cache Refreshed", "Models", "Voices"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.diagnostics)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        diag = self.diagnostics[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0: return diag.get("provider_id")
            if col == 1: return diag.get("name")
            if col == 2: return diag.get("type")
            if col == 3: return diag.get("version")
            if col == 4: return str(diag.get("reachable"))
            if col == 5: return diag.get("last_refreshed")
            if col == 6: return str(diag.get("models_count"))
            if col == 7: return str(diag.get("voices_count"))
            
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

class ProviderDiagnosticsWindow(QWidget):
    def __init__(self, diagnostics_data):
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        info_label = QLabel(loc.translate("desc_diagnostics"))
        info_label.setStyleSheet("color: #6B7280; font-style: italic;")
        layout.addWidget(info_label)
        
        self.table = QTableView()
        self.model = DiagnosticsTableModel(diagnostics_data)
        self.table.setModel(self.model)
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
