import re
import os

def build_settings_window():
    with open('settings_code.txt', 'r', encoding='utf-8') as f:
        code = f.read()

    # Imports
    imports = """import os
import json
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,
    QMessageBox, QFormLayout, QGroupBox, QRadioButton, QCheckBox,
    QTabWidget, QScrollArea
)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from backend.services.localization_service import LocalizationService
"""

    # We need to strip existing imports and MainWindow from code.
    # The classes TestConnectionWorker, TestDeepLConnectionWorker, etc. should stay.
    
    # Remove old imports
    code = re.sub(r'import sys.*?from backend\.services\.localization_service import LocalizationService\n', '', code, flags=re.DOTALL)
    
    # Rename class
    code = code.replace("class SettingsDialog(QDialog):", "class SettingsWindow(QMainWindow):")
    code = code.replace("super().__init__(parent)", "super().__init__(parent)\n        self.setWindowFlag(Qt.Window)")
    code = code.replace("self.accept()", "self.close()")
    
    # Replace init_ui completely
    init_ui_pattern = re.compile(r'    def init_ui\(self\):.*?    def load_settings\(self\):', re.DOTALL)
    
    new_init_ui = """    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # --- TAB: GENERAL ---
        self.tab_general = QWidget()
        gen_layout = QVBoxLayout(self.tab_general)
        
        # Profile selection
        profile_layout = QHBoxLayout()
        self.profile_label = QLabel("Processing Profile:")
        self.profile_label.setStyleSheet("font-weight: bold;")
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(self.profile_service.get_profiles() + ["Custom"])
        self.profile_combo.setCurrentText("Custom")
        self.profile_combo.currentIndexChanged.connect(self.on_profile_changed)
        profile_layout.addWidget(self.profile_label)
        profile_layout.addWidget(self.profile_combo)
        gen_layout.addLayout(profile_layout)
        
        self.lang_group = QGroupBox("Interface")
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel("Interface Language:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Tiếng Việt", "English"])
        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)
        lang_layout.addWidget(self.lang_label)
        lang_layout.addWidget(self.lang_combo)
        self.lang_group.setLayout(lang_layout)
        gen_layout.addWidget(self.lang_group)
        gen_layout.addStretch()
        self.tabs.addTab(self.tab_general, "General")
        
        # --- TAB: TRANSLATION ---
        self.tab_trans = QWidget()
        trans_layout = QVBoxLayout(self.tab_trans)
        
        provider_layout = QHBoxLayout()
        self.provider_label = QLabel("Translation Provider:")
        self.provider_combo = QComboBox()
        translation_providers = [p.provider_id for p in self.cap_mgr.registry.list_providers() if p.provider_type == "translation"]
        if not translation_providers: translation_providers = ["ChatAnywhere", "DeepL"]
        self.provider_combo.addItems(translation_providers)
        provider_layout.addWidget(self.provider_label)
        provider_layout.addWidget(self.provider_combo)
        trans_layout.addLayout(provider_layout)
        
        quality_layout = QHBoxLayout()
        self.quality_label = QLabel("Translation Quality:")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Standard (Fast)", "Balanced (Recommended)", "Maximum (Best quality)"])
        quality_layout.addWidget(self.quality_label)
        quality_layout.addWidget(self.quality_combo)
        trans_layout.addLayout(quality_layout)
        
        trans_layout.addStretch()
        self.tabs.addTab(self.tab_trans, "Translation")
        
        # --- TAB: VOICE ---
        self.tab_voice = QWidget()
        voice_layout = QVBoxLayout(self.tab_voice)
        
        enhance_layout = QHBoxLayout()
        self.enhance_label = QLabel("Speech Enhancement:")
        self.enhance_combo = QComboBox()
        self.enhance_combo.addItems(["Off (Fast)", "Demucs (High Quality)"])
        enhance_layout.addWidget(self.enhance_label)
        enhance_layout.addWidget(self.enhance_combo)
        voice_layout.addLayout(enhance_layout)
        
        tts_provider_layout = QHBoxLayout()
        self.tts_provider_label = QLabel("TTS Provider:")
        self.tts_provider_combo = QComboBox()
        tts_providers = [p.provider_id for p in self.cap_mgr.registry.list_providers() if p.provider_type == "tts"]
        if not tts_providers: tts_providers = ["Edge TTS", "Kira"]
        self.tts_provider_combo.addItems(tts_providers)
        self.tts_provider_combo.currentIndexChanged.connect(self.update_tts_ui_state)
        tts_provider_layout.addWidget(self.tts_provider_label)
        tts_provider_layout.addWidget(self.tts_provider_combo)
        voice_layout.addLayout(tts_provider_layout)
        
        self.voices_group = QGroupBox("Voice Assignment Config")
        self.voices_layout = QVBoxLayout()
        mode_layout = QHBoxLayout()
        self.mode_single_voice = QRadioButton("Single Voice")
        self.mode_multi_voice = QRadioButton("Multiple Voices")
        self.mode_single_voice.setChecked(True)
        self.mode_single_voice.toggled.connect(self.toggle_voice_mode)
        mode_layout.addWidget(self.mode_single_voice)
        mode_layout.addWidget(self.mode_multi_voice)
        self.voices_layout.addLayout(mode_layout)
        
        self.single_voice_container = QWidget()
        self.single_voice_layout = QFormLayout(self.single_voice_container)
        self.global_voice_combo = QComboBox()
        self.single_voice_layout.addRow("Select Voice for all speakers:", self.global_voice_combo)
        self.single_voice_info_label = QLabel("<font color='gray'>This voice will be applied to all detected speakers.</font>")
        self.single_voice_layout.addRow(self.single_voice_info_label)
        
        self.multi_voice_container = QWidget()
        self.multi_voice_layout = QFormLayout(self.multi_voice_container)
        self.speaker_combos = {}
        self.preview_buttons = {}
        
        self.voices_layout.addWidget(self.single_voice_container)
        self.voices_layout.addWidget(self.multi_voice_container)
        self.voices_group.setLayout(self.voices_layout)
        voice_layout.addWidget(self.voices_group)
        self.toggle_voice_mode()
        
        voice_layout.addStretch()
        self.tabs.addTab(self.tab_voice, "Voice")
        
        # --- TAB: PROVIDERS ---
        self.tab_prov = QWidget()
        prov_layout = QVBoxLayout(self.tab_prov)
        
        self.ca_group = QGroupBox("ChatAnywhere Config")
        self.ca_layout = QFormLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.base_url_edit = QLineEdit()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.refresh_ca_model_btn = QPushButton("Refresh Models")
        self.refresh_ca_model_btn.clicked.connect(self.refresh_translation_models)
        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_combo, 1)
        model_layout.addWidget(self.refresh_ca_model_btn)
        self.ca_layout.addRow("API Key:", self.api_key_edit)
        self.ca_layout.addRow("Base URL:", self.base_url_edit)
        self.ca_layout.addRow("Model Name:", model_layout)
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_status_label = QLabel("")
        test_layout = QHBoxLayout()
        test_layout.addWidget(self.test_btn)
        test_layout.addWidget(self.test_status_label)
        self.ca_layout.addRow(test_layout)
        self.ca_group.setLayout(self.ca_layout)
        prov_layout.addWidget(self.ca_group)
        
        self.kira_group = QGroupBox("Kira Config")
        self.kira_layout = QFormLayout()
        self.kira_api_key_edit = QLineEdit()
        self.kira_api_key_edit.setEchoMode(QLineEdit.Password)
        self.kira_model_combo = QComboBox()
        self.kira_model_combo.setEditable(True)
        self.refresh_kira_model_btn = QPushButton("Refresh Models")
        self.refresh_kira_model_btn.clicked.connect(self.refresh_tts_models)
        kira_model_layout = QHBoxLayout()
        kira_model_layout.addWidget(self.kira_model_combo, 1)
        kira_model_layout.addWidget(self.refresh_kira_model_btn)
        self.kira_speed_edit = QLineEdit("1.0")
        self.kira_test_btn = QPushButton("Test Connection")
        self.kira_test_btn.clicked.connect(self.test_kira_connection)
        self.kira_status_label = QLabel("")
        self.kira_layout.addRow("API Key:", self.kira_api_key_edit)
        self.kira_layout.addRow("Model Name:", kira_model_layout)
        self.kira_layout.addRow("Speed (0.25-4.0):", self.kira_speed_edit)
        ktest_layout = QHBoxLayout()
        ktest_layout.addWidget(self.kira_test_btn)
        ktest_layout.addWidget(self.kira_status_label)
        self.kira_layout.addRow(ktest_layout)
        self.kira_group.setLayout(self.kira_layout)
        prov_layout.addWidget(self.kira_group)
        
        prov_layout.addStretch()
        self.tabs.addTab(self.tab_prov, "Providers")
        
        # --- TAB: ADVANCED ---
        self.tab_adv = QWidget()
        adv_layout = QVBoxLayout(self.tab_adv)
        self.context_translate_cb = QCheckBox("Enable Context Translation (SceneBuilder)")
        self.analyzer_cb = QCheckBox("Enable Conversation Analyzer")
        adv_layout.addWidget(self.context_translate_cb)
        adv_layout.addWidget(self.analyzer_cb)
        adv_layout.addStretch()
        self.tabs.addTab(self.tab_adv, "Advanced")
        
        # Bottom Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 8px;")
        self.save_btn.clicked.connect(self.save_settings)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(btn_layout)

    def load_settings(self):"""
    
    code = init_ui_pattern.sub(new_init_ui, code)
    
    final_code = imports + "\n" + code
    
    with open("frontend/ui/settings_window.py", "w", encoding="utf-8") as f:
        f.write(final_code)

build_settings_window()
