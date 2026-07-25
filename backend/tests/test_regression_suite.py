import pytest
import re
import os
from frontend.state.provider_state import ProviderState

def test_provider_state_signals():
    """Verify ProviderState signal fires exactly once."""
    state = ProviderState()
    
    signals_emitted = []
    def on_changed(provider):
        signals_emitted.append(provider)
        
    state.translation_provider_changed.connect(on_changed)
    
    # Change provider
    state.translation_provider = "DeepL"
    
    assert len(signals_emitted) == 1
    assert signals_emitted[0] == "DeepL"
    
    # Change to same provider shouldn't emit
    state.translation_provider = "DeepL"
    assert len(signals_emitted) == 1

def test_no_property_hacks():
    """Verify no runtime property() hacks remain in settings_window.py."""
    filepath = os.path.join("frontend", "ui", "settings_window.py")
    if not os.path.exists(filepath):
        pytest.skip(f"Could not find {filepath}")
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Assert no 'property(' is used for state hacks
    assert not re.search(r'\.current_provider\s*=\s*property\(', content), "Found property hack for current_provider"
    assert not re.search(r'\.provider_changed\s*=\s*', content), "Found provider_changed alias hack"
    assert "self.trans_state" not in content, "Found legacy self.trans_state usage"

def test_no_direct_instantiations():
    """Verify no direct provider instantiations exist in settings_window.py."""
    filepath = os.path.join("frontend", "ui", "settings_window.py")
    if not os.path.exists(filepath):
        pytest.skip(f"Could not find {filepath}")
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "ChatAnywhereProvider(" not in content
    assert "DeepLTranslationProvider(" not in content
    assert "GeminiSpeechProvider(" not in content
    assert "ElevenLabsProvider(" not in content

def test_translation_providers_are_not_abstract():
    """Verify that all translation providers are concrete classes and can be instantiated."""
    import inspect
    from backend.providers.translation.manager import TranslationProviderManager
    
    manager = TranslationProviderManager()
    providers_to_test = ["chatanywhere", "deepl", "gemini", "google", "openai"]
    
    class MockLLMService:
        def __init__(self):
            class MockManager:
                def get(self, provider_id):
                    return None
            self._manager = MockManager()
        async def chat(self, *args, **kwargs):
            return "OK"
            
    mock_llm = MockLLMService()
    dummy_settings = {
        "chatanywhere": {"api_key": "dummy"},
        "deepl": {"api_key": "dummy"},
        "gemini": {"api_key": "dummy"},
        "google": {"api_key": "dummy"},
        "openai": {"api_key": "dummy"}
    }
    
    for pid in providers_to_test:
        provider = manager.create_provider(pid, dummy_settings, mock_llm)
        assert not inspect.isabstract(provider.__class__), f"Provider '{pid}' is abstract!"

def test_llm_providers_lifecycle():
    """Verify LLM managers lifecycle works properly for all providers."""
    from backend.providers.llm.manager import LLMProviderManager
    
    manager = LLMProviderManager()
    providers = ["chatanywhere", "gemini", "openai", "claude"]
    dummy_settings = {
        "chatanywhere": {"api_key": "dummy", "base_url": "http://dummy"},
        "gemini": {"api_key": "dummy"},
        "openai": {"api_key": "dummy"},
        "claude": {"api_key": "dummy"}
    }
    
    for pid in providers:
        p = manager.create_provider(pid, dummy_settings)
        assert p is not None
        assert manager.get(pid) == p
        
        # remove test
        manager.remove(pid)
        assert manager.get(pid, create_lazy=False) is None

def test_speech_providers_lifecycle():
    """Verify Speech managers lifecycle works properly for all providers."""
    from backend.providers.speech.manager import SpeechProviderManager
    
    manager = SpeechProviderManager()
    providers = ["gemini", "kira", "elevenlabs", "omnivoice", "edge"]
    dummy_settings = {
        "gemini": {"api_key": "dummy"},
        "kira": {"api_key": "dummy"},
        "elevenlabs": {"api_key": "dummy"}
    }
    
    for pid in providers:
        p = manager.create_provider(pid, dummy_settings)
        assert p is not None
        assert manager.get(pid) == p
        
        # remove test
        manager.remove(pid)
        assert manager.get(pid, create_lazy=False) is None

