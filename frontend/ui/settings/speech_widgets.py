import logging
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QLabel, QHBoxLayout, QVBoxLayout, QSlider, QMessageBox, QGroupBox, QCheckBox, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from backend.services.localization_service import LocalizationService

loc = LocalizationService()
logger = logging.getLogger(__name__)

class GeminiSpeechSettingsWidget(QWidget):
    test_requested = Signal()
    refresh_models_requested = Signal()
    refresh_voices_requested = Signal()
    preview_requested = Signal(str, str, str, str, float, float) # text, model, voice, lang, speed, pitch
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        group = QGroupBox(loc.translate("gemini_speech_config", "Gemini Speech Configuration"))
        form = QFormLayout()
        
        self.use_custom_key_chk = QCheckBox("Use custom API Key")
        self.use_custom_key_chk.toggled.connect(self._on_custom_key_toggled)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setVisible(False)
        self.capabilities_map = {}
        self.api_key_edit.setPlaceholderText("AIza...")
        
        # Model
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        self.refresh_model_btn = QPushButton(loc.translate("btn_refresh_models", "Refresh Models"))
        self.refresh_model_btn.clicked.connect(self.refresh_models)
        model_layout.addWidget(self.model_combo, 1)
        model_layout.addWidget(self.refresh_model_btn)
        self.capabilities_label = QLabel()
        self.capabilities_label.setStyleSheet("color: gray; font-size: 11px;")
        
        # Voice
        voice_layout = QHBoxLayout()
        self.voice_combo = QComboBox()
        self.refresh_voice_btn = QPushButton(loc.translate("btn_refresh_voices", "Refresh Voices"))
        self.refresh_voice_btn.clicked.connect(self.refresh_voices)
        voice_layout.addWidget(self.voice_combo, 1)
        voice_layout.addWidget(self.refresh_voice_btn)
        
        self.lang_edit = QComboBox()
        self.lang_edit.setEditable(True)
        languages = [
            "Auto Detect", "Vietnamese (vi-VN)", "English (en-US)", 
            "Japanese (ja-JP)", "Korean (ko-KR)", "Chinese Simplified (zh-CN)", 
            "Chinese Traditional (zh-TW)", "French (fr-FR)", "German (de-DE)", 
            "Spanish (es-ES)", "Portuguese (pt-BR)", "Russian (ru-RU)", 
            "Thai (th-TH)", "Indonesian (id-ID)"
        ]
        self.lang_edit.addItems(languages)
        self.lang_edit.setCurrentText("English (en-US)")
        self.style_edit = QLineEdit("")
        self.style_edit.setPlaceholderText("e.g. happy, sad (Optional)")
        
        # Speed & Pitch
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(25, 400) # 0.25 to 4.0
        self.speed_slider.setValue(100)
        self.speed_val = QLabel("1.0")
        self.speed_slider.valueChanged.connect(lambda v: self.speed_val.setText(f"{v/100:.2f}"))
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_val)
        
        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setRange(-20, 20)
        self.pitch_slider.setValue(0)
        self.pitch_val = QLabel("0")
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_val.setText(str(v)))
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(self.pitch_slider)
        pitch_layout.addWidget(self.pitch_val)
        
        # Preview
        self.preview_text = QLineEdit(loc.translate("preview_text_default", "Hello, this is a test of Gemini Speech."))
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(self.preview_text, 1)
        self.preview_btn = QPushButton(loc.translate("btn_generate_test_audio", "Generate Test Audio"))
        self.preview_btn.clicked.connect(self.play_preview)
        preview_layout.addWidget(self.preview_btn)
        
        # Test Connection
        self.test_btn = QPushButton(loc.translate("btn_test_connection", "Test Connection"))
        self.test_btn.clicked.connect(self.test_connection)
        self.status_lbl = QLabel(loc.translate("status_idle", "Idle"))
        test_layout = QHBoxLayout()
        test_layout.addWidget(self.test_btn)
        test_layout.addWidget(self.status_lbl)
        
        api_layout = QVBoxLayout()
        api_layout.addWidget(self.use_custom_key_chk)
        api_layout.addWidget(self.api_key_edit)
        form.addRow(loc.translate("lbl_api_key", "API Key:"), api_layout)
        form.addRow(loc.translate("lbl_model", "Model:"), model_layout)
        form.addRow("", self.capabilities_label)
        form.addRow(loc.translate("lbl_voice", "Voice:"), voice_layout)
        form.addRow(loc.translate("lbl_language", "Language:"), self.lang_edit)
        form.addRow(loc.translate("lbl_speaking_style", "Speaking Style:"), self.style_edit)
        form.addRow(loc.translate("lbl_speed", "Speed:"), speed_layout)
        form.addRow(loc.translate("lbl_pitch", "Pitch:"), pitch_layout)
        form.addRow(loc.translate("lbl_preview_text", "Preview Text:"), preview_layout)
        form.addRow("", test_layout)
        
        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
    def _on_custom_key_toggled(self, checked):
        self.api_key_edit.setVisible(checked)

    def test_connection(self):
        self.status_lbl.setText("Testing...")
        self.test_btn.setEnabled(False)
        self.test_requested.emit()
        
    def _on_model_changed(self, text):
        caps = self.capabilities_map.get(text, [])
        if caps:
            self.capabilities_label.setText(" ".join(f"✓ {c}" for c in caps))
        else:
            self.capabilities_label.setText("")

    def _on_test_finished(self, res):
        self.test_btn.setEnabled(True)
        if res.get("success"):
            models = res.get('models', []); self.capabilities_map.update(res.get('capabilities', {}))
            self.status_lbl.setText(f"✓ Connected. {len(models)} models.")
            self.status_lbl.setStyleSheet("color: green;")
            if not self.model_combo.currentText() and models:
                self.model_combo.addItems(models)
        else:
            self.status_lbl.setText(f"Failed: {res.get('message')}")
            self.status_lbl.setStyleSheet("color: red;")
            
    def refresh_models(self):
        self.refresh_model_btn.setEnabled(False)
        self.refresh_models_requested.emit()
        
    def _on_refresh_models_finished(self, res):
        self.refresh_model_btn.setEnabled(True)
        if res.get("success"):
            models = res.get("models", []); self.capabilities_map.update(res.get('capabilities', {}))
            curr = self.model_combo.currentText()
            self.model_combo.clear()
            self.model_combo.addItems(models)
            if curr in models:
                self.model_combo.setCurrentText(curr)
                
    def refresh_voices(self):
        self.refresh_voices_requested.emit()
            
    def play_preview(self):
        self.preview_btn.setEnabled(False)
        self.preview_btn.setText("Generating...")
        self.preview_requested.emit(
            self.preview_text.text(),
            self.model_combo.currentText(),
            self.voice_combo.currentText(),
            self.lang_edit.currentText(),
            self.speed_slider.value() / 100.0,
            float(self.pitch_slider.value())
        )
        
    def _on_preview_finished(self, audio_bytes):
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText(loc.translate("btn_generate_test_audio", "Generate Test Audio"))
        
        import tempfile
        import os
        from PySide6.QtCore import QUrl
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.write(fd, audio_bytes)
        os.close(fd)
        
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        
    def _on_preview_error(self, err):
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText(loc.translate("btn_generate_test_audio", "Generate Test Audio"))
        QMessageBox.warning(self, "Preview Failed", err)

    def load_config(self, conf):
        use_custom = conf.get("use_custom_key", False)
        self.use_custom_key_chk.setChecked(use_custom)
        self.api_key_edit.setVisible(use_custom)
        self.api_key_edit.setText(conf.get("api_key", ""))
        self.model_combo.setCurrentText(conf.get("model", "gemini-1.5-flash"))
        self.voice_combo.setCurrentText(conf.get("voice", "Puck"))
        self.lang_edit.setCurrentText(conf.get("language", "English (en-US)"))
        self.style_edit.setText(conf.get("style", ""))
        
        speed = conf.get("speed", 1.0)
        self.speed_slider.setValue(int(speed * 100))
        
        pitch = conf.get("pitch", 0)
        self.pitch_slider.setValue(int(pitch))

    def save_config(self):
        return {
            "use_custom_key": self.use_custom_key_chk.isChecked(),
            "api_key": self.api_key_edit.text() if self.use_custom_key_chk.isChecked() else "",
            "model": self.model_combo.currentText(),
            "voice": self.voice_combo.currentText(),
            "language": self.lang_edit.currentText(),
            "style": self.style_edit.text(),
            "speed": self.speed_slider.value() / 100.0,
            "pitch": self.pitch_slider.value()
        }


