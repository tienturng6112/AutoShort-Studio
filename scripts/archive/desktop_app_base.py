import sys
import os
import subprocess
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,
    QTextEdit, QFileDialog, QMessageBox, QDialog, QFormLayout, QGroupBox,
    QRadioButton, QCheckBox, QFrame, QScrollArea, QSpacerItem, QSizePolicy,
    QSplitter, QTabWidget, QPlainTextEdit, QListWidget, QTreeWidget, QTreeWidgetItem,
    QSlider, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import QProcess, Qt, QThread, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from backend.services.localization_service import LocalizationService


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoShort Studio Desktop App (PySide6)")
        self.resize(650, 500)
        
        self.project_dir = ""
        self.process = None

        self.init_ui()
        self.update_ui_text()
        
        # Initialize Services
        from backend.services.queue_service import QueueService
        from backend.services.recovery_service import RecoveryService
        
        self.queue_service = QueueService()
        self.queue_service.signals.project_output.connect(self.read_queue_output)
        self.queue_service.signals.project_finished.connect(self.queue_pipeline_finished)
        self.queue_service.signals.queue_updated.connect(self.update_queue_ui)
        self.queue_service.start()
        
        self.recovery_service = RecoveryService()
        self.check_recovery()

    def update_ui_text(self):
        loc = LocalizationService()
        self.setWindowTitle(loc.translate("window_title"))
        self.title_label.setText(loc.translate("window_title"))
        self.subtitle_label.setText(loc.translate("window_subtitle"))
        self.settings_btn.setText(loc.translate("settings"))
        if hasattr(self, 'projects_btn'):
            self.projects_btn.setText(loc.translate("projects"))
        
        self.input_title.setText(loc.translate("input_video_source"))
        self.browse_btn.setText(loc.translate("browse"))
        
        self.src_label.setText(loc.translate("source_language"))
        self.target_label.setText(loc.translate("target_language"))
        
        self.output_mode_group.setTitle(loc.translate("output_mode"))
        self.mode_sub_voice.setText(loc.translate("mode_sub_voice"))
        self.mode_sub_only.setText(loc.translate("mode_sub_only"))
        self.mode_voice_only.setText(loc.translate("mode_voice_only"))
        self.mode_sub_audio.setText(loc.translate("mode_sub_audio"))
        
        self.start_btn.setText(loc.translate("start_translation"))
        
        if self.process is None:
            self.progress_label.setText(loc.translate("status_idle"))
            
        self.open_folder_btn.setText(loc.translate("open_output_folder"))
        self.input_edit.setPlaceholderText(loc.translate("placeholder_input"))
        self.update_output_mode_desc()

    def init_ui(self):
        # Main widget & layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Header Layout (Title + Settings button)
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        self.title_label = QLabel("AutoShort Studio")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4F46E5;")
        self.subtitle_label = QLabel("Alpha MVP - Video Translation & Subtitling")
        self.subtitle_label.setStyleSheet("font-size: 12px; color: #6B7280;")
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        loc = LocalizationService()
        
        self.projects_btn = QPushButton(loc.translate("projects"))
        self.projects_btn.setStyleSheet("padding: 5px 10px; font-weight: bold;")
        self.projects_btn.clicked.connect(self.open_project_manager)
        
        self.diagnostics_btn = QPushButton("Diagnostics")
        self.diagnostics_btn.setStyleSheet("padding: 5px 10px; font-weight: bold;")
        self.diagnostics_btn.clicked.connect(self.open_diagnostics)
        
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setStyleSheet("padding: 5px 10px; font-weight: bold;")
        self.settings_btn.clicked.connect(self.open_settings)
        
        self.emotion_btn = QPushButton("Emotion Editor")
        self.emotion_btn.setStyleSheet("padding: 5px 10px; font-weight: bold; background-color: #EC4899; color: white;")
        self.emotion_btn.clicked.connect(self.open_emotion_editor)
        
        self.qa_btn = QPushButton("QA Dashboard")
        self.qa_btn.setStyleSheet("padding: 5px 10px; font-weight: bold; background-color: #F59E0B; color: white;")
        self.qa_btn.clicked.connect(self.open_qa_dashboard)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.projects_btn)
        header_layout.addWidget(self.diagnostics_btn)
        header_layout.addWidget(self.emotion_btn)
        header_layout.addWidget(self.qa_btn)
        header_layout.addWidget(self.settings_btn)
        main_layout.addLayout(header_layout)

        # Video source input layout
        input_layout = QVBoxLayout()
        self.input_title = QLabel("Input Video Source (Local file or YouTube URL)")
        self.input_title.setStyleSheet("font-weight: bold;")
        
        file_input_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Paste YouTube URL or browse a local file...")
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_file)
        file_input_layout.addWidget(self.input_edit)
        file_input_layout.addWidget(self.browse_btn)
        
        input_layout.addWidget(self.input_title)
        input_layout.addLayout(file_input_layout)
        main_layout.addLayout(input_layout)

        # Template Selection
        template_layout = QHBoxLayout()
        self.template_label = QLabel("Project Template:")
        self.template_label.setStyleSheet("font-weight: bold;")
        self.template_combo = QComboBox()
        self.template_combo.addItem("None (Use Global Settings)", "")
        
        from backend.template.template_manager import TemplateManager
        self.template_mgr = TemplateManager()
        for tpl in self.template_mgr.list_templates():
            self.template_combo.addItem(f"{tpl.metadata.name}", tpl.metadata.template_id)
            
        self.browse_templates_btn = QPushButton("Browse Templates")
        self.browse_templates_btn.clicked.connect(self.open_template_browser)
        
        template_layout.addWidget(self.template_label)
        template_layout.addWidget(self.template_combo)
        template_layout.addWidget(self.browse_templates_btn)
        main_layout.addLayout(template_layout)

        # Languages selectors
        langs_layout = QHBoxLayout()
        
        self.languages = [
            ("English", "en"),
            ("Vietnamese", "vi"),
            ("Japanese", "ja"),
            ("Korean", "ko"),
            ("Chinese (Simplified)", "zh"),
            ("Spanish", "es"),
            ("French", "fr"),
            ("German", "de"),
            ("Thai", "th"),
            ("Indonesian", "id"),
            ("Portuguese", "pt"),
            ("Italian", "it"),
            ("Russian", "ru"),
            ("Arabic", "ar"),
            ("Hindi", "hi")
        ]
        
        src_layout = QVBoxLayout()
        self.src_label = QLabel("Source Language")
        self.src_combo = QComboBox()
        for name, code in self.languages:
            self.src_combo.addItem(name, code)
        src_layout.addWidget(self.src_label)
        src_layout.addWidget(self.src_combo)
        
        target_layout = QVBoxLayout()
        self.target_label = QLabel("Target Language")
        self.target_combo = QComboBox()
        for name, code in self.languages:
            self.target_combo.addItem(name, code)
        target_layout.addWidget(self.target_label)
        target_layout.addWidget(self.target_combo)
        
        # Set defaults: Source = English, Target = Vietnamese
        eng_idx = self.src_combo.findText("English")
        if eng_idx != -1:
            self.src_combo.setCurrentIndex(eng_idx)
        vi_idx = self.target_combo.findText("Vietnamese")
        if vi_idx != -1:
            self.target_combo.setCurrentIndex(vi_idx)

        # Connect signals to prevent same language selection
        self.src_combo.currentIndexChanged.connect(self.check_languages)
        self.target_combo.currentIndexChanged.connect(self.check_languages)
        
        langs_layout.addLayout(src_layout)
        langs_layout.addLayout(target_layout)
        main_layout.addLayout(langs_layout)

        # Output Mode selection group
        self.output_mode_group = QGroupBox("Output Mode")
        output_mode_layout = QVBoxLayout()
        
        modes_layout = QHBoxLayout()
        self.mode_sub_voice = QRadioButton("Subtitle + Voice")
        self.mode_sub_only = QRadioButton("Subtitle Only")
        self.mode_voice_only = QRadioButton("Voice Only")
        self.mode_sub_audio = QRadioButton("Subtitle + Audio Files")
        
        modes_layout.addWidget(self.mode_sub_voice)
        modes_layout.addWidget(self.mode_sub_only)
        modes_layout.addWidget(self.mode_voice_only)
        modes_layout.addWidget(self.mode_sub_audio)
        output_mode_layout.addLayout(modes_layout)
        
        self.mode_desc_label = QLabel("")
        self.mode_desc_label.setStyleSheet("color: #6B7280; font-style: italic;")
        output_mode_layout.addWidget(self.mode_desc_label)
        
        self.output_mode_group.setLayout(output_mode_layout)
        main_layout.addWidget(self.output_mode_group)

        # Load output mode settings on startup
        self.load_output_mode()

        # Connect signals for output mode changes
        self.mode_sub_voice.toggled.connect(self.save_output_mode)
        self.mode_sub_only.toggled.connect(self.save_output_mode)
        self.mode_voice_only.toggled.connect(self.save_output_mode)
        self.mode_sub_audio.toggled.connect(self.save_output_mode)
        
        self.mode_sub_voice.toggled.connect(self.update_output_mode_desc)
        self.mode_sub_only.toggled.connect(self.update_output_mode_desc)
        self.mode_voice_only.toggled.connect(self.update_output_mode_desc)
        self.mode_sub_audio.toggled.connect(self.update_output_mode_desc)

        # Action button
        self.start_btn = QPushButton("Start Translation")
        self.start_btn.setStyleSheet("background-color: #4F46E5; color: white; font-weight: bold; padding: 10px; font-size: 14px;")