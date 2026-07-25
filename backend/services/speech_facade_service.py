import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class SpeechFacadeService:
    """UI-facing service wrapping SpeechProviderManager.
    
    This facade ensures the UI layer never instantiates or imports providers directly.
    """
    
    def __init__(self, manager: Optional[Any] = None):
        if manager is None:
            from backend.providers.speech.manager import SpeechProviderManager
            manager = SpeechProviderManager()
        self._manager = manager
    
    async def test_connection(self, provider_id: str) -> dict:
        try:
            return await self._manager.test_connection(provider_id)
        except Exception as e:
            return {"success": False, "error": str(e), "provider": provider_id}
    
    async def refresh_voices(self, provider_id: str) -> list:
        try:
            voices = await self._manager.refresh(provider_id)
            print(f"\n[SPEECH FACADE SERVICE] refresh_voices provider_id={provider_id} len(voices)={len(voices)}")
            return voices
        except Exception as e:
            print(f"\n[SPEECH FACADE SERVICE] refresh_voices provider_id={provider_id} EXCEPTION: {e}")
            return []

    async def refresh_models(self, provider_id: str) -> list:
        try:
            provider = self._manager.get(provider_id)
            if provider and hasattr(provider, "list_models"):
                return await provider.list_models()
            return []
        except Exception as e:
            logger.error(f"SpeechFacadeService refresh_models failed for '{provider_id}': {e}")
            return []
    
    def create_provider(self, provider_id: str, settings: dict):
        try:
            return self._manager.create_provider(provider_id, settings)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": provider_id
            }
    
    async def preview(self, provider_id: str, text: str, voice: str, **kwargs) -> bytes:
        try:
            provider = self._manager.get(provider_id)
            if not provider:
                raise ValueError(f"Speech provider '{provider_id}' not registered.")
            return await provider.preview(text, voice, **kwargs)
        except Exception as e:
            logger.error(f"Speech preview failed for {provider_id}: {e}")
            raise
    
    def list_providers(self) -> list:
        try:
            return self._manager.list()
        except Exception:
            return []

    def get(self, provider_id: str):
        return self._manager.get(provider_id)

    def supports(self, provider_id: str, capability: str) -> bool:
        if not hasattr(self, "_cap_mgr"):
            from backend.providers.provider_capability_manager import ProviderCapabilityManager
            from backend.providers.provider_registry import ProviderRegistry
            import os
            registry = ProviderRegistry()
            registry.inject_legacy_providers()
            registry.discover_providers(os.path.join("backend", "plugins", "providers"))
            self._cap_mgr = ProviderCapabilityManager(registry, config_dir="config")
            self._cap_mgr.refresh()
        return self._cap_mgr.supports(provider_id, "tts", capability)