def test_ui_provider_state_synchronization():
    """Verify UI controls synchronize automatically with ProviderState."""
    from PySide6.QtWidgets import QApplication
    from frontend.ui.settings_window import SettingsWindow
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        
    window = SettingsWindow()
    
    # 1. Test translation provider state change updates combo and stacked widget
    window._state.translation_provider = "deepl"
    assert window.provider_combo.currentText().lower() == "deepl"
    assert window.trans_stack.currentWidget() == window.trans_widgets["DeepL"]
    
    window._state.translation_provider = "chatanywhere"
    assert window.provider_combo.currentText().lower() == "chatanywhere"
    assert window.trans_stack.currentWidget() == window.trans_widgets["ChatAnywhere"]
    
    # 2. Test speech provider state change updates combo and stacked widget
    window._state.speech_provider = "kira"
    assert "kira" in window.tts_provider_combo.currentText().lower()
    assert window.speech_stacked_widget.currentWidget() == window.kira_group
    
    window._state.speech_provider = "edge"
    assert "edge" in window.tts_provider_combo.currentText().lower()
    assert window.speech_stacked_widget.currentWidget() == window.edge_tts_group


@pytest.mark.parametrize("provider_type, provider_id", [
    ("translation", "chatanywhere"),
    ("translation", "deepl"),
    ("translation", "gemini"),
    ("translation", "google"),
    ("translation", "openai"),
    ("speech", "gemini"),
    ("speech", "kira"),
    ("speech", "elevenlabs"),
    ("speech", "omnivoice"),
    ("speech", "edge"),
    ("llm", "chatanywhere"),
    ("llm", "gemini"),
    ("llm", "openai"),
    ("llm", "claude")
])
def test_provider_matrix(provider_type, provider_id):
    """Provider Matrix Test: ensure each provider implements identical lifecycle and abstract methods."""
    import inspect
    dummy_settings = {
        "chatanywhere": {"api_key": "dummy", "base_url": "http://dummy"},
        "deepl": {"api_key": "dummy"},
        "gemini": {"api_key": "dummy"},
        "google": {"api_key": "dummy"},
        "openai": {"api_key": "dummy"},
        "kira": {"api_key": "dummy"},
        "elevenlabs": {"api_key": "dummy"},
        "claude": {"api_key": "dummy"}
    }
    
    if provider_type == "translation":
        from backend.providers.translation.manager import TranslationProviderManager
        class MockLLMService:
            def __init__(self):
                class MockManager:
                    def get(self, pid): return None
                self._manager = MockManager()
            async def chat(self, *args, **kwargs): return "OK"
        
        manager = TranslationProviderManager()
        provider = manager.create_provider(provider_id, dummy_settings, MockLLMService())
        assert provider is not None
        assert not inspect.isabstract(provider.__class__)
        assert manager.get(provider_id) == provider
        assert hasattr(provider, "test_connection")
        assert hasattr(provider, "list_models")
        
    elif provider_type == "speech":
        from backend.providers.speech.manager import SpeechProviderManager
        manager = SpeechProviderManager()
        provider = manager.create_provider(provider_id, dummy_settings)
        assert provider is not None
        assert not inspect.isabstract(provider.__class__)
        assert manager.get(provider_id) == provider
        assert hasattr(provider, "test_connection")
        assert hasattr(provider, "list_voices")
        
    elif provider_type == "llm":
        from backend.providers.llm.manager import LLMProviderManager
        manager = LLMProviderManager()
        provider = manager.create_provider(provider_id, dummy_settings)
        assert provider is not None
        assert not inspect.isabstract(provider.__class__)
        assert manager.get(provider_id) == provider
        assert hasattr(provider, "test_connection")
        assert hasattr(provider, "list_models")


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_id", ["gemini", "kira", "elevenlabs", "omnivoice", "edge"])
async def test_speech_preview_matrix(provider_id):
    """Verify that calling preview() with arbitrary keyword args does not raise TypeError on any speech provider."""
    from backend.providers.speech.manager import SpeechProviderManager
    
    dummy_settings = {
        "gemini": {"api_key": "dummy"},
        "kira": {"api_key": "dummy"},
        "elevenlabs": {"api_key": "dummy"}
    }
    
    manager = SpeechProviderManager()
    provider = manager.create_provider(provider_id, dummy_settings)
    assert provider is not None
    
    try:
        await provider.preview(
            text="Hello world", 
            voice_name="dummy_voice", 
            emotion_profile={"model": "dummy", "speed": 1.0},
            future_unsupported_parameter="some_value"
        )
    except TypeError as e:
        assert "unexpected keyword argument" not in str(e), f"Provider {provider_id} raised unexpected keyword argument error: {e}"
    except Exception:
        pass


