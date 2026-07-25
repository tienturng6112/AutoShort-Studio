                    stats[spk]["count"] += 1
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
        
        self.browser = CharacterBrowserWindow(char_mgr=cm, voice_manager=vm)
        self.browser.character_assigned.connect(self.setCharacter)
        self.browser.show()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize capability manager
        from backend.providers.provider_registry import ProviderRegistry
        from backend.providers.provider_capability_manager import ProviderCapabilityManager
        import os
        registry = ProviderRegistry()
        registry.inject_legacy_providers()
        registry.discover_providers(os.path.join("backend", "plugins", "providers"))
        self.cap_mgr = ProviderCapabilityManager(registry, config_dir="config")
        self.cap_mgr.refresh()
        
        self.chatanywhere_api_key = ""
        self.deepl_api_key = ""
        self.tts_provider = "Edge TTS"
        self.kira_api_key = ""
        self.kira_model = "kira-3.0-flash-tts"
        self.kira_speed = 1.0
        self.use_context_translation = True
        self.use_conversation_analyzer = True
        
        from backend.services.profile_service import ProfileService
        self.profile_service = ProfileService()
        self._updating_profile = False
        
        self.setWindowTitle("Settings")
        self.resize(450, 680)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.init_ui()
        self.repopulate_speaker_voices()
        self.load_settings()
        self.update_ui_text()

    def toggle_voice_mode(self):
        is_single = self.mode_single_voice.isChecked()
        self.single_voice_container.setVisible(is_single)
        self.multi_voice_container.setVisible(not is_single)

    def update_ui_text(self):
        loc = LocalizationService()
        self.setWindowTitle(loc.translate("settings"))
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
