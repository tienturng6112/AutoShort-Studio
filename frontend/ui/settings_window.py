import json
import os
import traceback
import sys

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QPushButton, QTabWidget,
    QCheckBox, QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
    QFileDialog, QScrollArea, QGridLayout, QStackedWidget,
    QSlider, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl

from backend.services.localization_service import LocalizationService
from backend.services.speech_facade_service import SpeechFacadeService
from backend.services.translation_facade_service import TranslationFacadeService
from backend.providers.speech.manager import SpeechProviderManager

loc = LocalizationService()

# --------------- workers ---------------
class ServiceConnectionWorker(QThread):
    finished = Signal(dict)
    def __init__(self, svc: SpeechFacadeService, provider_id: str):
        super().__init__()
        self._svc = svc
        self._pid = provider_id
    def run(self):
        try:
            import asyncio
            coro = self._svc.test_connection(self._pid)
            res = asyncio.run(coro)
            self.finished.emit(res or {})
        except Exception as e:
            self.finished.emit({"success": False, "message": repr(e)})

class ServiceRefreshWorker(QThread):
    finished = Signal(dict)
    def __init__(self, svc: SpeechFacadeService, provider_id: str, resource_type: str):
        super().__init__()
        self._svc = svc
        self._pid = provider_id
        self._rtype = resource_type
    def run(self):
        try:
            import asyncio
            if self._rtype == "voices":
                coro = self._svc.refresh_voices(self._pid)
            else:
                coro = self._svc.refresh_models(self._pid)
            res = asyncio.run(coro)
            self.finished.emit(res or {})
        except Exception as e:
            self.finished.emit({"success": False, "message": repr(e)})

class ServicePreviewWorker(QThread):
    finished = Signal(bytes, str)
    error = Signal(str)
    def __init__(self, svc: SpeechFacadeService, provider_id: str, req: dict):
        super().__init__()
        self._svc = svc
        self._pid = provider_id
        self._req = req
    def run(self):
        try:
            import asyncio
            extra_kwargs = {k: v for k, v in self._req.items() if k not in ("text", "voice_name")}
            audio = asyncio.run(self._svc.preview(self._pid, self._req.get("text", ""), self._req.get("voice_name", ""), **extra_kwargs))
            voice_used = self._req.get("voice_name", "")
            self.finished.emit(audio, voice_used)
        except Exception as e:
            self.error.emit(repr(e))