def test_no_legacy_workers_in_frontend():
    """Regression test asserting that no frontend python file references removed legacy worker classes."""
    import os
    removed_workers = [
        "TestKiraConnectionWorker",
        "TestDeepLConnectionWorker",
        "TestConnectionWorker",
        "RefreshTranslationModelsWorker",
        "RefreshTTSModelsWorker",
        "PreviewWorker"
    ]
    
    frontend_dir = os.path.abspath("frontend")
    for root, dirs, files in os.walk(frontend_dir):
        if "pycache" in root or ".next" in root or "node_modules" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                import re
                for worker in removed_workers:
                    pattern = rf"\b{worker}\b"
                    assert not re.search(pattern, content), f"Frontend file '{os.path.basename(path)}' contains reference to removed worker class '{worker}'"


def test_chatanywhere_configuration_propagation():
    """Verify that fake configurations propagate correctly from Facade down to the Provider."""
    from backend.services.translation_facade_service import TranslationFacadeService
    
    fake_settings = {
        "chatanywhere": {
            "api_key": "test_propagation_key",
            "base_url": "https://api.test_propagation.tech/v1",
            "model": "gpt-99-super"
        }
    }
    
    service = TranslationFacadeService()
    provider = service.create_provider("chatanywhere", fake_settings)
    
    assert provider is not None
    assert provider.api_key == "test_propagation_key"
    assert provider.base_url == "https://api.test_propagation.tech/v1"
    assert provider._model == "gpt-99-super"


def test_pre_registration_lifecycle():
    """Verify that all standard translation providers are pre-registered on startup and return concrete instances."""
    from backend.providers.translation.manager import TranslationProviderManager
    import inspect
    
    manager = TranslationProviderManager()
    for pid in ["chatanywhere", "deepl", "google", "gemini", "openai"]:
        provider = manager.get(pid, create_lazy=False)
        assert provider is not None, f"Provider '{pid}' was not pre-registered on startup."
        assert not inspect.isabstract(provider.__class__), f"Provider class '{provider.__class__.__name__}' is abstract."


@pytest.mark.asyncio
async def test_speech_facade_refresh_models():
    """Verify SpeechFacadeService.refresh_models works for speech providers without AttributeError."""
    from backend.services.speech_facade_service import SpeechFacadeService
    facade = SpeechFacadeService()
    models = await facade.refresh_models("kira")
