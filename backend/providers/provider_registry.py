import os
import json
import logging
from typing import Dict, List, Optional
from backend.providers.metadata import ProviderMetadata
from backend.providers.capabilities import ProviderCapabilities, TranslationCapabilities, TTSCapabilities, SubtitleCapabilities

logger = logging.getLogger("ProviderRegistry")

class ProviderRegistry:
    """Manages dynamic loading, discovery, and registration of AI Providers."""
    
    def __init__(self):
        self._providers: Dict[str, ProviderMetadata] = {}
        self._enabled_providers: set[str] = set()
        
    def discover_providers(self, plugins_dir: str):
        """Scans the given directory for provider.json files and registers them."""
        if not os.path.exists(plugins_dir):
            return
            
        for root, dirs, files in os.walk(plugins_dir):
            if "provider.json" in files:
                json_path = os.path.join(root, "provider.json")
                self._load_from_json(json_path)

    def _load_from_json(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            caps_data = data.get("capabilities", {})
            
            # Map legacy or simple capabilities dictionary to structured capabilities
            translation_caps = TranslationCapabilities(**caps_data.get("translation", {})) if "translation" in caps_data else None
            tts_caps = TTSCapabilities(**caps_data.get("tts", {})) if "tts" in caps_data else None
            
            caps = ProviderCapabilities(
                supports_chat=caps_data.get("supports_chat", False),
                supports_audio_generation=caps_data.get("supports_audio_generation", False),
                translation=translation_caps,
                tts=tts_caps
            )
            
            metadata = ProviderMetadata(
                provider_id=data["id"],
                display_name=data.get("name", data["id"]),
                provider_type=data.get("type", "generic"),
                version=data.get("version", "1.0.0"),
                author=data.get("author", "Unknown"),
                homepage=data.get("homepage", ""),
                description=data.get("description", ""),
                capabilities=caps,
                models=data.get("models", []),
                voices=data.get("voices", []),
                limits=data.get("limits", {})
            )
            self.register(metadata)
        except Exception as e:
            logger.error(f"Failed to load provider metadata from {path}: {e}")

    def register(self, metadata: ProviderMetadata):
        """Registers a provider into the in-memory registry."""
        self._providers[metadata.provider_id] = metadata
        self._enabled_providers.add(metadata.provider_id)
        
    def enable_provider(self, provider_id: str):
        if provider_id in self._providers:
            self._enabled_providers.add(provider_id)
            
    def disable_provider(self, provider_id: str):
        if provider_id in self._enabled_providers:
            self._enabled_providers.remove(provider_id)
            
    def get_metadata(self, provider_id: str) -> Optional[ProviderMetadata]:
        return self._providers.get(provider_id)
        
    def list_providers(self, only_enabled: bool = True) -> List[ProviderMetadata]:
        if only_enabled:
            return [self._providers[pid] for pid in self._enabled_providers]
        return list(self._providers.values())

    def inject_legacy_providers(self):
        """Injects default metadata for hardcoded legacy providers (e.g. ChatAnywhere, EdgeTTS, DeepL)."""
        chatanywhere = ProviderMetadata(
            provider_id="ChatAnywhere",
            display_name="ChatAnywhere API",
            provider_type="translation",
            capabilities=ProviderCapabilities(
                supports_chat=True,
                translation=TranslationCapabilities(
                    context_translation=True,
                    translation_memory=True,
                    glossary=True,
                    batch_translation=True
                )
            )
        )
        self.register(chatanywhere)

        deepl = ProviderMetadata(
            provider_id="DeepL",
            display_name="DeepL Translator",
            provider_type="translation",
            capabilities=ProviderCapabilities(
                translation=TranslationCapabilities(
                    context_translation=False,
                    translation_memory=False,
                    glossary=True,
                    batch_translation=True
                )
            )
        )
        self.register(deepl)

        edge_tts = ProviderMetadata(
            provider_id="Edge TTS",
            display_name="Microsoft Edge TTS",
            provider_type="tts",
            capabilities=ProviderCapabilities(
                supports_audio_generation=True,
                tts=TTSCapabilities(
                    voice_library=True,
                    voice_preview=True,
                    speed_control=True,
                    pitch_control=True,
                    volume_control=True,
                    emotion=False,
                    voice_clone=False
                )
            )
        )
        self.register(edge_tts)
        
        elevenlabs = ProviderMetadata(
            provider_id="ElevenLabs",
            display_name="ElevenLabs",
            provider_type="tts",
            capabilities=ProviderCapabilities(
                supports_audio_generation=True,
                tts=TTSCapabilities(
                    voice_library=True,
                    voice_preview=True,
                    emotion=True,
                    voice_clone=True,
                    speed_control=False,
                    pitch_control=False
                )
            )
        )
        self.register(elevenlabs)

        kira = ProviderMetadata(
            provider_id="Kira",
            display_name="Kira AI",
            provider_type="tts",
            capabilities=ProviderCapabilities(
                supports_audio_generation=True,
                tts=TTSCapabilities(
                    voice_library=True,
                    voice_preview=True,
                    speed_control=True,
                    pitch_control=False,
                    volume_control=False,
                    emotion=False,
                    voice_clone=False
                )
            )
        )
        self.register(kira)

        omnivoice = ProviderMetadata(
            provider_id="OmniVoice",
            display_name="OmniVoice AI",
            provider_type="tts",
            capabilities=ProviderCapabilities(
                supports_audio_generation=True,
                tts=TTSCapabilities(
                    voice_library=True,
                    voice_preview=True,
                    speed_control=True,
                    pitch_control=True,
                    volume_control=True,
                    emotion=True,
                    voice_clone=True
                )
            )
        )
        self.register(omnivoice)




