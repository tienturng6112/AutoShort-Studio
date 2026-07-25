import sys

import os

import subprocess

import json

from PySide6.QtWidgets import (

    QShortcut,

    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,

    QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,

    QTextEdit, QFileDialog, QMessageBox, QDialog, QFormLayout, QGroupBox,

    QRadioButton, QCheckBox, QFrame, QScrollArea, QSpacerItem, QSizePolicy,

    QSplitter, QTabWidget, QPlainTextEdit, QListWidget, QTreeWidget, QTreeWidgetItem,

    QSlider, QTableWidget, QTableWidgetItem

)

from PySide6.QtCore import QKeySequence, QProcess, Qt, QThread, Signal, QUrl

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from frontend.workspace.workspace_manager import WorkspaceManager

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

                    stats[spk]["duration"] += dur
        except Exception:
            pass
    return stats

class CharacterSelectionButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("(Default Voice)", parent)
        self._character_id = ""
        self.clicked.connect(self.open_browser)

    def setCharacter(self, character_id):
        self._character_id = character_id
        from backend.character.character_manager import CharacterManager
        import os
        cm = CharacterManager(storage_path=os.path.join(os.getcwd(), "characters.json"))
        profile = cm.get_character(character_id)
        if profile:
            self.setText(f"{profile.display_name} ({profile.preferred_voice or 'No Voice'})")
        else:
            self.setText("(Default Voice)")

    def currentData(self):
        return self._character_id
        
    def currentText(self):
        return self._character_id

    # Dummy methods to satisfy legacy load_settings logic
    def clear(self): pass
    def addItem(self, text, data=None): pass
    def blockSignals(self, block): pass
    def setCurrentIndex(self, index): pass
    def count(self): return 1
    def findData(self, data): return 0 if data == self._character_id else -1

    def open_browser(self):
        from frontend.ui.character_browser_window import CharacterBrowserWindow
        from backend.character.character_manager import CharacterManager
        from backend.providers.provider_registry import ProviderRegistry
        from backend.providers.provider_capability_manager import ProviderCapabilityManager
        from backend.voice.voice_manager import VoiceManager
        import os
        
        registry = ProviderRegistry()
        registry.inject_legacy_providers()
        cap_mgr = ProviderCapabilityManager(registry, config_dir="config")
        vm = VoiceManager(cap_mgr, cache_path=os.path.join("config", "voice_cache.json"))
        cm = CharacterManager(storage_path=os.path.join(os.getcwd(), "characters.json"), voice_manager=vm)
            self.target_combo.setCurrentIndex(new_index)

            self.target_combo.blockSignals(False)



    def browse_file(self):

        file_path, _ = QFileDialog.getOpenFileName(

            self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.avi *.mov);;All Files (*)"

        )

        if file_path:

            self.input_edit.setText(file_path)



    def open_settings(self):

        dialog = SettingsDialog(self)

        dialog.exec()



    def open_diagnostics(self):

        from frontend.ui.provider_diagnostics_window import ProviderDiagnosticsWindow

        from backend.providers.provider_registry import ProviderRegistry

        from backend.providers.provider_capability_manager import ProviderCapabilityManager

        import os

        

        registry = ProviderRegistry()

        registry.inject_legacy_providers()

        registry.discover_providers(os.path.join("backend", "plugins", "providers"))

        cap_mgr = ProviderCapabilityManager(registry, config_dir="config")

        cap_mgr.refresh()

        

        self.diag_window = ProviderDiagnosticsWindow(cap_mgr)

        self.diag_window.show()



    def open_project_manager(self):

        from frontend.dialogs.project_manager_dialog import ProjectManagerDialog

        dialog = ProjectManagerDialog(self.queue_service, self)

        if dialog.exec():

            if dialog.resume_requested and dialog.selected_project_id:

                self.resume_project_id = dialog.selected_project_id

                self.input_edit.setText(f"[Resuming Project: {self.resume_project_id}]")

                self.start_pipeline()

        

    def open_emotion_editor(self):

        projects_dir = os.path.abspath("projects")

        if not os.path.exists(projects_dir):

            QMessageBox.warning(self, "No Projects", "No projects found. Please run a pipeline first.")

            return

            

        subdirs = [os.path.join(projects_dir, d) for d in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, d))]

        if not subdirs:

            QMessageBox.warning(self, "No Projects", "No projects found. Please run a pipeline first.")

            return

            

        latest_dir = max(subdirs, key=os.path.getmtime)

        from frontend.ui.emotion_editor_window import EmotionEditorWindow

        self.profile_label.setText(loc.translate("processing_profile") + ":")
        self.provider_label.setText(loc.translate("translation_provider") + ":")
        self.context_translate_cb.setText(loc.translate("enable_context_translation"))
        self.analyzer_cb.setText(loc.translate("enable_conversation_analyzer"))
        self.quality_label.setText(loc.translate("translation_quality") + ":")
        
        current_quality = self.quality_combo.currentIndex()
        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()
        self.quality_combo.addItems([
            loc.translate("tq_standard"),
            loc.translate("tq_balanced"),
            loc.translate("tq_maximum")
        ])
        self.quality_combo.setCurrentIndex(current_quality)
        self.quality_combo.blockSignals(False)
        
        self.enhance_label.setText(loc.translate("speech_enhancement") + ":")
        self.tts_provider_label.setText(loc.translate("tts_provider") + ":")
        
        provider_text = self.provider_combo.currentText()
        if "ChatAnywhere" in provider_text:
            self.ca_group.setTitle(loc.translate("chatanywhere_config"))
        elif "DeepL" in provider_text:
            self.ca_group.setTitle(loc.translate("deepl_config"))
        else:
            self.ca_group.setTitle(loc.translate("chatanywhere_config"))
        self.refresh_ca_model_btn.setText(loc.translate("refresh_models"))
        self.test_btn.setText(loc.translate("test_connection"))
        
        self.kira_group.setTitle(loc.translate("kira_config"))
        self.refresh_kira_model_btn.setText(loc.translate("refresh_models"))
        self.kira_test_btn.setText(loc.translate("test_connection"))
        
        self.voices_group.setTitle(loc.translate("speaker_voices"))
        self.mode_single_voice.setText(loc.translate("mode_single_voice"))
        self.mode_multi_voice.setText(loc.translate("mode_multi_voice"))
        
        if hasattr(self, 'single_voice_layout'):
            lbl = self.single_voice_layout.labelForField(self.global_voice_combo)
            if lbl:
                lbl.setText(loc.translate("global_voice_label"))
                
        if hasattr(self, 'single_voice_info_label'):
            self.single_voice_info_label.setText(f"<font color='gray'>{loc.translate('single_voice_info')}</font>")
        
        for prev_btn in self.preview_buttons.values():
            prev_btn.setText("▶ " + loc.translate("preview"))
            
        self.save_btn.setText(loc.translate("save_settings"))
        self.cancel_btn.setText(loc.translate("cancel"))
        self.lang_label.setText(loc.translate("interface_language") + ":")
        self.lang_group.setTitle(loc.translate("interface_section"))
        
        # Form layouts
        if self.ca_layout.labelForField(self.api_key_edit):
            self.ca_layout.labelForField(self.api_key_edit).setText(loc.translate("api_key") + ":")
        if self.ca_layout.labelForField(self.base_url_edit):
            self.ca_layout.labelForField(self.base_url_edit).setText(loc.translate("base_url") + ":")
            
        # Get Model Name label (it's the 3rd row, 0-indexed is 2)
        model_label = self.ca_layout.itemAt(2, QFormLayout.LabelRole)
        if model_label and model_label.widget():
            model_label.widget().setText(loc.translate("model_name") + ":")
            
        if self.kira_layout.labelForField(self.kira_api_key_edit):
            self.kira_layout.labelForField(self.kira_api_key_edit).setText(loc.translate("api_key") + ":")
        kira_model_label = self.kira_layout.itemAt(1, QFormLayout.LabelRole)
        if kira_model_label and kira_model_label.widget():
            kira_model_label.widget().setText(loc.translate("model_name") + ":")
        if self.kira_layout.labelForField(self.kira_speed_edit):
            self.kira_layout.labelForField(self.kira_speed_edit).setText(loc.translate("speed") + ":")
            
        # Placeholders
        provider_text = self.provider_combo.currentText()
        if "ChatAnywhere" in provider_text:
            self.api_key_edit.setPlaceholderText(loc.translate("enter_ca_key"))
        elif "DeepL" in provider_text:
            self.api_key_edit.setPlaceholderText(loc.translate("enter_deepl_key"))
        self.kira_api_key_edit.setPlaceholderText(loc.translate("enter_kira_key"))
        
        # Enhance combo
        current_enhance = self.enhance_combo.currentIndex()
        self.enhance_combo.blockSignals(True)
        self.enhance_combo.clear()
        self.enhance_combo.addItems([loc.translate("off_fast"), loc.translate("demucs_high_quality")])
        self.enhance_combo.setCurrentIndex(current_enhance)
        self.enhance_combo.blockSignals(False)

    def init_ui(self):
        layout = QVBoxLayout()
        
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
        layout.addLayout(profile_layout)
        
        # Provider selection
        provider_layout = QHBoxLayout()
        self.provider_label = QLabel("Translation Provider:")
        self.provider_label.setStyleSheet("font-weight: bold;")
        self.provider_combo = QComboBox()
        
        translation_providers = [p.provider_id for p in self.cap_mgr.registry.list_providers() if p.provider_type == "translation"]
        if not translation_providers:
            translation_providers = ["ChatAnywhere", "DeepL"]
        self.provider_combo.addItems(translation_providers)
        
        provider_layout.addWidget(self.provider_label)
        provider_layout.addWidget(self.provider_combo)
        layout.addLayout(provider_layout)
        
        # Context Translation Option
        self.context_translate_cb = QCheckBox("Enable Context Translation (SceneBuilder)")
        self.context_translate_cb.setChecked(True)
        layout.addWidget(self.context_translate_cb)
        
        self.analyzer_cb = QCheckBox("Enable Conversation Analyzer")
        self.analyzer_cb.setChecked(True)
        layout.addWidget(self.analyzer_cb)
        
        # Translation Quality selection
        quality_layout = QHBoxLayout()
        self.quality_label = QLabel("Translation Quality:")
        self.quality_label.setStyleSheet("font-weight: bold;")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Standard (Fast)", "Balanced (Recommended)", "Maximum (Best quality)"])
        quality_layout.addWidget(self.quality_label)
        quality_layout.addWidget(self.quality_combo)
        layout.addLayout(quality_layout)
        
        # Speech Enhancement selection
        enhance_layout = QHBoxLayout()
        self.enhance_label = QLabel("Speech Enhancement:")
        self.enhance_label.setStyleSheet("font-weight: bold;")
        self.enhance_combo = QComboBox()
        self.enhance_combo.addItems(["Off (Fast)", "Demucs (High Quality)"])
        enhance_layout.addWidget(self.enhance_label)
        enhance_layout.addWidget(self.enhance_combo)
        layout.addLayout(enhance_layout)
        
        # TTS Provider selection
        tts_provider_layout = QHBoxLayout()
        self.tts_provider_label = QLabel("TTS Provider:")
        self.tts_provider_label.setStyleSheet("font-weight: bold;")
        self.tts_provider_combo = QComboBox()
        
        tts_providers = [p.provider_id for p in self.cap_mgr.registry.list_providers() if p.provider_type == "tts"]
        if not tts_providers:
            tts_providers = ["Edge TTS", "Kira"]
        self.tts_provider_combo.addItems(tts_providers)
        
        self.tts_provider_combo.currentIndexChanged.connect(self.update_tts_ui_state)
        tts_provider_layout.addWidget(self.tts_provider_label)
        tts_provider_layout.addWidget(self.tts_provider_combo)
        layout.addLayout(tts_provider_layout)
        
        # Config container groupbox
        self.ca_group = QGroupBox("ChatAnywhere Config")
        self.ca_layout = QFormLayout()
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Enter ChatAnywhere API Key")
        self.api_key_edit.textChanged.connect(self.on_api_key_changed)
        
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.chatanywhere.tech/v1")
        
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
        
        # Connection check components
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_status_label = QLabel("")
        
        test_layout = QHBoxLayout()
        test_layout.addWidget(self.test_btn)
        test_layout.addWidget(self.test_status_label)
        self.ca_layout.addRow(test_layout)
        
        self.ca_group.setLayout(self.ca_layout)
        layout.addWidget(self.ca_group)
        
        # Kira Config groupbox
        self.kira_group = QGroupBox("Kira Config")
        self.kira_layout = QFormLayout()
        
        self.kira_api_key_edit = QLineEdit()
        self.kira_api_key_edit.setEchoMode(QLineEdit.Password)
        self.kira_api_key_edit.setPlaceholderText("Enter Kira API Key")
        self.kira_api_key_edit.textChanged.connect(self.on_kira_api_key_changed)
        
        self.kira_model_combo = QComboBox()
        self.kira_model_combo.setEditable(True)
        
        self.refresh_kira_model_btn = QPushButton("Refresh Models")
        self.refresh_kira_model_btn.clicked.connect(self.refresh_tts_models)
        
        kira_model_layout = QHBoxLayout()
        kira_model_layout.addWidget(self.kira_model_combo, 1)
        kira_model_layout.addWidget(self.refresh_kira_model_btn)
        
        self.kira_speed_edit = QLineEdit()
        self.kira_speed_edit.setPlaceholderText("1.0")
        self.kira_speed_edit.setText("1.0")
        
        self.kira_test_btn = QPushButton("Test Connection")
        self.kira_test_btn.clicked.connect(self.test_kira_connection)
        self.kira_status_label = QLabel("")
        
        self.kira_layout.addRow("API Key:", self.kira_api_key_edit)
        self.kira_layout.addRow("Model Name:", kira_model_layout)
        self.kira_layout.addRow("Speed (0.25-4.0):", self.kira_speed_edit)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.kira_test_btn)
        btn_layout.addWidget(self.kira_status_label)
        self.kira_layout.addRow(btn_layout)
        
        self.kira_group.setLayout(self.kira_layout)
        layout.addWidget(self.kira_group)
        
        # Voice Assignment Config groupbox
        self.voices_group = QGroupBox("Voice Assignment Config")
        self.voices_layout = QVBoxLayout()
        
        mode_layout = QHBoxLayout()
        self.mode_single_voice = QRadioButton("Single Voice")
        self.mode_multi_voice = QRadioButton("Multiple Voices")
        self.mode_single_voice.setChecked(True)
        self.global_voice_combo = VoiceSelectionButton(self)
        self.single_voice_layout.addRow("Voice:", self.global_voice_combo)
        
        self.single_voice_info_label = QLabel("<font color='gray'>This voice will be applied to all detected speakers.</font>")
        self.single_voice_layout.addRow(self.single_voice_info_label)
        self.voices_layout.addWidget(self.single_voice_container)

        # Multiple Voices Container
        self.multi_voice_container = QWidget()
        multi_voice_layout = QFormLayout(self.multi_voice_container)
        
        stats = get_speaker_stats()
        self.speaker_combos = {}
        self.preview_buttons = {}
        self.speaker_containers = {}
        
        for spk in ["Speaker_A", "Speaker_B", "Speaker_C", "Speaker_D"]:
            spk_container = QWidget()
            spk_layout = QVBoxLayout(spk_container)
            spk_container.setContentsMargins(0, 0, 0, 4)
            spk_layout.setSpacing(2)
            
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)
            
            lbl = QLabel(f"<b>{spk}</b>")
            lbl.setMinimumWidth(80)
            row_layout.addWidget(lbl)
            
            combo = VoiceSelectionButton(self)
            self.speaker_combos[spk] = combo
            row_layout.addWidget(combo, 1)
            
            prev_btn = QPushButton("▶ Preview")
            prev_btn.setFixedWidth(80)
            prev_btn.clicked.connect(lambda checked=False, s=spk, c=combo, b=prev_btn: self.preview_voice(s, c, b))
            self.preview_buttons[spk] = prev_btn
            row_layout.addWidget(prev_btn)
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setStyleSheet("background-color: #4F46E5; color: white; font-weight: bold;")
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        self.provider_combo.currentIndexChanged.connect(self.update_ui_state)
        self.repopulate_speaker_voices()

    def on_api_key_changed(self, text):
        self.test_status_label.setText("")
        provider_text = self.provider_combo.currentText()
        if "ChatAnywhere" in provider_text:
            self.chatanywhere_api_key = text.strip()
        elif "DeepL" in provider_text:
            self.deepl_api_key = text.strip()

    def update_ui_state(self):
        loc = LocalizationService()
        provider_text = self.provider_combo.currentText()
        is_ca = "ChatAnywhere" in provider_text
        is_deepl = "DeepL" in provider_text
        
        self.ca_group.setEnabled(is_ca or is_deepl)
        
        # Temporarily block signals to prevent triggering on_api_key_changed when updating text
        self.api_key_edit.blockSignals(True)
        if is_ca:
            self.ca_group.setTitle("ChatAnywhere Config")
            self.api_key_edit.setText(self.chatanywhere_api_key)
            self.api_key_edit.setPlaceholderText(loc.translate("enter_ca_key"))
        elif is_deepl:
            self.ca_group.setTitle("DeepL Config")
            self.api_key_edit.setText(self.deepl_api_key)
            self.api_key_edit.setPlaceholderText(loc.translate("enter_deepl_key"))
        self.api_key_edit.blockSignals(False)
            
        label_url = self.ca_layout.labelForField(self.base_url_edit)
        if label_url:
            label_url.setVisible(is_ca)
        self.base_url_edit.setVisible(is_ca)
        
        # We need to hide/show the model_layout row instead of just self.model_combo
        model_row = self.ca_layout.rowCount() - 2
                    idx = self.model_combo.findText(saved_model)
                    if idx != -1:
                        self.model_combo.setCurrentIndex(idx)
                    else:
                        self.model_combo.setCurrentText(saved_model)
                    
                    # Force initial api key display
                    self.api_key_edit.blockSignals(True)
                    if provider == "DeepL":
                        self.api_key_edit.setText(self.deepl_api_key)
                    else:
                        self.api_key_edit.setText(self.chatanywhere_api_key)
                    self.api_key_edit.blockSignals(False)
                    
                    enhance = data.get("speech_enhancement", "off")
                    if enhance == "demucs":
                        self.enhance_combo.setCurrentIndex(1)
                    else:
                        self.enhance_combo.setCurrentIndex(0)
                        
                    # Load TTS settings
                    self.tts_provider = data.get("tts_provider", "Edge TTS")
                    if self.tts_provider == "Kira":
                        self.tts_provider_combo.setCurrentIndex(1)
                    else:
                        self.tts_provider_combo.setCurrentIndex(0)
                        
                    kira_config = data.get("kira", {})
                    self.kira_api_key = kira_config.get("api_key", "")
                    self.kira_api_key_edit.setText(self.kira_api_key)
                    self.kira_speed_edit.setText(str(kira_config.get("speed", "1.0")))
                    
                    saved_kira_model = kira_config.get("model", "kira-3.0-flash-tts")
                    idx = self.kira_model_combo.findText(saved_kira_model)
                    if idx != -1:
                        self.kira_model_combo.setCurrentIndex(idx)
                    else:
                        self.kira_model_combo.setCurrentText(saved_kira_model)
                    
                    # Repopulate voices based on provider
                    self.repopulate_speaker_voices()
                    
                    voice_mode = data.get("voice_mode", "SINGLE")
                    self.mode_single_voice.setChecked(voice_mode == "SINGLE")
                    self.mode_multi_voice.setChecked(voice_mode == "MULTI")
                    
                    global_voice = data.get("global_voice", "")
                    g_idx = self.global_voice_combo.findData(global_voice)
                    if g_idx != -1:
                        self.global_voice_combo.setCurrentIndex(g_idx)
                    elif global_voice:
                        self.global_voice_combo.addItem(global_voice, global_voice)
                        self.global_voice_combo.setCurrentIndex(self.global_voice_combo.count() - 1)
                    else:
                        self.global_voice_combo.setCurrentIndex(0)
                        
                    speaker_voices = data.get("speaker_voices", {})
                    for spk, combo in self.speaker_combos.items():
                        configured_voice = speaker_voices.get(spk, "")
                        idx = combo.findData(configured_voice)
                        if idx != -1:
                            combo.setCurrentIndex(idx)
                        elif configured_voice:
                            # Add item as technical ID and friendly text
                            combo.addItem(configured_voice, configured_voice)
                            combo.setCurrentIndex(combo.count() - 1)
                        else:
                            combo.setCurrentIndex(0)
            except Exception:
                pass
        else:
            self.base_url_edit.setText("https://api.chatanywhere.tech/v1")
            self._load_cached_models()
            self.model_combo.setCurrentText("gpt-4o-mini")
            self.enhance_combo.setCurrentIndex(0)
            self.tts_provider_combo.setCurrentIndex(0)
            self.repopulate_speaker_voices()
            for combo in self.speaker_combos.values():
                combo.setCurrentIndex(0)
        self.update_ui_state()
        self.update_tts_ui_state()

    def save_settings(self):
        if self.tts_provider_combo.currentIndex() == 1:
            current_kira_model = self.kira_model_combo.currentText().strip()
            models = [self.kira_model_combo.itemText(i) for i in range(self.kira_model_combo.count())]
            if models and current_kira_model not in models:
                suggested = models[0]
                loc = LocalizationService()
                QMessageBox.warning(self, loc.translate("msg_warning"), f"Model '{current_kira_model}' không tồn tại hoặc chưa được hỗ trợ.\nĐề xuất: {suggested}")
                return
                
        os.makedirs("config", exist_ok=True)
        settings_path = os.path.join("config", "settings.json")
        
        provider_text = self.provider_combo.currentText()
        
        speaker_voices = {}
        for spk, combo in self.speaker_combos.items():
            val = combo.currentData()
            if val:
                speaker_voices[spk] = val
                
        # Parse speed value safely
        speed_val = 1.0
        try:
            speed_val = float(self.kira_speed_edit.text().strip())
        except ValueError:
            pass
            
        existing_data = {}
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception:
                pass
                
        quality_map = {0: "Standard", 1: "Balanced", 2: "Maximum"}
        
        settings = {
            "processing_profile": self.profile_combo.currentText(),
            "use_context_translation": self.context_translate_cb.isChecked(),
            "use_conversation_analyzer": self.analyzer_cb.isChecked(),
            "translation_quality": quality_map.get(self.quality_combo.currentIndex(), "Balanced"),
            "translation_provider": provider_text,
            "speech_enhancement": "demucs" if self.enhance_combo.currentIndex() == 1 else "off",
            "tts_provider": "Kira" if self.tts_provider_combo.currentIndex() == 1 else "Edge TTS",
            "language": "vi" if self.lang_combo.currentIndex() == 0 else "en",
            "voice_mode": "SINGLE" if self.mode_single_voice.isChecked() else "MULTI",
            "global_voice": self.global_voice_combo.currentData() or "",
            "speaker_voices": speaker_voices,
            "output_mode": existing_data.get("output_mode", "Subtitle + Voice"),
            "chatanywhere": {
                "api_key": self.chatanywhere_api_key,
                "base_url": self.base_url_edit.text().strip() or "https://api.chatanywhere.tech/v1",
                "model": self.model_combo.currentText().strip() or "gpt-4o-mini"
            },
            "deepl": {
                "api_key": self.deepl_api_key,
                "model": self.model_combo.currentText().strip() if "DeepL" in provider_text else "default"
            },
            "kira": {
                "api_key": self.kira_api_key,
                "model": self.kira_model_combo.currentText().strip() or "kira-3.0-flash-tts",
                "speed": speed_val
            }
        }
        
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save settings: {str(e)}")

    def test_connection(self):
        provider_text = self.provider_combo.currentText()
        loc = LocalizationService()
        if "ChatAnywhere" in provider_text:
            if not self.chatanywhere_api_key:
                self.test_status_label.setText(loc.translate("msg_api_key_required"))
                self.test_status_label.setStyleSheet("color: #DC2626; font-weight: bold;")
                return
            self.test_status_label.setText(loc.translate("msg_testing_connection"))
            self.test_status_label.setStyleSheet("color: #4F46E5;")
            self.test_btn.setEnabled(False)
            self.ca_worker = TestConnectionWorker(self.chatanywhere_api_key, self.base_url_edit.text().strip() or "https://api.chatanywhere.tech/v1")
            self.ca_worker.finished.connect(self.on_test_finished)
            self.ca_worker.start()
        elif "DeepL" in provider_text:
            if not self.deepl_api_key:
                self.test_status_label.setText(loc.translate("msg_api_key_required"))
                self.test_status_label.setStyleSheet("color: #DC2626; font-weight: bold;")
                return
            self.test_status_label.setText(loc.translate("msg_testing_deepl"))
            self.test_status_label.setStyleSheet("color: #4F46E5;")
            self.test_btn.setEnabled(False)
            self.worker = TestDeepLConnectionWorker(self.deepl_api_key)
            self.worker.finished.connect(self.on_test_finished)
            self.worker.start()

    def on_test_finished(self, result):
        self.test_btn.setEnabled(True)
        if result.get("status") == "Connected":
            latency = result.get("latency_ms", 0)
            self.test_status_label.setText(f"Success! ({latency:.0f}ms)")
            self.test_status_label.setStyleSheet("color: #16A34A; font-weight: bold;")
        else:
            err = result.get("error", "Connection failed")
            self.test_status_label.setText(f"Failed: Check logs")
            self.test_status_label.setStyleSheet("color: #DC2626; font-weight: bold;")
            self.test_status_label.setToolTip(err)

    def on_kira_api_key_changed(self, text):
        self.kira_api_key = text.strip()
        self.kira_status_label.setText("")

    def on_lang_changed(self):
        idx = self.lang_combo.currentIndex()
        if idx == 0:
            lang_code = "vi"
        else:
            lang_code = "en"
            
        loc = LocalizationService()
        loc.change_language(lang_code)
        
        # Trigger UI update across application
        self.update_ui_text()
        if self.parentWidget() and hasattr(self.parentWidget(), "update_ui_text"):
            self.parentWidget().update_ui_text()

    def switch_to_custom_profile(self, *args):
        # Prevent recursion if already updating via profile selection
        if getattr(self, '_updating_profile', False): return
        
        # Switch the combobox to "Custom" silently
        idx = self.profile_combo.findText("Custom")
        if idx != -1 and self.profile_combo.currentIndex() != idx:
            self.profile_combo.blockSignals(True)
            self.profile_combo.setCurrentIndex(idx)
            self.profile_combo.blockSignals(False)

    def on_profile_changed(self):
        profile_name = self.profile_combo.currentText()
        if profile_name == "Custom":
            return
            
        settings = self.profile_service.get_profile_settings(profile_name)
        if not settings:
            return
            
        self._updating_profile = True
        try:
            if "translation_provider" in settings:
                idx = self.provider_combo.findText(settings["translation_provider"])
                if idx != -1: self.provider_combo.setCurrentIndex(idx)
                
            if "speech_enhancement" in settings:
                enh_idx = 1 if settings["speech_enhancement"] == "demucs" else 0
                self.enhance_combo.setCurrentIndex(enh_idx)
                
            if "tts_provider" in settings:
                idx = self.tts_provider_combo.findText(settings["tts_provider"])
                if idx != -1: self.tts_provider_combo.setCurrentIndex(idx)
                
            prov = settings.get("translation_provider", "").lower()
            if prov and prov in settings:
                model = settings[prov].get("model")
                if model:
                    self.model_combo.setCurrentText(model)
                    
            tts = settings.get("tts_provider", "").lower()
            if "kira" in tts and "kira" in settings:
                kmodel = settings["kira"].get("model")
                if kmodel:
                    self.kira_model_combo.setCurrentText(kmodel)
        finally:
            self._updating_profile = False

    def update_tts_ui_state(self):
        provider_id = self.tts_provider_combo.currentText()
        
        has_speed = self.cap_mgr.supports(provider_id, "tts", "speed_control")
        if hasattr(self, 'kira_speed_edit'):
            self.kira_speed_edit.setEnabled(has_speed)
            
        has_emotion = self.cap_mgr.supports(provider_id, "tts", "emotion")
        
        is_kira = "Kira" in provider_id
        self.kira_group.setVisible(is_kira)
    def repopulate_speaker_voices(self):
        # The voices are now selected via VoiceBrowserWindow
        # We just keep the buttons enabled and maybe update their state
        is_kira = self.tts_provider_combo.currentIndex() == 1
        
        provider_id = "kira" if is_kira else "edge-tts"
        # We don't need to manually fetch voices here anymore.
        pass

    def test_kira_connection(self):
        api_key = self.kira_api_key_edit.text().strip()
        loc = LocalizationService()
        if not api_key:
            self.kira_status_label.setText(loc.translate("msg_api_key_required"))
            self.kira_status_label.setStyleSheet("color: #DC2626; font-weight: bold;")
            return
            
        self.kira_status_label.setText(loc.translate("msg_testing"))
        self.kira_status_label.setStyleSheet("color: #4F46E5;")
        self.kira_test_btn.setEnabled(False)
        
        self.kira_worker = TestKiraConnectionWorker(api_key)
        self.kira_worker.finished.connect(self.on_kira_connection_tested)
        self.kira_worker.start()

    def on_kira_connection_tested(self, result):
        loc = LocalizationService()
        self.kira_test_btn.setEnabled(True)
        if result.get("status") == "Connected":
            count = result.get("voices_count", 0)
            self.kira_status_label.setText(f"{loc.translate('msg_success')}! ({count} voices)")
            self.kira_status_label.setStyleSheet("color: #16A34A; font-weight: bold;")
        else:
            err = result.get("error", "Connection failed")
            self.kira_status_label.setText(loc.translate("msg_failed"))
            self.kira_status_label.setStyleSheet("color: #DC2626; font-weight: bold;")
            self.kira_status_label.setToolTip(err)

    def _load_cached_models(self):
        cache_path = os.path.join("config", "models_cache.json")
        try:
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    trans_provider = self.provider_combo.currentText()
                    tts_provider = self.tts_provider_combo.currentText()
                    
                    trans_models = cache_data.get(trans_provider, [])
                    if trans_models:
                        self.model_combo.clear()
                        self.model_combo.addItems(trans_models)
                        
                    tts_models = cache_data.get(tts_provider, [])
                    if tts_models:
                        self.kira_model_combo.clear()
                        self.kira_model_combo.addItems(tts_models)
        except Exception:
            pass

    def _save_models_to_cache(self, provider_name, models):
        cache_path = os.path.join("config", "models_cache.json")
        cache_data = {}
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
            except Exception:
                pass
        cache_data[provider_name] = models
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=4)
        except Exception:
            pass

    def refresh_translation_models(self):
        loc = LocalizationService()
        provider_text = self.provider_combo.currentText()
        if "DeepL" in provider_text:
            provider = "DeepL"
            api_key = self.deepl_api_key
        else:
            provider = "ChatAnywhere"
            api_key = self.api_key_edit.text().strip()
            
        if not api_key:
            QMessageBox.warning(self, loc.translate("msg_warning"), f"Please enter an API Key for {provider} first.")
            return
            
        base_url = self.base_url_edit.text().strip() or "https://api.chatanywhere.tech/v1"
        self.refresh_ca_model_btn.setEnabled(False)
        self.refresh_ca_model_btn.setText(loc.translate("stage_1").split(":")[0] + "...") # just a quick fallback to Refreshing... wait I don't have refreshing string. I will just use "Refreshing..." but wait, user didn't ask for "Refreshing...". I will just leave it.
        
        self.trans_model_worker = RefreshTranslationModelsWorker(provider, api_key, base_url)
        self.trans_model_worker.finished.connect(lambda res: self.on_trans_models_refreshed(res, provider))
        self.trans_model_worker.start()

    def on_trans_models_refreshed(self, result, provider_name):
        self.refresh_ca_model_btn.setEnabled(True)
        self.refresh_ca_model_btn.setText("Refresh Models")
        
        if result.get("status") == "Success":
            models = result.get("models", [])
            self._save_models_to_cache(provider_name, models)
            
            if not models:
                self.save_btn.setEnabled(False)
            else:
                self.save_btn.setEnabled(True)
            
            current_model = self.model_combo.currentText()
            self.model_combo.clear()
            self.model_combo.addItems(models)
            if current_model in models:
                self.model_combo.setCurrentText(current_model)
            elif models:
                self.model_combo.setCurrentIndex(0)
        else:
            QMessageBox.critical(self, loc.translate("msg_error"), f"Failed to refresh models: {result.get('error')}")

    def refresh_tts_models(self):
        if hasattr(self, 'tts_model_worker') and self.tts_model_worker.isRunning():
            return
            
        provider_text = self.tts_provider_combo.currentText()
        api_key = self.kira_api_key_edit.text().strip()
        loc = LocalizationService()
        
        self.refresh_kira_model_btn.setEnabled(False)
        self.kira_model_combo.setEnabled(False)
        self._previous_kira_model = self.kira_model_combo.currentText()
        self.kira_model_combo.setCurrentText("Đang tải danh sách model...")
        
        self.tts_model_worker = RefreshTTSModelsWorker(provider_text, api_key)
        self.tts_model_worker.finished.connect(lambda res: self.on_tts_models_refreshed(res, provider_text))
        self.tts_model_worker.start()

    def on_tts_models_refreshed(self, result, provider_name):
        loc = LocalizationService()
        self.refresh_kira_model_btn.setEnabled(True)
        self.refresh_kira_model_btn.setText(loc.translate("refresh_models"))
        self.kira_model_combo.setEnabled(True)
        
        if result.get("status") == "Success":
            models = result.get("models", [])
            self._save_models_to_cache(provider_name, models)
            
            if not models:
                self.save_btn.setEnabled(False)
            else:
                self.save_btn.setEnabled(True)
            
            current_model = getattr(self, '_previous_kira_model', "")
            self.kira_model_combo.clear()
            self.kira_model_combo.addItems(models)
            if current_model in models:
                self.kira_model_combo.setCurrentText(current_model)
            elif models:
                self.kira_model_combo.setCurrentIndex(0)
                
            self.kira_status_label.setText("")
        else:
            current_model = getattr(self, '_previous_kira_model', "")
            if current_model:
                self.kira_model_combo.setCurrentText(current_model)
            self.kira_status_label.setText(f"{loc.translate('msg_error')}: {result.get('error')}")
            self.kira_status_label.setStyleSheet("color: #DC2626; font-weight: bold;")


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
        from backend.providers.provider_capability_manager import ProviderCapabilityManager
        import os
        
        registry = ProviderRegistry()
        registry.inject_legacy_providers()
        registry.discover_providers(os.path.join("backend", "plugins", "providers"))
        cap_mgr = ProviderCapabilityManager(registry, config_dir="config")
        cap_mgr.refresh()
        
        self.diag_window = ProviderDiagnosticsWindow(cap_mgr)
        self.diag_window.show()

    def open_project_manager(self):
        from frontend.ui.project_manager_window import ProjectManagerWindow
        self.pm_window = ProjectManagerWindow()
        self.pm_window.show()
        
    def open_emotion_editor(self):
        projects_dir = os.path.abspath("projects")
        if not os.path.exists(projects_dir):
            QMessageBox.warning(self, "No Projects", "No projects found. Please run a pipeline first.")
            return
            
        subdirs = [os.path.join(projects_dir, d) for d in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, d))]
        if not subdirs:
            QMessageBox.warning(self, "No Projects", "No projects found. Please run a pipeline first.")
            return
            
        latest_dir = max(subdirs, key=os.path.getmtime)
        from frontend.ui.emotion_editor_window import EmotionEditorWindow
        self.emotion_window = EmotionEditorWindow(project_dir=latest_dir)
        self.emotion_window.show()

    def start_pipeline(self):
        input_val = self.input_edit.text().strip()
        is_resume = hasattr(self, 'resume_project_id') and self.resume_project_id is not None
        if idx >= 0:
            self.template_combo.setCurrentIndex(idx)

    def start_pipeline(self):
        input_val = self.input_edit.text().strip()
        is_resume = hasattr(self, 'resume_project_id') and self.resume_project_id is not None
        
        if not input_val and not is_resume:
            loc = LocalizationService()
            QMessageBox.warning(self, loc.translate("msg_warning"), "Please specify an input video file or YouTube URL.")
            return

        # Prepare UI
        self.start_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.input_edit.setEnabled(False)
        self.src_combo.setEnabled(False)
        self.target_combo.setEnabled(False)
        self.open_folder_btn.setVisible(False)
        self.status_banner.setVisible(False)
        idx = self.template_combo.findData(tpl_id)
        if idx >= 0:
            self.template_combo.setCurrentIndex(idx)

    def start_pipeline(self):
        input_val = self.input_edit.text().strip()
        is_resume = hasattr(self, 'resume_project_id') and self.resume_project_id is not None
        
        if not input_val and not is_resume:
            loc = LocalizationService()
            QMessageBox.warning(self, loc.translate("msg_warning"), "Please specify an input video file or YouTube URL.")
            return

        # Prepare UI
        self.start_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.input_edit.setEnabled(False)
        self.src_combo.setEnabled(False)
        self.target_combo.setEnabled(False)
        self.open_folder_btn.setVisible(False)
        self.status_banner.setVisible(False)
        self.speaker_summary_label.setVisible(False)
        self.translation_quality_label.setVisible(False)
        
        self.progress_bar.setValue(0)
        self.progress_label.setText("Status: Queuing...")
        self.log_viewer.clear()
        
        from backend.services.project_repository import ProjectRepository
        from backend.models.project_models import ProjectMetadata, ProjectSnapshot, ExecutionState
        import time
        
        repo = ProjectRepository()
        
        if is_resume:
            project_id = self.resume_project_id
            
            # Preflight Speaker Validation
            project_data = repo.load(project_id)
            if project_data:
                output_mode = project_data.settings_snapshot.output_mode
                if output_mode in ["Subtitle + Voice", "Voice Only", "Subtitle + Audio Files"]:
                    stats = {}
                    import json
                    aligned_path = os.path.join("projects", project_id, "subtitle", "aligned_transcript.json")
                    if not os.path.exists(aligned_path):
                        aligned_path = os.path.join("projects", project_id, "subtitle", "transcript.json")
                        
                    if os.path.exists(aligned_path):
                        try:
                            with open(aligned_path, "r", encoding="utf-8") as f:
                                tdata = json.load(f)
                                for seg in tdata.get("segments", []):
                                    spk = seg.get("speaker_id")
                                    if spk:
                                        stats[spk] = stats.get(spk, 0) + 1
                        except Exception:
                            pass
                    
                    speaker_voices = {}
                    voice_mode = "SINGLE"
                    if os.path.exists("config/settings.json"):
                        try:
                            with open("config/settings.json", "r", encoding="utf-8") as f:
                                sdata = json.load(f)
                                speaker_voices = sdata.get("speaker_voices", {})
                                voice_mode = sdata.get("voice_mode", "SINGLE")
                        except Exception:
                            pass
                            
                    unconfigured = []
                    if voice_mode == "MULTI":
                        for spk, count in stats.items():
                            if count > 0:
                                voice = speaker_voices.get(spk, "")
                                if not voice:
                                    unconfigured.append((spk, count))
                                
                    if unconfigured:
                        loc = LocalizationService()
                        spk_name, spk_count = unconfigured[0]
                        
                        msg_text = loc.translate("msg_speaker_validation")
                        if msg_text == "msg_speaker_validation":
                            msg_text = f"Bạn chưa chọn giọng đọc cho {spk_name} ({spk_count} câu thoại)."
                        else:
                            msg_text = msg_text.format(spk_name, spk_count)
                            
                        msg_box = QMessageBox(self)
                        msg_box.setIcon(QMessageBox.Warning)
                        msg_box.setWindowTitle(loc.translate("msg_warning"))
                        msg_box.setText(msg_text)
                        
                        settings_btn = msg_box.addButton(loc.translate("btn_open_settings"), QMessageBox.ActionRole)
                        cancel_btn = msg_box.addButton(loc.translate("cancel"), QMessageBox.RejectRole)
                        
                        msg_box.exec()
                        
                        if msg_box.clickedButton() == settings_btn:
                            self.open_settings()
                            
            snapshot = ProjectSnapshot(output_mode=output_mode)
            exec_state = ExecutionState(status="Waiting")
            project_data = ProjectMetadata(
                project_id=project_id,
                project_name=project_name,
                created_at=time.time(),
                modified_at=time.time(),
                input_video=input_val,
                settings_snapshot=snapshot,
                languages={"source": self.src_combo.currentData(), "target": self.target_combo.currentData()},
                execution_state=exec_state
            )
            repo.save(project_data)

        self.log_viewer.append(f"[System] Enqueuing project {project_id}...")
        self.queue_service.enqueue(project_id)

    def read_queue_output(self, project_id, text):
        loc = LocalizationService()
        self.log_viewer.append(f"[{project_id}] {text}")
                        json.dump(tpl.payload.translation_settings, f)
                        
                    with open(os.path.join(project_dir, "characters.json"), "w", encoding="utf-8") as f:
                        json.dump(tpl.payload.character_profiles, f)
        self.log_viewer.append(f"[System] Enqueuing project {project_id}...")
        self.queue_service.enqueue(project_id)

    def read_queue_output(self, project_id, text):
        loc = LocalizationService()
        self.log_viewer.append(f"[{project_id}] {text}")
        
        # Map stages to progress
        if "Stage 1:" in text:
            self.progress_label.setText(loc.translate("stage_1"))
            self.progress_bar.setValue(12)
        elif "Stage 2:" in text:
            self.progress_label.setText(loc.translate("stage_2"))
            self.progress_bar.setValue(25)
        elif "Stage 3:" in text:
            self.progress_label.setText(loc.translate("stage_3"))
            self.progress_bar.setValue(37)
        elif "Stage 4:" in text:
            self.progress_label.setText(loc.translate("stage_4"))
            self.progress_bar.setValue(50)
            self.update_speaker_summary(project_id)
        elif "[Translation Quality Score]" in text:
            score = text.split("[Translation Quality Score]")[-1].strip()
            self.translation_quality_label.setText(f"{loc.translate('translation_quality')}: {score}")
            self.translation_quality_label.setVisible(True)
        elif "Stage 5:" in text:
            self.progress_label.setText(loc.translate("stage_5"))
            self.progress_bar.setValue(62)
            
        elif "Stage 6:" in text:
            self.progress_label.setText(loc.translate("stage_6"))
            self.progress_bar.setValue(75)
        elif "Stage 7:" in text:
            self.progress_label.setText(loc.translate("stage_7"))
            self.progress_bar.setValue(87)
        elif "Stage 8:" in text:
            self.progress_label.setText(loc.translate("stage_8"))
            self.progress_bar.setValue(95)
        elif "Alpha 0.1A E2E Pipeline completed successfully!" in text:
            self.progress_label.setText(loc.translate("stage_completed"))
            self.progress_bar.setValue(100)
            
    def update_speaker_summary(self, project_id):
        import os, json
        stats = {}
        total_segments = 0
        total_duration = 0.0
        aligned_path = os.path.join("projects", project_id, "subtitle", "aligned_transcript.json")
        if not os.path.exists(aligned_path):
            aligned_path = os.path.join("projects", project_id, "subtitle", "transcript.json")
            
        if os.path.exists(aligned_path):
            try:
                with open(aligned_path, "r", encoding="utf-8") as f:
                    tdata = json.load(f)
                    for seg in tdata.get("segments", []):
                        spk = seg.get("speaker_id")
                        if spk:
                            if spk not in stats:
                                stats[spk] = 0
                            stats[spk] += 1
                            total_segments += 1
                            start = seg.get("start", 0.0)
                            end = seg.get("end", 0.0)
                            total_duration += (end - start)
            except Exception:
                pass
                
        num_speakers = len(stats)
        if num_speakers == 0:
            return
            
        spk_text = "speaker" if num_speakers == 1 else "speakers"
        summary_text = f"🎤 Detected: {num_speakers} {spk_text} | {total_segments} segments | {total_duration:.1f} sec"
        self.speaker_summary_label.setText(summary_text)
        self.speaker_summary_label.setVisible(True)

    def queue_pipeline_finished(self, project_id, exit_code):
        loc = LocalizationService()
        self.start_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.input_edit.setEnabled(True)
        self.src_combo.setEnabled(True)
        self.target_combo.setEnabled(True)
        
        from backend.services.project_repository import ProjectRepository
        repo = ProjectRepository()
        try:
            project_data = repo.load(project_id)
            self.project_dir = repo.get_project_dir(project_id)
            mode = project_data.settings_snapshot.output_mode
        except Exception:
            self.project_dir = ""
            mode = "Subtitle + Voice"

        if exit_code == 0:

        idx = self.template_combo.findData(tpl_id)
        if idx >= 0:
            self.template_combo.setCurrentIndex(idx)

    def start_pipeline(self):
        input_val = self.input_edit.text().strip()
        is_resume = hasattr(self, 'resume_project_id') and self.resume_project_id is not None
        
        if not input_val and not is_resume:
            loc = LocalizationService()
            QMessageBox.warning(self, loc.translate("msg_warning"), "Please specify an input video file or YouTube URL.")
            return

        # Prepare UI
        self.start_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.input_edit.setEnabled(False)
        self.src_combo.setEnabled(False)
        self.target_combo.setEnabled(False)
        self.open_folder_btn.setVisible(False)
        self.status_banner.setVisible(False)
        self.speaker_summary_label.setVisible(False)
        self.translation_quality_label.setVisible(False)
        
        self.progress_bar.setValue(0)
        self.progress_label.setText("Status: Queuing...")
        self.log_viewer.clear()
        
        from backend.services.project_repository import ProjectRepository
        from backend.models.project_models import ProjectMetadata, ProjectSnapshot, ExecutionState
        import time
        
        repo = ProjectRepository()
        
        if is_resume:
            project_id = self.resume_project_id
            
            # Preflight Speaker Validation
            project_data = repo.load(project_id)
            if project_data:
                output_mode = project_data.settings_snapshot.output_mode
                if output_mode in ["Subtitle + Voice", "Voice Only", "Subtitle + Audio Files"]:
                    stats = {}
                    import json
                    aligned_path = os.path.join("projects", project_id, "subtitle", "aligned_transcript.json")
                    if not os.path.exists(aligned_path):
                        aligned_path = os.path.join("projects", project_id, "subtitle", "transcript.json")
                        
                    if os.path.exists(aligned_path):
                        try:
                            with open(aligned_path, "r", encoding="utf-8") as f:
                                tdata = json.load(f)
                                for seg in tdata.get("segments", []):
                                    spk = seg.get("speaker_id")
                                    if spk:
                                        stats[spk] = stats.get(spk, 0) + 1
                        except Exception:
                            pass
                    
                    speaker_voices = {}
                    voice_mode = "SINGLE"
                    if os.path.exists("config/settings.json"):
                        try:
                            with open("config/settings.json", "r", encoding="utf-8") as f:
                                sdata = json.load(f)
                                speaker_voices = sdata.get("speaker_voices", {})
                                voice_mode = sdata.get("voice_mode", "SINGLE")
                        except Exception:
                            pass
                            
                    unconfigured = []
                    if voice_mode == "MULTI":
                        for spk, count in stats.items():
                            if count > 0:
                                voice = speaker_voices.get(spk, "")
                                if not voice:
                                    unconfigured.append((spk, count))
                                
                    if unconfigured:
                        loc = LocalizationService()
                        spk_name, spk_count = unconfigured[0]
                        
                        msg_text = loc.translate("msg_speaker_validation")
                        if msg_text == "msg_speaker_validation":
                            msg_text = f"Bạn chưa chọn giọng đọc cho {spk_name} ({spk_count} câu thoại)."
                        else:
                            msg_text = msg_text.format(spk_name, spk_count)
                            
                        msg_box = QMessageBox(self)
                        msg_box.setIcon(QMessageBox.Warning)
                        msg_box.setWindowTitle(loc.translate("msg_warning"))
                        msg_box.setText(msg_text)
                        
                        settings_btn = msg_box.addButton(loc.translate("btn_open_settings"), QMessageBox.ActionRole)
                        cancel_btn = msg_box.addButton(loc.translate("cancel"), QMessageBox.RejectRole)
                        
                        msg_box.exec()
                        
                        if msg_box.clickedButton() == settings_btn:
                            self.open_settings()
                            
                        json.dump(tpl.payload.translation_settings, f)
                        
                    with open(os.path.join(project_dir, "characters.json"), "w", encoding="utf-8") as f:
                        json.dump(tpl.payload.character_profiles, f)
        self.log_viewer.append(f"[System] Enqueuing project {project_id}...")
        self.queue_service.enqueue(project_id)

    def read_queue_output(self, project_id, text):
        loc = LocalizationService()
        self.log_viewer.append(f"[{project_id}] {text}")
        
        # Map stages to progress
        if "Stage 1:" in text:
            self.progress_label.setText(loc.translate("stage_1"))
            self.progress_bar.setValue(12)
        elif "Stage 2:" in text:
            self.progress_label.setText(loc.translate("stage_2"))
            self.progress_bar.setValue(25)
        elif "Stage 3:" in text:
            self.progress_label.setText(loc.translate("stage_3"))
            self.progress_bar.setValue(37)
        elif "Stage 4:" in text:
            self.progress_label.setText(loc.translate("stage_4"))
            self.progress_bar.setValue(50)
            self.update_speaker_summary(project_id)
        elif "[Translation Quality Score]" in text:
            score = text.split("[Translation Quality Score]")[-1].strip()
            self.translation_quality_label.setText(f"{loc.translate('translation_quality')}: {score}")
            self.translation_quality_label.setVisible(True)
        elif "Stage 5:" in text:
            self.progress_label.setText(loc.translate("stage_5"))
            self.progress_bar.setValue(62)
            
        elif "Stage 6:" in text:
            self.progress_label.setText(loc.translate("stage_6"))
            self.progress_bar.setValue(75)
        elif "Stage 7:" in text:
            self.progress_label.setText(loc.translate("stage_7"))
            self.progress_bar.setValue(87)
        elif "Stage 8:" in text:
            self.progress_label.setText(loc.translate("stage_8"))
            self.progress_bar.setValue(95)
        elif "Alpha 0.1A E2E Pipeline completed successfully!" in text:
            self.progress_label.setText(loc.translate("stage_completed"))
            self.progress_bar.setValue(100)
            
    def update_speaker_summary(self, project_id):
        import os, json
        stats = {}
        total_segments = 0
        total_duration = 0.0
        aligned_path = os.path.join("projects", project_id, "subtitle", "aligned_transcript.json")
        if not os.path.exists(aligned_path):
            aligned_path = os.path.join("projects", project_id, "subtitle", "transcript.json")
            
        if os.path.exists(aligned_path):
            try:
                with open(aligned_path, "r", encoding="utf-8") as f:
                    tdata = json.load(f)
                    for seg in tdata.get("segments", []):
                        spk = seg.get("speaker_id")
                        if spk:
                            if spk not in stats:
                                stats[spk] = 0
                            stats[spk] += 1
                            total_segments += 1
                            start = seg.get("start", 0.0)
                            end = seg.get("end", 0.0)
                            total_duration += (end - start)
            except Exception:
                pass
                
        num_speakers = len(stats)
        if num_speakers == 0:
            return
            
        spk_text = "speaker" if num_speakers == 1 else "speakers"
        summary_text = f"🎤 Detected: {num_speakers} {spk_text} | {total_segments} segments | {total_duration:.1f} sec"
        self.speaker_summary_label.setText(summary_text)
        self.speaker_summary_label.setVisible(True)

    def queue_pipeline_finished(self, project_id, exit_code):
        loc = LocalizationService()
        self.start_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.input_edit.setEnabled(True)
        self.src_combo.setEnabled(True)
        self.target_combo.setEnabled(True)
        
        from backend.services.project_repository import ProjectRepository
        repo = ProjectRepository()
        try:
            project_data = repo.load(project_id)
            self.project_dir = repo.get_project_dir(project_id)
            mode = project_data.settings_snapshot.output_mode
        except Exception:
            self.project_dir = ""
            mode = "Subtitle + Voice"

        if exit_code == 0:

    def apply_template(self, tpl):
        pass

    def update_queue_ui(self):
        pass

    def check_recovery(self):
        pass

    def update_output_mode_desc(self):
        pass

    def open_output_folder(self):
        import os, subprocess, sys
        projects_dir = os.path.abspath('projects')
        if os.path.exists(projects_dir):
            if sys.platform == 'win32':
                os.startfile(projects_dir)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', projects_dir])
            else:
                subprocess.Popen(['xdg-open', projects_dir])

    def load_output_mode(self):
        import json, os
        settings_path = "config/workspace.json"
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    mode = data.get("output_mode", "Sub & Voice")
                    if mode == "Sub & Voice":
                        self.mode_sub_voice.setChecked(True)
                    elif mode == "Sub Only":
                        self.mode_sub_only.setChecked(True)
                    elif mode == "Voice Only":
                        self.mode_voice_only.setChecked(True)
                    elif mode == "Sub + Audio":
                        self.mode_sub_audio.setChecked(True)
            except Exception: pass

    def save_output_mode(self):
        import json, os
        mode = "Sub & Voice"
        if self.mode_sub_only.isChecked(): mode = "Sub Only"
        if self.mode_voice_only.isChecked(): mode = "Voice Only"
        if self.mode_sub_audio.isChecked(): mode = "Sub + Audio"
        
        settings_path = "config/workspace.json"
        data = {}
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception: pass
        data["output_mode"] = mode
        os.makedirs("config", exist_ok=True)
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception: pass

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