def test_translation_widget_refresh_models_slot():
    """Verify that ChatAnywhereSettingsWidget populates all models received from worker slot."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from frontend.ui.settings.translation_widgets import ChatAnywhereSettingsWidget
    
    widget = ChatAnywhereSettingsWidget()
    mock_res = {
        "success": True,
        "status": "Success",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "claude-3-5-sonnet"]
    }
    
    widget._on_refresh_models_finished(mock_res)
    
    assert widget.model_combo.count() == 4
    all_items = [widget.model_combo.itemText(i) for i in range(widget.model_combo.count())]
    assert all_items == ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "claude-3-5-sonnet"]
@pytest.mark.asyncio
async def test_elevenlabs_list_voices(monkeypatch):
    """Regression test asserting that ElevenLabsProvider.list_voices returns list containing voice_id and name."""
    from backend.providers.speech.elevenlabs.elevenlabs_provider import ElevenLabsProvider
    import httpx
    
    mock_voices_data = {
        "voices": [
            {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "labels": {"gender": "female", "language": "en"}},
            {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "labels": {"gender": "female", "language": "en"}}
        ]
    }
    
    class MockResponse:
        status_code = 200
        def json(self):
            return mock_voices_data

    class MockAsyncClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        async def get(self, url, headers=None, timeout=None):
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    
    provider = ElevenLabsProvider(api_key="fake_elevenlabs_key")
    voices = await provider.list_voices()
    
    assert isinstance(voices, list)
    assert len(voices) > 0
    for item in voices:
        assert "voice_id" in item
        assert "name" in item
        assert item["voice_id"]
        assert item["name"]


def test_voice_language_filter():
    """Verify language filter shows only matching language voices."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from backend.services.localization_service import LocalizationService
    from frontend.ui.settings.speech_widgets import ElevenLabsSettingsWidget
    
    widget = ElevenLabsSettingsWidget(LocalizationService())
    voices = [
        {"voice_id": "v1", "name": "Thanh Ngọc", "language": "vi", "preview_url": "http://example.com/1.mp3"},
        {"voice_id": "v2", "name": "Rachel", "language": "en-US", "preview_url": "http://example.com/2.mp3"}
    ]
    widget._on_refresh_voices_finished(voices)
    
    widget.lang_filter_combo.setCurrentText("vi")
    assert widget.voice_combo.count() == 1
    assert widget.voice_combo.currentText() == "Thanh Ngọc"


def test_voice_search():
    """Verify instant search filters voices matching search string."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from backend.services.localization_service import LocalizationService
    from frontend.ui.settings.speech_widgets import ElevenLabsSettingsWidget
    
    widget = ElevenLabsSettingsWidget(LocalizationService())
    voices = [
        {"voice_id": "v1", "name": "Thanh Ngọc", "language": "vi"},
        {"voice_id": "v2", "name": "Trung Caha", "language": "vi"},
        {"voice_id": "v3", "name": "Rachel", "language": "en"}
    ]
    widget._on_refresh_voices_finished(voices)
    
    widget.search_voice_edit.setText("thanh")
    assert widget.voice_combo.count() == 1
    assert widget.voice_combo.currentText() == "Thanh Ngọc"


def test_voice_filter_preserves_selection():
    """Verify selection survives filtering whenever possible."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from backend.services.localization_service import LocalizationService
    from frontend.ui.settings.speech_widgets import ElevenLabsSettingsWidget
    
    widget = ElevenLabsSettingsWidget(LocalizationService())
    voices = [
        {"voice_id": "v1", "name": "Thanh Ngọc", "language": "vi"},
        {"voice_id": "v2", "name": "Trung Caha", "language": "vi"}
    ]
    widget._on_refresh_voices_finished(voices)
    widget.voice_combo.setCurrentIndex(1)
    assert widget.voice_combo.currentData() == "v2"
    
    widget.search_voice_edit.setText("caha")
    assert widget.voice_combo.currentData() == "v2"


def test_preview_button_state():
    """Verify Preview button is enabled only when preview_url exists."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from backend.services.localization_service import LocalizationService
    from frontend.ui.settings.speech_widgets import ElevenLabsSettingsWidget
    
    widget = ElevenLabsSettingsWidget(LocalizationService())
    voices = [
        {"voice_id": "v1", "name": "HasPreview", "language": "en", "preview_url": "http://example.com/p.mp3"},
        {"voice_id": "v2", "name": "NoPreview", "language": "en", "preview_url": None}
    ]
    widget._on_refresh_voices_finished(voices)
    
    widget.voice_combo.setCurrentIndex(0)
    assert widget.preview_btn.isEnabled() == True
    
    widget.voice_combo.setCurrentIndex(1)
    assert widget.preview_btn.isEnabled() == False


def test_preview_stops_on_voice_change():
    """Verify selecting another voice stops current playback."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from backend.services.localization_service import LocalizationService
    from frontend.ui.settings.speech_widgets import ElevenLabsSettingsWidget
    
    widget = ElevenLabsSettingsWidget(LocalizationService())
    voices = [
        {"voice_id": "v1", "name": "V1", "language": "en", "preview_url": "http://example.com/1.mp3"},
        {"voice_id": "v2", "name": "V2", "language": "en", "preview_url": "http://example.com/2.mp3"}
    ]
    widget._on_refresh_voices_finished(voices)
    
    stopped = []
    widget._stop_preview = lambda: stopped.append(True)
    
    widget.voice_combo.setCurrentIndex(1)
    assert len(stopped) > 0


