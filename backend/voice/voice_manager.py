import json
import os
import time
import logging
import asyncio
from typing import List, Optional, Dict
from backend.voice.metadata import VoiceMetadata
from backend.providers.provider_registry import ProviderRegistry
from backend.providers.provider_capability_manager import ProviderCapabilityManager

logger = logging.getLogger("VoiceManager")

class VoiceManager:
    def __init__(self, capability_manager: Optional[ProviderCapabilityManager] = None, cache_path: Optional[str] = None):
        if capability_manager is None:
            from backend.providers.provider_registry import ProviderRegistry
            from backend.providers.provider_capability_manager import ProviderCapabilityManager
            import os
            registry = ProviderRegistry()
            registry.inject_legacy_providers()
            registry.discover_providers(os.path.join("backend", "plugins", "providers"))
            capability_manager = ProviderCapabilityManager(registry, config_dir="config")
            capability_manager.refresh()
            
        self.cap_mgr = capability_manager
        self.registry = capability_manager.registry
        self.cache_path = cache_path or os.path.join("config", "voice_cache.json")
        self._cache = {
            "version": 1,
            "last_updated": 0,
            "providers": {}
        }
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("version") == 1:
                        self._cache = data
            except Exception as e:
                logger.error(f"Failed to load voice cache: {e}")

    def _save_cache(self):
        try:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save voice cache: {e}")

    async def refresh(self, provider_id: Optional[str] = None) -> int:
        """Queries providers for voices, updates the cache, and returns the number of voices loaded."""
        total_loaded = 0
        
        providers_to_refresh = []
        if provider_id:
            provider = self.registry.get_metadata(provider_id)
            if not provider:
                provider = next((p for p in self.registry.list_providers(only_enabled=False) if p.provider_id.lower() == provider_id.lower()), None)
            if provider and provider.provider_type == "tts":
                providers_to_refresh.append(provider)
        else:
            providers_to_refresh = [p for p in self.registry.list_providers() if p.provider_type == "tts"]

        from backend.services.speech_facade_service import SpeechFacadeService
        facade = SpeechFacadeService()

        for provider in providers_to_refresh:
            pid = provider.provider_id
            
            try:
                provider_instance = facade._manager.get(pid)
                if not provider_instance:
                    continue
                    
                # Support async and sync list_voices
                if asyncio.iscoroutinefunction(provider_instance.list_voices):
                    raw_voices = await provider_instance.list_voices()
                else:
                    raw_voices = provider_instance.list_voices()
                
                # Normalize raw_voices into VoiceMetadata dictionaries
                normalized = []
                for v in raw_voices:
                    try:
                        # Ensure v is dict
                        if not isinstance(v, dict):
                            # Try to cast if it's an object
                            v = v.__dict__ if hasattr(v, '__dict__') else v
                        
                        # Preserve existing favorite status if any
                        existing = self.get_voice(v.get("name", ""), pid)
                        favorite = existing.favorite if existing else False
                        
                        meta = VoiceMetadata(
                            voice_id=v.get("name", ""),
                            provider_id=pid,
                            display_name=v.get("display_name", v.get("name", "Unknown")),
                            language=v.get("language", "Unknown"),
                            locale=v.get("locale"),
                            gender=v.get("gender", "Unknown"),
                            favorite=favorite,
                            preview_supported=self.cap_mgr.supports(pid, "tts", "voice_preview")
                        )
                        normalized.append(meta.model_dump())
                    except Exception as e:
                        logger.warning(f"Error normalizing voice {v} from {pid}: {e}")
                        
                self._cache["providers"][pid] = {
                    "last_refreshed": time.time(),
                    "voices": normalized
                }
                total_loaded += len(normalized)
            except Exception as e:
                logger.error(f"Failed to refresh voices for {pid}: {e}")
                
        self._cache["last_updated"] = time.time()
        self._save_cache()
        return total_loaded

    def list_voices(self, **filters) -> List[VoiceMetadata]:
        """Returns all cached voices matching the exact filter constraints."""
        results = []
        for pid, provider_data in self._cache.get("providers", {}).items():
            for v_dict in provider_data.get("voices", []):
                meta = VoiceMetadata(**v_dict)
                match = True
                for k, v in filters.items():
                    if getattr(meta, k, None) != v:
                        match = False
                        break
                if match:
                    results.append(meta)
        return results

    def search(self, query: str, **filters) -> List[VoiceMetadata]:
        """Fuzzy searches voices by tags, display_name, or accent, while respecting filters."""
        query = query.lower()
        base_results = self.list_voices(**filters)
        
        if not query:
            return base_results
            
        results = []
        for meta in base_results:
            searchable_text = f"{meta.display_name} {meta.language} {meta.locale} {meta.gender} {' '.join(meta.tags)}".lower()
            if query in searchable_text:
                results.append(meta)
                
        return results

    def get_voice(self, voice_id: str, provider_id: str) -> Optional[VoiceMetadata]:
        """Exact lookup for a specific voice."""
        provider_data = self._cache.get("providers", {}).get(provider_id, {})
        for v_dict in provider_data.get("voices", []):
            if v_dict.get("voice_id") == voice_id:
                return VoiceMetadata(**v_dict)
        return None

    def favorite(self, voice_id: str, provider_id: str, is_favorite: bool):
        """Marks or unmarks a voice as a favorite, persisting the change to cache."""
        provider_data = self._cache.get("providers", {}).get(provider_id, {})
        for v_dict in provider_data.get("voices", []):
            if v_dict.get("voice_id") == voice_id:
                v_dict["favorite"] = is_favorite
                self._save_cache()
                return

    async def preview(self, text: str, voice_id: str, provider_id: str) -> bytes:
        """Dispatches a transient synthesis request to the provider to preview the voice."""
        from backend.services.speech_facade_service import SpeechFacadeService
        provider_instance = SpeechFacadeService()._manager.get(provider_id)
        if not provider_instance:
            raise ValueError(f"Provider {provider_id} not available")
            
        if asyncio.iscoroutinefunction(provider_instance.synthesize_speech):
            return await provider_instance.synthesize_speech(text, voice_id)
        else:
            return provider_instance.synthesize_speech(text, voice_id)
