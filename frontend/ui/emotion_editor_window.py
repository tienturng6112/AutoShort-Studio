from backend.services.localization_service import LocalizationService

loc = LocalizationService()

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView, 
    QLabel, QPushButton, QMessageBox, QComboBox, QSlider
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
import json
import os
from backend.speech.models import Transcript

class EmotionTableModel(QAbstractTableModel):
    def __init__(self, transcript: Transcript = None, parent=None):
        super().__init__(parent)
        self.transcript = transcript
        self.headers = ["ID", "Speaker", "Original Text", "Emotion", "Intensity", "Override"]

    def rowCount(self, parent=QModelIndex()):
        if not self.transcript: return 0
        return len(self.transcript.segments)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not self.transcript:
            return None
            
        seg = self.transcript.segments[index.row()]
        col = index.column()
        
        emotion_data = getattr(seg, "emotion", {}) or {}
        emotion_id = emotion_data.get("emotion_id", "Neutral")
        intensity = emotion_data.get("intensity", 1.0)
        is_override = emotion_data.get("user_override", False)
        
        if role == Qt.DisplayRole:
            if col == 0: return str(seg.id)
            if col == 1: return seg.speaker_id or "Unknown"
            if col == 2: return seg.text
            if col == 3: return emotion_id
            if col == 4: return f"{intensity:.1f}"
            if col == 5: return "Yes" if is_override else "No"
            
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def update_data(self, transcript):
        self.beginResetModel()
        self.transcript = transcript
        self.endResetModel()

class EmotionEditorWindow(QWidget):
    def __init__(self, project_dir: str):
        super().__init__()
        self.project_dir = project_dir
        self.transcript = None
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Warning Banner (if capabilities missing)
        self.warning_label = QLabel(loc.translate("emotion_warning"))
        self.warning_label.setStyleSheet("color: #D97706; font-weight: bold; padding: 5px; background-color: #FEF3C7; border-radius: 4px;")
        
        # Main Table
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.model = EmotionTableModel()
        self.table.setModel(self.model)
        
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        # Editor Panel
        editor_layout = QHBoxLayout()
        
        self.emotion_combo = QComboBox()
        for ek, ev in [("emotion_neutral", "Neutral"), ("emotion_happy", "Happy"), ("emotion_sad", "Sad"), ("emotion_angry", "Angry"), ("emotion_excited", "Excited"), ("emotion_calm", "Calm")]:
            self.emotion_combo.addItem(loc.translate(ek), ev)
        
        self.intensity_slider = QSlider(Qt.Horizontal)
        self.intensity_slider.setRange(0, 10)
        self.intensity_slider.setValue(10)
        self.intensity_slider.setFixedWidth(150)
        
        self.apply_btn = QPushButton(loc.translate("btn_apply_override"))
        self.apply_btn.clicked.connect(self.apply_override)
        
        self.reset_btn = QPushButton(loc.translate("btn_reset_auto"))
        self.reset_btn.clicked.connect(self.reset_auto)
        
        editor_layout.addWidget(QLabel(loc.translate("lbl_emotion")))
        editor_layout.addWidget(self.emotion_combo)
        editor_layout.addWidget(QLabel(loc.translate("lbl_intensity")))
        editor_layout.addWidget(self.intensity_slider)
        editor_layout.addWidget(self.apply_btn)
        editor_layout.addWidget(self.reset_btn)
        editor_layout.addStretch()
        
        # Save Button
        self.save_btn = QPushButton(loc.translate("btn_save_all_changes"))
        self.save_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold;")
        self.save_btn.clicked.connect(self.save_data)
        
        layout.addWidget(self.warning_label)
        layout.addWidget(self.table)
        layout.addLayout(editor_layout)
        layout.addWidget(self.save_btn)


    def retranslate_ui(self):
        loc = LocalizationService()
        if hasattr(self, 'warning_label'):
            self.warning_label.setText(loc.translate("emotion_warning"))
        if hasattr(self, 'apply_btn'):
            self.apply_btn.setText(loc.translate("btn_apply_override"))
        if hasattr(self, 'reset_btn'):
            self.reset_btn.setText(loc.translate("btn_reset_auto"))
        if hasattr(self, 'save_btn'):
            self.save_btn.setText(loc.translate("btn_save_all_changes"))
        # Update emotion combo texts
        if hasattr(self, 'emotion_combo'):
            for i in range(self.emotion_combo.count()):
                code = self.emotion_combo.itemData(i)
                if code:
                    self.emotion_combo.setItemText(i, loc.translate(f"emotion_{code.lower()}"))

    def load_data(self):
        # We need to read from the transcript json (Stage 3.5 output)
        transcript_path = os.path.join(self.project_dir, "cache", "transcript.json")
        if not os.path.exists(transcript_path):
            transcript_path = os.path.join(self.project_dir, "transcription", "transcript.json")
            
        if os.path.exists(transcript_path):
            try:
                with open(transcript_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.transcript = Transcript(**data)
                    self.model.update_data(self.transcript)
            except Exception as e:
                QMessageBox.warning(self, loc.translate("msg_error"), loc.translate("msg_load_transcript_fail").format(err=str(e)))
        else:
            QMessageBox.information(self, loc.translate("msg_info"), loc.translate("msg_no_transcript"))

    def apply_override(self):
        idx = self.table.currentIndex()
        if not idx.isValid() or not self.transcript: return
        
        seg = self.transcript.segments[idx.row()]
        emotion = self.emotion_combo.currentData() or self.emotion_combo.currentText()
        intensity = self.intensity_slider.value() / 10.0
        
        seg.emotion = {
            "emotion_id": emotion,
            "intensity": intensity,
            "confidence": 100.0,
            "user_override": True,
            "provider_supported": False
        }
        
        # Force refresh row
        self.model.dataChanged.emit(
            self.model.index(idx.row(), 0),
            self.model.index(idx.row(), self.model.columnCount() - 1)
        )

    def reset_auto(self):
        idx = self.table.currentIndex()
        if not idx.isValid() or not self.transcript: return
        
        seg = self.transcript.segments[idx.row()]
        # Reset override flag, effectively letting the pipeline re-detect on next run
        # Or we can just set it to Neutral
        seg.emotion = {
            "emotion_id": "Neutral",
            "intensity": 1.0,
            "confidence": 100.0,
            "user_override": False,
            "provider_supported": False
        }
        
        self.model.dataChanged.emit(
            self.model.index(idx.row(), 0),
            self.model.index(idx.row(), self.model.columnCount() - 1)
        )

    def save_data(self):
        if not self.transcript: return
        
        transcript_path = os.path.join(self.project_dir, "cache", "transcript.json")
        try:
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(self.transcript.to_json())
            QMessageBox.information(self, loc.translate("msg_success"), loc.translate("msg_emotions_saved"))
        except Exception as e:
            QMessageBox.warning(self, loc.translate("msg_error"), loc.translate("msg_save_fail").format(err=str(e)))