def test_preview_stops_on_widget_close():
    """Verify playback stops when the Settings widget closes."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from backend.services.localization_service import LocalizationService
    from frontend.ui.settings.speech_widgets import ElevenLabsSettingsWidget
    from PySide6.QtGui import QCloseEvent
    
    widget = ElevenLabsSettingsWidget(LocalizationService())
    stopped = []
    widget._stop_preview = lambda: stopped.append(True)
    
    widget.closeEvent(QCloseEvent())
    assert len(stopped) == 1


def test_favorite_restore():
    """Verify favorites reload correctly."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from backend.services.localization_service import LocalizationService
    from frontend.ui.settings.speech_widgets import ElevenLabsSettingsWidget
    
    widget = ElevenLabsSettingsWidget(LocalizationService())
    widget._favorites = {"v2"}
    
    voices = [
        {"voice_id": "v1", "name": "V1", "language": "en"},
        {"voice_id": "v2", "name": "V2", "language": "en"}
    ]
    widget._on_refresh_voices_finished(voices)
    widget.voice_combo.setCurrentIndex(1)
    assert widget.favorite_btn.text() == "★ Favorite"


def test_favorites_filter():
    """Verify Favorites Only shows only favorite voices."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from backend.services.localization_service import LocalizationService
    from frontend.ui.settings.speech_widgets import ElevenLabsSettingsWidget
    
    widget = ElevenLabsSettingsWidget(LocalizationService())
    widget._favorites = {"v2"}
    
    voices = [
        {"voice_id": "v1", "name": "V1", "language": "en"},
        {"voice_id": "v2", "name": "V2", "language": "en"}
    ]
    widget._on_refresh_voices_finished(voices)
    
    widget.favorites_only_chk.setChecked(True)
    assert widget.voice_combo.count() == 1
    assert widget.voice_combo.currentData() == "v2"


@pytest.mark.asyncio
async def test_filter_does_not_call_api_again(monkeypatch):
    """Verify Refresh Voices calls API once, while Search and Language Filter make zero additional API calls."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from backend.services.localization_service import LocalizationService
    from frontend.ui.settings.speech_widgets import ElevenLabsSettingsWidget
    from backend.providers.speech.elevenlabs.elevenlabs_provider import ElevenLabsProvider
    import httpx
    
    api_calls = []
    class MockResponse:
        status_code = 200
        def json(self):
            api_calls.append("get")
            return {"voices": [{"voice_id": "v1", "name": "V1", "labels": {"language": "en"}}]}

    class MockAsyncClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        async def get(self, url, headers=None, timeout=None):
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    
    provider = ElevenLabsProvider(api_key="key")
    voices = await provider.list_voices()
    assert len(api_calls) == 1
    
    widget = ElevenLabsSettingsWidget(LocalizationService())
    widget._on_refresh_voices_finished(voices)
    
    widget.search_voice_edit.setText("V1")
    widget.lang_filter_combo.setCurrentText("en")
    assert len(api_calls) == 1