class ElevenLabsSettingsWidget(QWidget):
    test_requested = Signal()
    refresh_voices_requested = Signal()
    preview_requested = Signal(str, str, str, str, float, float) # text, model, voice, lang, speed, pitch

    def __init__(self, loc, parent=None):
        super().__init__(parent)
        self.loc = loc
        self.api_key = ""
        self._all_voices: list[dict] = []
        self._favorites: set = self._load_favorites()
        self.player = None
        self.audio_output = None
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # API Key
        api_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("ElevenLabs API Key")
        api_layout.addWidget(QLabel(self.loc.translate("api_key")))
        api_layout.addWidget(self.api_key_edit)
        self.layout.addLayout(api_layout)
        
        # Form Layout
        form = QFormLayout()
        
        # Model
        self.model_combo = QComboBox()
        self.model_combo.addItems(["eleven_multilingual_v2", "eleven_monolingual_v1", "eleven_multilingual_v1", "eleven_turbo_v2", "eleven_turbo_v2_5"])
        form.addRow(self.loc.translate("model_name"), self.model_combo)
        
        # Language Filter
        self.lang_filter_combo = QComboBox()
        self.lang_filter_combo.addItem("All Languages")
        self.lang_filter_combo.currentTextChanged.connect(self._apply_voice_filters)
        form.addRow(self.loc.translate("language", "Language"), self.lang_filter_combo)
        
        # Search & Favorites Checkbox
        search_fav_layout = QHBoxLayout()
        self.search_voice_edit = QLineEdit()
        self.search_voice_edit.setPlaceholderText("Search Voice")
        self.search_voice_edit.textChanged.connect(self._apply_voice_filters)
        
        self.favorites_only_chk = QCheckBox(self.loc.translate("favorites_only", "Favorites Only"))
        self.favorites_only_chk.stateChanged.connect(self._apply_voice_filters)
        
        search_fav_layout.addWidget(self.search_voice_edit, stretch=1)
        search_fav_layout.addWidget(self.favorites_only_chk)
        form.addRow("Search Voice", search_fav_layout)
        
        # Voice Combo & Refresh & Favorite Toggle
        self.voice_combo = QComboBox()
        self.voice_combo.currentIndexChanged.connect(self._on_voice_selection_changed)
        
        self.refresh_voices_btn = QPushButton(self.loc.translate("refresh_voices", "Refresh Voices"))
        self.refresh_voices_btn.clicked.connect(self.refresh_voices)
        
        self.favorite_btn = QPushButton("☆ Favorite")
        self.favorite_btn.clicked.connect(self._toggle_favorite)
        
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(self.voice_combo, stretch=1)
        voice_layout.addWidget(self.favorite_btn)
        voice_layout.addWidget(self.refresh_voices_btn)
        
        form.addRow(self.loc.translate("voice"), voice_layout)
        self.layout.addLayout(form)
        
        # Voice Details Metadata Panel
        self.meta_group = QGroupBox("Voice Details")
        self.meta_layout = QFormLayout(self.meta_group)
        
        self.lbl_meta_name = QLabel("-")
        self.lbl_meta_lang = QLabel("-")
        self.lbl_meta_gender = QLabel("-")
        self.lbl_meta_category = QLabel("-")
        self.lbl_meta_desc = QLabel("-")
        self.lbl_meta_labels = QLabel("-")
        self.lbl_meta_id = QLabel("-")
        
        # ComboBox size adjust policy to prevent expanding window minimum width
        self.model_combo.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
        self.lang_filter_combo.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
        self.voice_combo.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
        
        self.meta_layout.addRow("Name:", self.lbl_meta_name)
        self.meta_layout.addRow("Language:", self.lbl_meta_lang)
        self.meta_layout.addRow("Gender:", self.lbl_meta_gender)
        self.meta_layout.addRow("Category:", self.lbl_meta_category)
        self.meta_layout.addRow("Description:", self.lbl_meta_desc)
        self.meta_layout.addRow("Labels:", self.lbl_meta_labels)
        self.meta_layout.addRow("Voice ID:", self.lbl_meta_id)
        
        for lbl in [
            self.lbl_meta_name, self.lbl_meta_lang, self.lbl_meta_gender,
            self.lbl_meta_category, self.lbl_meta_desc, self.lbl_meta_labels, self.lbl_meta_id
        ]:
            lbl.setWordWrap(True)
            lbl.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            
        self.meta_scroll = QScrollArea()
        self.meta_scroll.setWidgetResizable(True)
        self.meta_scroll.setWidget(self.meta_group)
        self.meta_scroll.setMaximumHeight(140)
        self.layout.addWidget(self.meta_scroll)
        
        # Status Block
        self.status_group = QGroupBox(self.loc.translate("status"))
        status_layout = QFormLayout(self.status_group)
        
        self.lbl_status = QLabel("Unknown")
        self.lbl_latency = QLabel("-")
        self.lbl_account = QLabel("-")
        self.lbl_quota = QLabel("-")
        
        status_layout.addRow("Status:", self.lbl_status)
        status_layout.addRow("Latency:", self.lbl_latency)
        status_layout.addRow("Account:", self.lbl_account)
        status_layout.addRow("Quota:", self.lbl_quota)
        self.layout.addWidget(self.status_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.test_conn_btn = QPushButton(self.loc.translate("test_connection"))
        self.test_conn_btn.clicked.connect(self.test_connection)
        self.preview_btn = QPushButton(self.loc.translate("preview_voice", "▶ Preview Voice"))
        self.preview_btn.clicked.connect(self.preview_voice)
        
        btn_layout.addWidget(self.test_conn_btn)
        btn_layout.addWidget(self.preview_btn)
        self.layout.addLayout(btn_layout)
        
        self.layout.addStretch()

    def _load_favorites(self) -> set:
        import json, os
        fav_path = os.path.join("config", "elevenlabs_favorites.json")
        if os.path.exists(fav_path):
            try:
                with open(fav_path, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                pass
        return set()

    def _save_favorites(self):
        import json, os
        os.makedirs("config", exist_ok=True)
        fav_path = os.path.join("config", "elevenlabs_favorites.json")
        with open(fav_path, "w", encoding="utf-8") as f:
            json.dump(list(self._favorites), f, indent=4)

    def _toggle_favorite(self):
        vid = self.voice_combo.currentData()
        if not vid:
            return
        if vid in self._favorites:
            self._favorites.remove(vid)
            print(f"\n[FAVORITES]\n  Favorite Count: {len(self._favorites)}\n  Removed: {vid}\n===============\n")
        else:
            self._favorites.add(vid)
            print(f"\n[FAVORITES]\n  Favorite Count: {len(self._favorites)}\n  Added: {vid}\n===============\n")
            
        self._save_favorites()
        self._on_voice_selection_changed()
        if self.favorites_only_chk.isChecked():
            self._apply_voice_filters()

    def _on_voice_selection_changed(self):
        self._stop_preview()
        vid = self.voice_combo.currentData()
        
        # Update Favorite Button text
        if vid and vid in self._favorites:
            self.favorite_btn.setText("★ Favorite")
        else:
            self.favorite_btn.setText("☆ Favorite")
            
        # Find voice metadata
        voice_dict = next((v for v in self._all_voices if v.get("voice_id") == vid), None)
        
        if voice_dict:
            name = voice_dict.get("name") or voice_dict.get("display_name") or vid
            lang = voice_dict.get("language") or "Unknown"
            gender = voice_dict.get("gender") or "Unknown"
            category = voice_dict.get("category") or ""
            desc = voice_dict.get("description") or ""
            labels = str(voice_dict.get("labels", {})) if voice_dict.get("labels") else ""
            preview_url = voice_dict.get("preview_url")
            
            self.lbl_meta_name.setText(name)
            self.lbl_meta_lang.setText(lang)
            self.lbl_meta_gender.setText(gender)
            self.lbl_meta_id.setText(vid)
            
            # Hide/show optional fields
            self.lbl_meta_category.setText(category)
            self.meta_layout.setRowVisible(self.lbl_meta_category, bool(category))
            
            self.lbl_meta_desc.setText(desc)
            self.meta_layout.setRowVisible(self.lbl_meta_desc, bool(desc))
            
            self.lbl_meta_labels.setText(labels)
            self.meta_layout.setRowVisible(self.lbl_meta_labels, bool(labels))
            
            has_preview = bool(preview_url)
            self.preview_btn.setEnabled(has_preview)
            
            print(f"\n[VOICE PREVIEW]")
            print(f"  Voice ID:          {vid}")
            print(f"  Voice Name:        {name}")
            print(f"  Preview Available: {has_preview}")
            print("===================\n")
        else:
            self.preview_btn.setEnabled(False)

    def test_connection(self):
        self.test_conn_btn.setEnabled(False)
        self.test_conn_btn.setText(self.loc.translate("testing_connection", "Testing..."))
        self.test_requested.emit()

    def _on_test_finished(self, res):
        self.test_conn_btn.setEnabled(True)
        self.test_conn_btn.setText(self.loc.translate("test_connection"))
        
        if res.get("success"):
            self.lbl_status.setText(f"<font color='green'>{res.get('message')}</font>")
            self.lbl_account.setText(res.get("account_type", "Unknown"))
            self.lbl_quota.setText(f"{res.get('quota_used', 0)} / {res.get('quota_limit', 0)}")
            self.refresh_voices()
        else:
            self.lbl_status.setText(f"<font color='red'>{res.get('message')}</font>")
            self.lbl_account.setText("-")
            self.lbl_quota.setText("-")
            
        latency = res.get("latency_ms")
        if latency:
            self.lbl_latency.setText(f"{latency} ms")

    def refresh_voices(self):
        self.refresh_voices_btn.setEnabled(False)
        self.refresh_voices_requested.emit()

    def _on_refresh_voices_finished(self, voices):
        self.refresh_voices_btn.setEnabled(True)
        self._all_voices = [
            v if isinstance(v, dict) else {
                "voice_id": getattr(v, "voice_id", ""),
                "name": getattr(v, "name", getattr(v, "display_name", "")),
                "display_name": getattr(v, "display_name", getattr(v, "name", "")),
                "language": getattr(v, "language", "en-US"),
                "gender": getattr(v, "gender", "Unknown"),
                "category": getattr(v, "category", None),
                "description": getattr(v, "description", None),
                "labels": getattr(v, "labels", None),
                "preview_url": getattr(v, "preview_url", None)
            } for v in voices
        ]
        
        # Dynamic languages dropdown
        current_lang = self.lang_filter_combo.currentText()
        self.lang_filter_combo.blockSignals(True)
        self.lang_filter_combo.clear()
        self.lang_filter_combo.addItem("All Languages")
        
        unique_langs = sorted(list({
            v.get("language") for v in self._all_voices if v.get("language")
        }))
        for lang in unique_langs:
            self.lang_filter_combo.addItem(lang)
            
        if self.lang_filter_combo.findText(current_lang) != -1:
            self.lang_filter_combo.setCurrentText(current_lang)
        self.lang_filter_combo.blockSignals(False)
        
        self._apply_voice_filters()

    def _apply_voice_filters(self):
        lang_filter = self.lang_filter_combo.currentText() if hasattr(self, "lang_filter_combo") else "All Languages"
        search_text = self.search_voice_edit.text().strip().lower() if hasattr(self, "search_voice_edit") else ""
        favorites_only = self.favorites_only_chk.isChecked() if hasattr(self, "favorites_only_chk") else False
        
        prev_voice_id = self.voice_combo.currentData()
        
        filtered = []
        for v in self._all_voices:
            vid = v.get("voice_id", "")
            v_lang = v.get("language", "")
            v_name = (v.get("name") or v.get("display_name") or "").lower()
            v_desc = (v.get("description") or "").lower()
            v_labels = str(v.get("labels") or "").lower()
            
            if favorites_only and vid not in self._favorites:
                continue
                
            if lang_filter != "All Languages" and v_lang != lang_filter:
                continue
                
            if search_text and (search_text not in v_name and search_text not in v_desc and search_text not in v_labels):
                continue
                
            filtered.append(v)
            
        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()
        
        selected_index = -1
        for idx, v in enumerate(filtered):
            vid = v.get("voice_id", "")
            vname = v.get("name") or v.get("display_name") or vid
            self.voice_combo.addItem(vname, vid)
            if prev_voice_id and vid == prev_voice_id:
                selected_index = idx
                
        if selected_index != -1:
            self.voice_combo.setCurrentIndex(selected_index)
        elif self.voice_combo.count() > 0:
            self.voice_combo.setCurrentIndex(0)
            
        self.voice_combo.blockSignals(False)
        
        self._on_voice_selection_changed()
        
        current_voice_id = self.voice_combo.currentData() if self.voice_combo.count() > 0 else (prev_voice_id or "None")
        
        print("\n[VOICE FILTER AUDIT]")
        print(f"  Total Voices:        {len(self._all_voices)}")
        print(f"  Language Filter:     {lang_filter}")
        print(f"  Search Text:         {search_text}")
        print(f"  Visible Voices:      {len(filtered)}")
        print(f"  Selected Voice ID:   {current_voice_id}")
        print("=====================\n")

    def preview_voice(self):
        if self.voice_combo.count() == 0:
            return
            
        vid = self.voice_combo.currentData()
        voice_dict = next((v for v in self._all_voices if v.get("voice_id") == vid), None)
        preview_url = voice_dict.get("preview_url") if voice_dict else None
        
        if hasattr(self, 'player') and self.player and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._stop_preview()
            return
            
        if not preview_url:
            return
            
        self.preview_btn.setText("Stop")
        print(f"\n[VOICE PREVIEW]\n  Voice ID: {vid}\n  Voice Name: {self.voice_combo.currentText()}\n  Preview Started: True\n===============\n")
        
        from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
        from PySide6.QtCore import QUrl
        
        if hasattr(self, 'player') and self.player:
            self.player.stop()
            
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl(preview_url))
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.play()

    def _on_playback_state_changed(self, state):
        from PySide6.QtMultimedia import QMediaPlayer
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.preview_btn.setText(self.loc.translate("preview_voice", "▶ Preview Voice"))

    def _stop_preview(self):
        if hasattr(self, 'player') and self.player:
            self.player.stop()
            print("\n[VOICE PREVIEW]\n  Preview Stopped: True\n===============\n")
        self.preview_btn.setText(self.loc.translate("preview_voice", "▶ Preview Voice"))

    def closeEvent(self, event):
        self._stop_preview()
        super().closeEvent(event)

    def load_config(self, conf):
        providers = conf.get("providers", {})
        el_config = providers.get("elevenlabs", conf.get("elevenlabs", {}))
        self.api_key_edit.setText(el_config.get("api_key", ""))
        model = el_config.get("model", "eleven_multilingual_v2")
        idx = self.model_combo.findText(model)
        if idx != -1:
            self.model_combo.setCurrentIndex(idx)
        else:
            self.model_combo.setCurrentText(model)

    def save_config(self):
        return {
            "api_key": self.api_key_edit.text().strip(),
            "model": self.model_combo.currentText()
        }


class KiraSettingsWidget(QWidget):
    test_requested = Signal()
    refresh_voices_requested = Signal()
    preview_requested = Signal(str, str, str, str, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_voices = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        group = QGroupBox("Kira Speech Configuration")
        form = QFormLayout()

        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Kira API Key")

        # Base URL
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://kiraai.vn/api/v1")

        # Model
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems(["kira-3.0-flash-tts", "kira-3.0-pro-tts"])
        model_layout.addWidget(self.model_combo, 1)

        # Speed
        self.speed_edit = QLineEdit("1.0")

        # Voice
        voice_layout = QHBoxLayout()
        self.voice_combo = QComboBox()
        self.refresh_voice_btn = QPushButton("Refresh Voices")
        self.refresh_voice_btn.clicked.connect(self.refresh_voices)
        voice_layout.addWidget(self.voice_combo, 1)
        voice_layout.addWidget(self.refresh_voice_btn)

        # Preview
        self.preview_text = QLineEdit("Xin chào, đây là giọng nói từ Kira TTS.")
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(self.preview_text, 1)
        self.preview_btn = QPushButton("Generate Test Audio")
        self.preview_btn.clicked.connect(self.play_preview)
        preview_layout.addWidget(self.preview_btn)

        # Test Connection
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        self.status_lbl = QLabel("Idle")
        test_layout = QHBoxLayout()
        test_layout.addWidget(self.test_btn)
        test_layout.addWidget(self.status_lbl)

        form.addRow("API Key:", self.api_key_edit)
        form.addRow("Base URL:", self.base_url_edit)
        form.addRow("Model:", model_layout)
        form.addRow("Speed:", self.speed_edit)
        form.addRow("Voice:", voice_layout)
        form.addRow("Preview Text:", preview_layout)
        form.addRow("", test_layout)

        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

    def test_connection(self):
        self.test_btn.setEnabled(False)
        self.status_lbl.setText("Testing...")
        self.test_requested.emit()

    def _on_test_finished(self, res):
        self.test_btn.setEnabled(True)
        if res.get("success"):
            models = res.get('models', [])
            self.status_lbl.setText("✓ Connected.")
            self.status_lbl.setStyleSheet("color: green;")
            if models:
                curr = self.model_combo.currentText()
                self.model_combo.clear()
                self.model_combo.addItems(models)
                if curr in models:
                    self.model_combo.setCurrentText(curr)
        else:
            self.status_lbl.setText(f"Failed: {res.get('message')}")
            self.status_lbl.setStyleSheet("color: red;")

    def refresh_voices(self):
        self.refresh_voice_btn.setEnabled(False)
        self.refresh_voices_requested.emit()

    def _on_refresh_voices_finished(self, voices):
        self.refresh_voice_btn.setEnabled(True)
        self._all_voices = [
            v if isinstance(v, dict) else {
                "voice_id": getattr(v, "voice_id", ""),
                "name": getattr(v, "name", getattr(v, "display_name", "")),
                "display_name": getattr(v, "display_name", getattr(v, "name", "")),
                "language": getattr(v, "language", "vi"),
                "gender": getattr(v, "gender", "Neutral"),
                "category": getattr(v, "category", None),
                "description": getattr(v, "description", None),
                "labels": getattr(v, "labels", None),
                "preview_url": getattr(v, "preview_url", None)
            } for v in voices
        ]

        prev_voice_id = self.voice_combo.currentData()
        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()
        selected_index = -1
        for idx, v in enumerate(self._all_voices):
            vid = v.get("voice_id", "")
            vname = v.get("display_name") or v.get("name") or vid
            self.voice_combo.addItem(vname, vid)
            if prev_voice_id and vid == prev_voice_id:
                selected_index = idx
        if selected_index != -1:
            self.voice_combo.setCurrentIndex(selected_index)
        elif self.voice_combo.count() > 0:
            self.voice_combo.setCurrentIndex(0)
        self.voice_combo.blockSignals(False)

    def play_preview(self):
        self.preview_btn.setEnabled(False)
        self.preview_btn.setText("Generating...")
        self.preview_requested.emit(
            self.preview_text.text(),
            self.model_combo.currentText(),
            self.voice_combo.currentText(),
            "",
            float(self.speed_edit.text() or "1.0"),
            0.0
        )

    def _on_preview_finished(self, audio_bytes):
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText("Generate Test Audio")
        import tempfile, os
        from PySide6.QtCore import QUrl
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.write(fd, audio_bytes)
        os.close(fd)
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()

    def _on_preview_error(self, err):
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText("Generate Test Audio")
        QMessageBox.warning(self, "Preview Failed", err)

    def load_config(self, conf):
        providers = conf.get("providers", {})
        kira_config = providers.get("kira", conf.get("kira", {}))
        self.api_key_edit.setText(kira_config.get("api_key", ""))
        self.base_url_edit.setText(kira_config.get("base_url", "https://kiraai.vn/api/v1"))
        self.speed_edit.setText(str(kira_config.get("speed", "1.0")))
        model = kira_config.get("model", "kira-3.0-flash-tts")
        idx = self.model_combo.findText(model)
        if idx != -1:
            self.model_combo.setCurrentIndex(idx)
        else:
            self.model_combo.setCurrentText(model)

    def save_config(self):
        return {
            "api_key": self.api_key_edit.text().strip(),
            "base_url": self.base_url_edit.text().strip(),
            "model": self.model_combo.currentText().strip(),
            "speed": float(self.speed_edit.text().strip() or "1.0")
        }