class SettingsWindow(QWidget):
    settings_saved = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = type('State', (), {})()
        self._state.translation_provider = "chatanywhere"
        self._state.speech_provider = "edge"
        
        self._speech_svc = SpeechFacadeService()
        self._trans_svc = TranslationFacadeService()
        self._trans_widgets = {}
        self._speech_widgets = {}
        
        self.init_ui()
        self.init_translation_widgets()
        self.init_speech_widgets()
        self.load_settings()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        # ---------- tab general ----------
        self.tab_general = QWidget()
        gen_layout = QVBoxLayout(self.tab_general)
        gen_scroll = QScrollArea()
        gen_scroll.setWidgetResizable(True)
        gen_content = QWidget()
        gen_form = QFormLayout(gen_content)
        
        # translation
        trans_group = QGroupBox(loc.translate("group_translation"))
        trans_layout = QVBoxLayout()
        self.provider_combo = QComboBox()
        trans_layout.addWidget(QLabel(loc.translate("lbl_translation_provider")))
        trans_layout.addWidget(self.provider_combo)
        self.trans_stack = QStackedWidget()
        trans_layout.addWidget(self.trans_stack)
        trans_group.setLayout(trans_layout)
        gen_form.addRow(trans_group)
        
        # speech
        speech_group = QGroupBox(loc.translate("group_speech"))
        speech_layout = QVBoxLayout()
        
        self.tts_provider_combo = QComboBox()
        self.tts_provider_combo.addItems([
            "Edge TTS", "ElevenLabs"
        ])
        self.tts_provider_combo.currentTextChanged.connect(self._on_combo_speech_provider_changed)
        speech_layout.addWidget(QLabel(loc.translate("lbl_tts_provider")))
        speech_layout.addWidget(self.tts_provider_combo)
        
        self.speech_stacked_widget = QStackedWidget()
        speech_layout.addWidget(self.speech_stacked_widget)
        
        # voice mode
        voice_mode_group = QGroupBox(loc.translate("group_voice_mode"))
        voice_mode_layout = QVBoxLayout()
        self.mode_single_voice = QCheckBox(loc.translate("chk_single_voice"))
        self.mode_multi_voice = QCheckBox(loc.translate("chk_multi_voice"))
        self.mode_single_voice.toggled.connect(lambda checked: self.mode_multi_voice.setChecked(not checked) if checked else None)
        self.mode_multi_voice.toggled.connect(lambda checked: self.mode_single_voice.setChecked(not checked) if checked else None)
        voice_mode_layout.addWidget(self.mode_single_voice)
        voice_mode_layout.addWidget(self.mode_multi_voice)
        
        # single voice container
        self.single_voice_container = QWidget()
        self.single_voice_layout = QFormLayout(self.single_voice_container)
        self.global_voice_combo = QComboBox()
        self.single_voice_layout.addRow(loc.translate("lbl_select_voice_all"), self.global_voice_combo)
        self.single_voice_info_label = QLabel("<font color='gray'>This voice will be applied to all detected speakers.</font>")
        self.single_voice_layout.addRow(self.single_voice_info_label)
        self.single_voice_container.setVisible(True)
        voice_mode_layout.addWidget(self.single_voice_container)
        
        # speaker voices container
        self.speaker_voices_container = QWidget()
        self.speaker_voices_layout = QVBoxLayout(self.speaker_voices_container)
        self.speaker_voices_layout.setContentsMargins(0, 0, 0, 0)
        self.speaker_voices_container.setVisible(False)
        voice_mode_layout.addWidget(self.speaker_voices_container)
        
        voice_mode_group.setLayout(voice_mode_layout)
        speech_layout.addWidget(voice_mode_group)
        
        speech_group.setLayout(speech_layout)
        gen_form.addRow(speech_group)
        
        gen_scroll.setWidget(gen_content)
        gen_layout.addWidget(gen_scroll)
        self.tabs.addTab(self.tab_general, loc.translate("tab_general"))
        
        # ---------- tab advanced ----------
        self.tab_adv = QWidget()
        adv_layout = QVBoxLayout(self.tab_adv)
        adv_scroll = QScrollArea()
        adv_scroll.setWidgetResizable(True)
        adv_content = QWidget()
        adv_form = QFormLayout(adv_content)
        
        # output
        output_group = QGroupBox(loc.translate("group_output"))
        output_layout = QFormLayout()
        self.output_mode_combo = QComboBox()
        self.output_mode_combo.addItems(["video", "audio", "both"])
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["mp4", "avi", "mov", "mkv"])
        output_layout.addRow(loc.translate("lbl_output_mode"), self.output_mode_combo)
        output_layout.addRow(loc.translate("lbl_output_format"), self.output_format_combo)
        output_group.setLayout(output_layout)
        adv_form.addRow(output_group)
        
        # subtitle
        sub_group = QGroupBox(loc.translate("group_subtitle"))
        sub_layout = QFormLayout()
        self.subtitle_enabled = QCheckBox(loc.translate("chk_enable_subtitles"))
        sub_layout.addRow(self.subtitle_enabled)
        self.subtitle_style_combo = QComboBox()
        self.subtitle_style_combo.addItems(["classic", "modern", "minimal"])
        sub_layout.addRow(loc.translate("lbl_subtitle_style"), self.subtitle_style_combo)
        self.subtitle_fontsize = QSpinBox()
        self.subtitle_fontsize.setRange(8, 72)
        self.subtitle_fontsize.setValue(24)
        sub_layout.addRow(loc.translate("lbl_subtitle_fontsize"), self.subtitle_fontsize)
        sub_group.setLayout(sub_layout)
        adv_form.addRow(sub_group)
        
        # background music
        music_group = QGroupBox(loc.translate("group_background_music"))
        music_layout = QFormLayout()
        self.bg_music_enabled = QCheckBox(loc.translate("chk_enable_bg_music"))
        music_layout.addRow(self.bg_music_enabled)
        self.bg_music_volume = QSlider(Qt.Horizontal)
        self.bg_music_volume.setRange(0, 100)
        self.bg_music_volume.setValue(30)
        music_layout.addRow(loc.translate("lbl_bg_music_volume"), self.bg_music_volume)
        music_group.setLayout(music_layout)
        adv_form.addRow(music_group)
        
        adv_scroll.setWidget(adv_content)
        adv_layout.addWidget(adv_scroll)
        self.tabs.addTab(self.tab_adv, loc.translate("tab_advanced"))
        
        # ---------- bottom buttons ----------
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton(loc.translate("btn_save_settings"))
        self.save_btn.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 8px;")
        self.save_btn.clicked.connect(self.save_settings)
        
        self.cancel_btn = QPushButton(loc.translate("btn_cancel"))
        self.cancel_btn.clicked.connect(self.close)
        
        self.save_status_label = QLabel("")
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_status_label)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(btn_layout)
        
        # connect signals
        self.mode_single_voice.toggled.connect(self._on_voice_mode_changed)
        self.mode_multi_voice.toggled.connect(self._on_voice_mode_changed)
        
    def _on_voice_mode_changed(self):
        single = self.mode_single_voice.isChecked()
        self.single_voice_container.setVisible(single)
        self.speaker_voices_container.setVisible(not single)
        
    def init_translation_widgets(self):
        from frontend.ui.settings.translation_widgets import (
            ChatAnywhereSettingsWidget,
            DeepLSettingsWidget,
        )
        self.trans_widgets = {}
        
        chatanywhere_widget = ChatAnywhereSettingsWidget()
        chatanywhere_widget.test_requested.connect(lambda: self._test_translation_provider("chatanywhere", chatanywhere_widget))
        self.trans_widgets["chatanywhere"] = chatanywhere_widget
        self.trans_stack.addWidget(chatanywhere_widget)
        
        deepl_widget = DeepLSettingsWidget()
        deepl_widget.test_requested.connect(lambda: self._test_translation_provider("deepl", deepl_widget))
        self.trans_widgets["deepl"] = deepl_widget
        self.trans_stack.addWidget(deepl_widget)
        
        
        self.provider_combo.clear()
        self.provider_combo.addItems(["ChatAnywhere", "DeepL"])
        self.provider_combo.currentTextChanged.connect(self._on_combo_provider_changed)
        
    def init_speech_widgets(self):
        from frontend.ui.settings.speech_widgets import (
            ElevenLabsSettingsWidget,
            EdgeTTSSettingsWidget,
        )
        
        self.speech_widgets = {}
        
        # ElevenLabs
        self.elevenlabs_widget = ElevenLabsSettingsWidget(loc)
        self.speech_widgets["elevenlabs"] = self.elevenlabs_widget
        self.speech_stacked_widget.addWidget(self.elevenlabs_widget)
        
        self.elevenlabs_widget.test_requested.connect(lambda: self._test_speech_provider("elevenlabs", self.elevenlabs_widget))
        self.elevenlabs_widget.refresh_voices_requested.connect(lambda: self._refresh_speech_voices("elevenlabs", self.elevenlabs_widget))
        self.elevenlabs_widget.preview_requested.connect(lambda t, m, v, l, s, p: self._preview_speech("elevenlabs", self.elevenlabs_widget, t, m, v, l, s, p))
        
        # Edge TTS - dedicated widget, no shared UI
        self.edge_widget = EdgeTTSSettingsWidget(loc)
        self.speech_widgets["edge"] = self.edge_widget
        self.speech_stacked_widget.addWidget(self.edge_widget)
        
        self.edge_widget.test_audio_requested.connect(lambda: self._test_edge_audio())
        
        # set default widget
        self.speech_stacked_widget.setCurrentWidget(self.elevenlabs_widget)
        
    def _on_combo_provider_changed(self, provider_name: str):
        self._state.translation_provider = provider_name.lower()
        
    def _on_state_provider_changed(self, provider_name: str):
        provider_name = provider_name.lower()
        matched_key = None
        for key in self.trans_widgets:
            if key.lower() == provider_name:
                matched_key = key
                break
        if matched_key:
            self.trans_stack.setCurrentWidget(self.trans_widgets[matched_key])
        
        self.provider_combo.blockSignals(True)
        for idx in range(self.provider_combo.count()):
            if self.provider_combo.itemText(idx).lower() == provider_name:
                self.provider_combo.setCurrentIndex(idx)
                break
        self.provider_combo.blockSignals(False)
        
    def _on_combo_speech_provider_changed(self, text: str):
        mapping = {
            "ElevenLabs": "elevenlabs",
            "Edge TTS": "edge"
        }
        provider_id = mapping.get(text, "edge")
        self._state.speech_provider = provider_id
        
        # Switch stacked widget and sync global_voice_combo
        if provider_id in self.speech_widgets:
            widget = self.speech_widgets[provider_id]
            self.speech_stacked_widget.setCurrentWidget(widget)
            if hasattr(widget, 'voice_combo') and widget.voice_combo.count() > 0:
                self._sync_global_voice_combo(widget)
        
    def _on_state_speech_provider_changed(self, provider_id: str):
        provider_id = provider_id.lower()
        if provider_id in self.speech_widgets:
            self.speech_stacked_widget.setCurrentWidget(self.speech_widgets[provider_id])
            
        mapping = {
            "elevenlabs": "ElevenLabs",
            "edge": "Edge TTS"
        }
        target_text = mapping.get(provider_id, "Edge TTS")
        
        self.tts_provider_combo.blockSignals(True)
        idx = self.tts_provider_combo.findText(target_text)
        if idx != -1:
            self.tts_provider_combo.setCurrentIndex(idx)
        self.tts_provider_combo.blockSignals(False)
        
        self.update_tts_ui_state()
        
    def update_tts_ui_state(self):
        pass
        
    def load_settings(self):
        settings_path = os.path.abspath(
            os.path.join("config", "settings.json")
        )
        
        print("=" * 80)
        print("[LOAD SETTINGS]")
        print(f"  settings_path: {settings_path}")
        print("=" * 80 + "\n")
        
        if not os.path.exists(settings_path):
            print("[LOAD SETTINGS] settings.json not found, using defaults.")
            return
            
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[LOAD SETTINGS] Error loading settings: {e}")
            return
            
        print(f"[LOAD SETTINGS] Loaded keys: {list(data.keys())}")
        
        # output mode
        output_mode = data.get("output_mode", "video")
        idx = self.output_mode_combo.findText(output_mode)
        if idx != -1:
            self.output_mode_combo.setCurrentIndex(idx)
            
        output_format = data.get("output_format", "mp4")
        idx = self.output_format_combo.findText(output_format)
        if idx != -1:
            self.output_format_combo.setCurrentIndex(idx)
            
        # subtitle
        self.subtitle_enabled.setChecked(data.get("subtitle_enabled", False))
        subtitle_style = data.get("subtitle_style", "classic")
        idx = self.subtitle_style_combo.findText(subtitle_style)
        if idx != -1:
            self.subtitle_style_combo.setCurrentIndex(idx)
        self.subtitle_fontsize.setValue(data.get("subtitle_fontsize", 24))
        
        # background music
        self.bg_music_enabled.setChecked(data.get("bg_music_enabled", False))
        self.bg_music_volume.setValue(data.get("bg_music_volume", 30))
        
        # voice mode
        voice_mode = data.get("voice_mode", "SINGLE")
        if voice_mode == "SINGLE":
            self.mode_single_voice.setChecked(True)
        else:
            self.mode_multi_voice.setChecked(True)
            
        # speech provider
        speech_provider = data.get("speech_provider", "edge")
        self._on_state_speech_provider_changed(speech_provider)
        
        # load speech widget configs
        providers = data.get("providers", {})
        for pid, widget in self.trans_widgets.items():
            if pid in providers:
                try:
                    widget.load_config(providers)
                except Exception as e:
                    print(f"[LOAD SETTINGS] Error loading config for {pid}: {e}")

        for pid, widget in self.speech_widgets.items():
            if pid in providers:
                try:
                    widget.load_config(providers)
                except Exception as e:
                    print(f"[LOAD SETTINGS] Error loading config for {pid}: {e}")
                    
        # global voice
        global_voice = data.get("global_voice", "")
        print(f"[LOAD SETTINGS] global_voice from settings: '{global_voice}'")
        if global_voice:
            g_idx = self.global_voice_combo.findData(global_voice)
            if g_idx != -1:
                self.global_voice_combo.setCurrentIndex(g_idx)
            else:
                self.global_voice_combo.addItem(global_voice, global_voice)
                self.global_voice_combo.setCurrentIndex(self.global_voice_combo.count() - 1)
        else:
            if self.global_voice_combo.count() > 0:
                self.global_voice_combo.setCurrentIndex(0)
                
        print("[LOAD SETTINGS] Done.\n")
        
    def save_settings(self):
        settings_path = os.path.abspath(
            os.path.join("config", "settings.json")
        )
        
        print("=" * 80)
        print("[SAVE SETTINGS]")
        print(f"  settings_path: {settings_path}")
        print("=" * 80 + "\n")
        
        # load existing
        data = {}
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                pass
                
        # gather speaker voices
        speaker_voices = {}
        
        # build settings
        data["output_mode"] = self.output_mode_combo.currentText()
        data["output_format"] = self.output_format_combo.currentText()
        data["subtitle_enabled"] = self.subtitle_enabled.isChecked()
        data["subtitle_style"] = self.subtitle_style_combo.currentText()
        data["subtitle_fontsize"] = self.subtitle_fontsize.value()
        data["bg_music_enabled"] = self.bg_music_enabled.isChecked()
        data["bg_music_volume"] = self.bg_music_volume.value()
        data["voice_mode"] = "SINGLE" if self.mode_single_voice.isChecked() else "MULTI"
        data["global_voice"] = self.global_voice_combo.currentData() or ""
        data["speaker_voices"] = speaker_voices
        data["speech_provider"] = self._state.speech_provider
        
        # save widget configs
        providers = data.get("providers", {})
        for pid, widget in self.trans_widgets.items():
            try:
                providers[pid] = widget.save_config()
            except Exception as e:
                print(f"[SAVE SETTINGS] Error saving config for {pid}: {e}")

        for pid, widget in self.speech_widgets.items():
            try:
                providers[pid] = widget.save_config()
            except Exception as e:
                print(f"[SAVE SETTINGS] Error saving config for {pid}: {e}")
        data["providers"] = providers
        
        # ensure directory exists
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[SAVE SETTINGS] Saved successfully.")
            self.save_status_label.setText("Settings saved.")
            self.settings_saved.emit(data)
        except Exception as e:
            print(f"[SAVE SETTINGS] Error saving: {e}")
            self.save_status_label.setText(f"Error: {e}")
            
    def repopulate_speaker_voices(self):
        pass

    def _test_translation_provider(self, provider_id: str, widget):
        pid_lower = provider_id.lower()
        config = widget.save_config() if hasattr(widget, 'save_config') else {}
        if not config:
            config = {"api_key": getattr(widget, 'api_key', '')}
            
        # Wrap config in nested {provider_id: {config}} format expected by the manager
        self._trans_svc.create_provider(pid_lower, {pid_lower: config})
        
        from frontend.ui.settings_window import ServiceConnectionWorker
        self._tw_worker = ServiceConnectionWorker(self._trans_svc, pid_lower)
        self._tw_worker.finished.connect(lambda res: self._on_translation_test_finished(widget, res))
        self._tw_worker.start()

    def _on_translation_test_finished(self, widget, result: dict):
        widget._on_test_finished(result)
        models = result.get("models", [])
        if models:
            widget._on_refresh_models_finished({"success": True, "models": models})
        
    def _test_speech_provider(self, provider_id: str, widget):
        pid_lower = provider_id.lower()
        config = {}
        if pid_lower == "elevenlabs":
            config = {"elevenlabs": {"api_key": widget.api_key_edit.text(), "model": widget.model_combo.currentText()}}
        else:
            config = {}
        self._speech_svc.create_provider(pid_lower, config)
        
        resolved_pid = pid_lower
        manager_instance = getattr(self._speech_svc, '_provider_manager', None)
        
        print("=" * 40 + " TEST SPEECH " + "=" * 40)
        print(f"  ProviderManager.get(provider_id): {manager_instance.__class__.__name__ if manager_instance else 'None'}")
        print(f"  Resolved Provider ID:             {resolved_pid}")
        print("=" * 88 + "\n")
        
        from frontend.ui.settings_window import ServiceConnectionWorker
        self._sw_worker = ServiceConnectionWorker(self._speech_svc, pid_lower)
        self._sw_worker.finished.connect(lambda res: widget._on_test_finished(res))
        self._sw_worker.start()
        
    def _refresh_speech_models(self, provider_id: str, widget):
        pid_lower = provider_id.lower()
        config = {}
        self._speech_svc.create_provider(pid_lower, config)
        from frontend.ui.settings_window import ServiceRefreshWorker
        self._sm_worker = ServiceRefreshWorker(self._speech_svc, pid_lower, "models")
        self._sm_worker.finished.connect(lambda res: widget._on_refresh_models_finished(res))
        self._sm_worker.start()
        
    def _refresh_speech_voices(self, provider_id: str, widget):
        pid_lower = provider_id.lower()
        config = {}
        if pid_lower == "elevenlabs":
            config = {"elevenlabs": {"api_key": widget.api_key_edit.text(), "model": widget.model_combo.currentText()}}
        else:
            config = {}
        self._speech_svc.create_provider(pid_lower, config)
        from frontend.ui.settings_window import ServiceRefreshWorker
        self._sv_worker = ServiceRefreshWorker(self._speech_svc, pid_lower, "voices")
        self._sv_worker.finished.connect(lambda res: self._on_voices_refreshed(res, widget, pid_lower))
        self._sv_worker.start()
        
    def _sync_global_voice_combo(self, widget):
        """Copy voice items from widget.voice_combo to global_voice_combo."""
        prev_voice = self.global_voice_combo.currentData()
        self.global_voice_combo.blockSignals(True)
        self.global_voice_combo.clear()
        selected_index = -1
        for i in range(widget.voice_combo.count()):
            text = widget.voice_combo.itemText(i)
            data = widget.voice_combo.itemData(i)
            self.global_voice_combo.addItem(text, data)
            if prev_voice and data == prev_voice:
                selected_index = i
        if selected_index != -1:
            self.global_voice_combo.setCurrentIndex(selected_index)
        elif self.global_voice_combo.count() > 0:
            self.global_voice_combo.setCurrentIndex(0)
        self.global_voice_combo.blockSignals(False)
        
    def _on_voices_refreshed(self, result, widget, provider_id):
        print(f"\n[ON VOICES REFRESHED] provider_id={provider_id}")
        voices = result.get("data", []) if result.get("success") or result.get("status") == "Success" else []
        print(f"[ON VOICES REFRESHED] result keys={list(result.keys())}")
        print(f"[ON VOICES REFRESHED] voices count={len(voices)}")
        if voices:
            print(f"[ON VOICES REFRESHED] first voice sample={voices[0]}")
        widget._on_refresh_voices_finished(voices)
        
        # Sync global_voice_combo with the widget's voice_combo
        if hasattr(widget, 'voice_combo'):
            self._sync_global_voice_combo(widget)
            print(f"[ON VOICES REFRESHED] global_voice_combo now has {self.global_voice_combo.count()} items")
            print(f"[ON VOICES REFRESHED] global_voice_combo current data: {self.global_voice_combo.currentData()}")
        
    def _preview_speech(self, provider_id: str, widget, text, model, voice, lang, speed, pitch):
        pid_lower = provider_id.lower()
        config = {}
        if pid_lower == "elevenlabs":
            config = {"elevenlabs": {"api_key": widget.api_key_edit.text(), "model": widget.model_combo.currentText()}}
        else:
            config = {}
        self._speech_svc.create_provider(pid_lower, config)
        
        req = {
            "text": text,
            "voice_name": voice,
            "emotion_profile": {
                "model": model,
                "language": lang,
                "speed": speed,
                "pitch": pitch
            }
        }
        
        from frontend.ui.settings_window import ServicePreviewWorker
        self._sp_worker = ServicePreviewWorker(self._speech_svc, pid_lower, req)
        self._sp_worker.finished.connect(lambda audio, v: widget._on_preview_finished(audio))
        self._sp_worker.error.connect(lambda err: widget._on_preview_error(err))
        self._sp_worker.start()
        
    def _test_edge_audio(self):
        """Generate and play a test audio using the Edge TTS provider."""
        widget = self.edge_widget
        voice_id = widget.get_selected_voice_id()
        if not voice_id:
            widget._on_test_audio_error("No voice selected.")
            return
            
        # Create the provider with no config needed (Edge TTS is free/no-key)
        pid_lower = "edge"
        self._speech_svc.create_provider(pid_lower, {})
        
        rate = widget.get_rate()
        pitch = widget.get_pitch()
        volume = widget.get_volume()
        
        # Map rate/pitch to edge-tts parameters (rate=+/-50%, pitch=+/-50Hz)
        rate_str = f"{rate:+d}%"
        pitch_str = f"{pitch:+d}Hz"
        
        req = {
            "text": "This is a test audio from Edge TTS.",
            "voice_name": voice_id,
            "rate": rate_str,
            "pitch": pitch_str,
            "volume": volume
        }
        
        print(f"\n[EDGE TTS TEST] voice={voice_id} rate={rate_str} pitch={pitch_str} volume={volume}%\n")
        
        from frontend.ui.settings_window import ServicePreviewWorker
        self._edge_audio_worker = ServicePreviewWorker(self._speech_svc, pid_lower, req)
        self._edge_audio_worker.finished.connect(lambda audio, v: widget._on_test_audio_finished(audio))
        self._edge_audio_worker.error.connect(lambda err: widget._on_test_audio_error(err))
        self._edge_audio_worker.start()
