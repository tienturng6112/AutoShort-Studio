from typing import Dict, List, Optional, Any
from backend.providers.speech.base_speech_provider import BaseSpeechProvider

class SpeechProviderManager:
    """Independent manager and sole factory for Speech (TTS) Providers.
    
    This is the ONLY way to create speech provider instances.
    TTSProviderFactory has been deprecated and removed.
    """
    
    def __init__(self):
        self._providers: Dict[str, BaseSpeechProvider] = {}
        
    def register(self, provider_id: str, provider: BaseSpeechProvider) -> None:
        self._providers[provider_id.lower()] = provider
        
    def remove(self, provider_id: str) -> None:
        self._providers.pop(provider_id.lower(), None)
        
    def get(self, provider_id: str, create_lazy: bool = True) -> Optional[BaseSpeechProvider]:
        provider_id = provider_id.lower()
        if provider_id not in self._providers and create_lazy:
            try:
                import json
                import os
                settings_path = os.path.join("config", "settings.json")
                settings = {}
                if os.path.exists(settings_path):
                    with open(settings_path, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                self.create_provider(provider_id, settings)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Lazy creation of speech provider {provider_id} failed: {e}")
        return self._providers.get(provider_id)
        
    def list(self) -> List[str]:
        return list(self._providers.keys())
        
    async def test_connection(self, provider_id: str) -> Dict[str, Any]:
        provider = self.get(provider_id)
        if not provider:
            return {"success": False, "error": "Provider not registered."}
        try:
            return await provider.test_connection()
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    async def refresh(self, provider_id: str) -> List[Dict[str, Any]]:
        provider = self.get(provider_id)
        if not provider:
            print(f"\n[SPEECH PROVIDER MANAGER] refresh provider_id={provider_id} provider=NULL -> return []")
            return []
        voices = await provider.list_voices()
        print(f"\n[SPEECH PROVIDER MANAGER] refresh provider_id={provider_id} len(voices)={len(voices)}")
        return voices

    def create_provider(self, provider_id: str, settings: dict) -> BaseSpeechProvider:
        """Factory: creates, registers, and returns a speech provider instance.
        
        This is the sole TTS factory. Replaces the deprecated TTSProviderFactory.
        
        Args:
            provider_id: Provider identifier (gemini, kira, elevenlabs, omnivoice, edge).
            settings: Application settings dict (typically loaded from settings.json).
            
        Returns:
            BaseSpeechProvider: The created and registered provider instance.
        """
        provider_id = provider_id.lower()

        if provider_id == "gemini":
            from backend.providers.speech.gemini.provider import GeminiSpeechProvider
            config = settings.get("providers", {}).get("gemini", settings.get("gemini", {}))
            provider = GeminiSpeechProvider(
                api_key=config.get("api_key", ""),
                cache_dir=config.get("cache_dir")
            )
        elif provider_id == "kira":
            from backend.providers.speech.elevenlabs.kira_provider import KiraProvider
            config = settings.get("kira", settings.get("providers", {}).get("kira", {}))
            try:
                speed_val = float(config.get("speed", 1.0))
            except (ValueError, TypeError):
                speed_val = 1.0
            provider = KiraProvider(
                api_key=config.get("api_key", ""),
                model=config.get("model", "kira-3.0-flash-tts"),
                speed=speed_val
            )
        elif provider_id == "elevenlabs":
            from backend.providers.speech.elevenlabs.elevenlabs_provider import ElevenLabsProvider
            config = settings.get("elevenlabs", settings.get("providers", {}).get("elevenlabs", {}))
            provider = ElevenLabsProvider(
                api_key=config.get("api_key", ""),
                model=config.get("model", "eleven_multilingual_v2")
            )
        elif provider_id == "omnivoice":
            from backend.providers.tts.omnivoice_provider import OmniVoiceProvider
            provider = OmniVoiceProvider()
        else:
            # Default: Edge TTS (no API key required)
            from backend.providers.speech.edge.edge_tts_provider import EdgeTTSProvider
            provider = EdgeTTSProvider()

        import inspect
        if inspect.isabstract(provider.__class__):
            raise ValueError(f"Provider class {provider.__class__.__name__} for '{provider_id}' is abstract. Missing methods.")

        self.register(provider_id, provider)
        return provider

