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


class EdgeTTSSettingsWidget(QWidget):
    """Dedicated settings widget for Edge TTS.
    
    Edge TTS does NOT use an API key. It uses Microsoft's public TTS interface.
    Only shows: Voice List, Rate, Pitch, Volume, Test Audio.
    Does NOT show: API Key, Base URL, Test Connection, Refresh Voices.
    """
    
    test_audio_requested = Signal()
    voice_changed = Signal()

    def __init__(self, loc, parent=None):
        super().__init__(parent)
        self.loc = loc
        self._all_voices: list[dict] = []
        self.player = None
        self.audio_output = None
        
        self._init_ui()
        self._populate_default_voices()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # -- Voice selection --
        voice_group = QGroupBox("Voice")
        voice_form = QFormLayout(voice_group)
        
        self.voice_combo = QComboBox()
        self.voice_combo.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
        self.voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        voice_form.addRow(self.loc.translate("voice"), self.voice_combo)
        
        layout.addWidget(voice_group)
        
        # -- Parameters group: Rate, Pitch, Volume --
        params_group = QGroupBox("Parameters")
        params_form = QFormLayout(params_group)
        
        # Rate slider (-50% to +50%, default 0)
        rate_layout = QHBoxLayout()
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(-50, 50)
        self.rate_slider.setValue(0)
        self.rate_slider.setTickPosition(QSlider.TicksBelow)
        self.rate_slider.setTickInterval(10)
        self.rate_label = QLabel("0%")
        self.rate_slider.valueChanged.connect(lambda v: self.rate_label.setText(f"{v:+d}%"))
        rate_layout.addWidget(self.rate_slider, stretch=1)
        rate_layout.addWidget(self.rate_label)
        params_form.addRow("Rate", rate_layout)
        
        # Pitch slider (-50Hz to +50Hz, default 0)
        pitch_layout = QHBoxLayout()
        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setRange(-50, 50)
        self.pitch_slider.setValue(0)
        self.pitch_slider.setTickPosition(QSlider.TicksBelow)
        self.pitch_slider.setTickInterval(10)
        self.pitch_label = QLabel("0Hz")
        self.pitch_slider.valueChanged.connect(lambda v: self.pitch_label.setText(f"{v:+d}Hz"))
        pitch_layout.addWidget(self.pitch_slider, stretch=1)
        pitch_layout.addWidget(self.pitch_label)
        params_form.addRow("Pitch", pitch_layout)
        
        # Volume slider (0 to 100, default 100)
        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QSlider.TicksBelow)
        self.volume_slider.setTickInterval(10)
        self.volume_label = QLabel("100%")
        self.volume_slider.valueChanged.connect(lambda v: self.volume_label.setText(f"{v}%"))
        volume_layout.addWidget(self.volume_slider, stretch=1)
        volume_layout.addWidget(self.volume_label)
        params_form.addRow("Volume", volume_layout)
        
        layout.addWidget(params_group)
        
        # -- Test Audio button --
        self.test_audio_btn = QPushButton("▶ Test Audio")
        self.test_audio_btn.clicked.connect(self._on_test_audio)
        layout.addWidget(self.test_audio_btn)
        
        # -- Status label for test result --
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
    def _populate_default_voices(self):
        """Load voices from the Edge TTS provider or fallback list."""
        self._all_voices = [
            {"voice_id": "en-US-GuyNeural", "display_name": "Guy", "gender": "Male", "language": "en", "locale": "en-US"},
            {"voice_id": "en-US-JennyNeural", "display_name": "Jenny", "gender": "Female", "language": "en", "locale": "en-US"},
            {"voice_id": "en-GB-RyanNeural", "display_name": "Ryan", "gender": "Male", "language": "en", "locale": "en-GB"},
            {"voice_id": "en-GB-SoniaNeural", "display_name": "Sonia", "gender": "Female", "language": "en", "locale": "en-GB"},
            {"voice_id": "ja-JP-KeitaNeural", "display_name": "Keita", "gender": "Male", "language": "ja", "locale": "ja-JP"},
            {"voice_id": "ja-JP-NanamiNeural", "display_name": "Nanami", "gender": "Female", "language": "ja", "locale": "ja-JP"},
            {"voice_id": "vi-VN-NamMinhNeural", "display_name": "Nam Minh", "gender": "Male", "language": "vi", "locale": "vi-VN"},
            {"voice_id": "vi-VN-HoaiMyNeural", "display_name": "Hoai My", "gender": "Female", "language": "vi", "locale": "vi-VN"},
            {"voice_id": "ko-KR-SunHiNeural", "display_name": "SunHi", "gender": "Female", "language": "ko", "locale": "ko-KR"},
            {"voice_id": "ko-KR-InJoonNeural", "display_name": "InJoon", "gender": "Male", "language": "ko", "locale": "ko-KR"},
            {"voice_id": "zh-CN-XiaoxiaoNeural", "display_name": "Xiaoxiao", "gender": "Female", "language": "zh", "locale": "zh-CN"},
            {"voice_id": "zh-CN-YunxiNeural", "display_name": "Yunxi", "gender": "Male", "language": "zh", "locale": "zh-CN"},
            {"voice_id": "fr-FR-DeniseNeural", "display_name": "Denise", "gender": "Female", "language": "fr", "locale": "fr-FR"},
            {"voice_id": "fr-FR-HenriNeural", "display_name": "Henri", "gender": "Male", "language": "fr", "locale": "fr-FR"},
            {"voice_id": "de-DE-KatjaNeural", "display_name": "Katja", "gender": "Female", "language": "de", "locale": "de-DE"},
            {"voice_id": "de-DE-ConradNeural", "display_name": "Conrad", "gender": "Male", "language": "de", "locale": "de-DE"},
            {"voice_id": "es-ES-ElviraNeural", "display_name": "Elvira", "gender": "Female", "language": "es", "locale": "es-ES"},
            {"voice_id": "es-ES-AlvaroNeural", "display_name": "Alvaro", "gender": "Male", "language": "es", "locale": "es-ES"},
        ]
        
        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()
        for v in self._all_voices:
            display = v.get("display_name", v["voice_id"])
            locale = v.get("locale", "")
            label = f"{display} ({locale})" if locale else display
            self.voice_combo.addItem(label, v["voice_id"])
        self.voice_combo.blockSignals(False)
        
        print(f"\n[EDGE TTS] Populated {len(self._all_voices)} default voices.\n")
        
    def set_voices(self, voices: list[dict]):
        """Replace the voice list with data from the backend provider."""
        if voices:
            self._all_voices = voices
            prev_voice_id = self.voice_combo.currentData()
            self.voice_combo.blockSignals(True)
            self.voice_combo.clear()
            selected_index = -1
            for idx, v in enumerate(voices):
                vid = v.get("voice_id", "")
                display = v.get("display_name") or v.get("name") or vid
                locale = v.get("locale", v.get("language", ""))
                label = f"{display} ({locale})" if locale else display
                self.voice_combo.addItem(label, vid)
                if prev_voice_id and vid == prev_voice_id:
                    selected_index = idx
            if selected_index != -1:
                self.voice_combo.setCurrentIndex(selected_index)
            elif self.voice_combo.count() > 0:
                self.voice_combo.setCurrentIndex(0)
            self.voice_combo.blockSignals(False)
            print(f"\n[EDGE TTS] Updated to {len(voices)} voices from backend.\n")
        
    def _on_voice_changed(self):
        self.voice_changed.emit()
        
    def _on_test_audio(self):
        """Emit signal to trigger test audio generation."""
        self.test_audio_btn.setEnabled(False)
        self.test_audio_btn.setText("⏳ Generating...")
        self.status_label.setText("")
        self.test_audio_requested.emit()
        
    def _on_test_audio_finished(self, audio_data: bytes):
        """Play back the generated test audio."""
        self.test_audio_btn.setEnabled(True)
        self.test_audio_btn.setText("▶ Test Audio")
        
        if not audio_data:
            self.status_label.setText("<font color='red'>Test audio generation failed.</font>")
            return
            
        # Play the audio data
        import tempfile
        import os
        temp_path = os.path.join(tempfile.gettempdir(), "edge_tts_test.wav")
        try:
            with open(temp_path, "wb") as f:
                f.write(audio_data)
                
            if hasattr(self, 'player') and self.player:
                self.player.stop()
                
            from PySide6.QtCore import QUrl
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            self.player.setSource(QUrl.fromLocalFile(temp_path))
            self.player.play()
            self.status_label.setText("<font color='green'>Playing test audio...</font>")
        except Exception as e:
            self.status_label.setText(f"<font color='red'>Error: {e}</font>")
            
    def _on_test_audio_error(self, error_msg: str):
        self.test_audio_btn.setEnabled(True)
        self.test_audio_btn.setText("▶ Test Audio")
        self.status_label.setText(f"<font color='red'>Error: {error_msg}</font>")
        
    def get_selected_voice_id(self) -> str:
        return self.voice_combo.currentData() or ""
        
    def get_rate(self) -> int:
        return self.rate_slider.value()
        
    def get_pitch(self) -> int:
        return self.pitch_slider.value()
        
    def get_volume(self) -> int:
        return self.volume_slider.value()

    def load_config(self, conf):
        """Load Edge TTS settings from config."""
        providers = conf.get("providers", {})
        edge_config = providers.get("edge", conf.get("edge", {}))
        
        voice = edge_config.get("voice", "")
        if voice:
            idx = self.voice_combo.findData(voice)
            if idx != -1:
                self.voice_combo.setCurrentIndex(idx)
                
        rate = edge_config.get("rate", 0)
        self.rate_slider.setValue(rate)
        
        pitch = edge_config.get("pitch", 0)
        self.pitch_slider.setValue(pitch)
        
        volume = edge_config.get("volume", 100)
        self.volume_slider.setValue(volume)

    def save_config(self) -> dict:
        return {
            "voice": self.voice_combo.currentData() or "",
            "rate": self.rate_slider.value(),
            "pitch": self.pitch_slider.value(),
            "volume": self.volume_slider.value()
        }

    def closeEvent(self, event):
        if hasattr(self, 'player') and self.player:
            self.player.stop()
        super().closeEvent(event)