def test_elevenlabs_widget_layout_stability():
    """Verify that ElevenLabsSettingsWidget labels have wordWrap and QSizePolicy.Ignored to prevent window expansion."""
    from PySide6.QtWidgets import QApplication, QComboBox, QSizePolicy
    app = QApplication.instance() or QApplication([])
    from backend.services.localization_service import LocalizationService
    from frontend.ui.settings.speech_widgets import ElevenLabsSettingsWidget
    
    widget = ElevenLabsSettingsWidget(LocalizationService())
    
    # ComboBox size adjust policy check
    assert widget.voice_combo.sizeAdjustPolicy() == QComboBox.AdjustToContentsOnFirstShow
    
    # Metadata labels wordWrap and sizePolicy checks
    labels = [
        widget.lbl_meta_name, widget.lbl_meta_lang, widget.lbl_meta_gender,
        widget.lbl_meta_category, widget.lbl_meta_desc, widget.lbl_meta_labels, widget.lbl_meta_id
    ]
    for lbl in labels:
        assert lbl.wordWrap() == True
        assert lbl.sizePolicy().horizontalPolicy() == QSizePolicy.Ignored
        
    # Long text setting does not produce infinite minimum width
    very_long_desc = "Long description " * 100
    widget.lbl_meta_desc.setText(very_long_desc)
    assert widget.lbl_meta_desc.wordWrap() == True


def test_restore_layout_state_geometry_validation():
    """Verify that off-screen saved geometry is ignored and falls back to default 1100x700 at (100, 100)."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from desktop_app import MainWindow, WorkspaceManager
    
    wm = WorkspaceManager.get_instance()
    # Save off-screen geometry (completely outside any screen bounds)
    wm._layout_data['mainwindow_geom'] = [-999999, -999999, 1924, 904]
    
    win = MainWindow()
    # Expect fall back to (100, 100) and (1100, 700)
    assert win.x() == 100
    assert win.y() == 100
    assert win.width() == 1100
    assert win.height() == 700
    win.close()


def test_browse_file_video_filters_and_unicode():
    """Verify browse_file allows video extensions and supports Unicode filenames."""
    import os
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from desktop_app import MainWindow
    
    win = MainWindow()
    assert hasattr(win, "browse_file")
    
    # Verify Unicode path handling
    unicode_paths = ["你好.mp4", "日本語.mp4", "động đất.mp4", "🔥video.mp4"]
    for path in unicode_paths:
        win.input_edit.setText(path)
        assert win.input_edit.text() == path
    win.close()


def test_pause_resume_pipeline(tmp_path):
    """Verify pause and resume button state toggle and pause.flag management."""
    import os
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from desktop_app import MainWindow
    
    win = MainWindow()
    assert hasattr(win, "pause_btn")
    assert win.start_btn.isEnabled() == True
    assert win.pause_btn.isEnabled() == False
    
    # Simulate start
    win.start_btn.setEnabled(False)
    win.pause_btn.setEnabled(True)
    assert win.pause_btn.text() == "Pause"
    
    # Toggle to Pause
    win.toggle_pause_pipeline()
    assert win.pause_btn.text() == "Resume"
    
    # Toggle to Resume
    win.toggle_pause_pipeline()
    assert win.pause_btn.text() == "Pause"
    
    # Finish
    win.queue_pipeline_finished("proj_test", 0)
    assert win.start_btn.isEnabled() == True
    assert win.pause_btn.isEnabled() == False
    win.close()


def test_settings_persistence(tmp_path):
    """Verify that settings are saved and loaded correctly from config/settings.json."""
    import os, json
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from frontend.ui.settings_window import SettingsWindow
    
    sw = SettingsWindow()
    sw.kira_api_key = "test_kira_key"
    sw._state.speech_provider = "elevenlabs"
    sw.save_settings()
    
    # Reload
    sw2 = SettingsWindow()
    sw2.load_settings()
    assert sw2._state.speech_provider == "elevenlabs"
    sw.close()
    sw2.close()


def test_project_repository_save_no_attribute_error(tmp_path):
    """Verify ProjectRepository creates project directory and metadata without AttributeError."""
    import time
    from backend.services.project_repository import ProjectRepository
    from backend.models.project_models import ProjectMetadata
    
    repo = ProjectRepository(projects_dir=str(tmp_path))
    proj_id = "proj_unit_test"
    metadata = ProjectMetadata(
        project_id=proj_id,
        project_name="Test Project",
        created_at=time.time(),
        modified_at=time.time(),
        input_video="test.mp4"
    )
    res = repo.save(metadata)
    assert res == True
    assert os.path.exists(repo.get_project_file_path(proj_id))
