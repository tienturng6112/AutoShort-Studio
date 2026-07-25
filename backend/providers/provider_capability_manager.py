import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.providers.provider_registry import ProviderRegistry

logger = logging.getLogger("ProviderCapabilityManager")

class CapabilityValidationError(Exception):
    pass

class ProviderCapabilityManager:
    """Unified Capability Manager for querying and validating provider capabilities."""
    
    def __init__(self, registry: ProviderRegistry, config_dir: str = "config"):
        self.registry = registry
        self.config_dir = config_dir
        self.cache_file = os.path.join(self.config_dir, "provider_capabilities.json")
        self._cache = {}
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load provider capability cache: {e}")

    def _save_cache(self):
        os.makedirs(self.config_dir, exist_ok=True)
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save provider capability cache: {e}")

    def refresh(self):
        """Refreshes metadata, models, and voices from all providers and updates the cache."""
        # For dynamic providers, this might make network requests to get updated voices/models.
        # Since we use static metadata right now, we just copy registry into cache format.
        now = datetime.utcnow().isoformat()
        
        for provider in self.registry.list_providers():
            pid = provider.provider_id
            if pid not in self._cache:
                self._cache[pid] = {}
                
            self._cache[pid]["models"] = provider.models
            self._cache[pid]["voices"] = provider.voices
            self._cache[pid]["last_refreshed"] = now
            self._cache[pid]["reachable"] = True # placeholder for network check
            
        self._save_cache()

    def supports(self, provider_id: str, domain: str, feature: str) -> bool:
        """Returns True if the provider supports the requested feature in the given domain."""
        metadata = self.registry.get_metadata(provider_id)
        if not metadata:
            return False
            
        caps = metadata.capabilities
        domain_caps = getattr(caps, domain, None)
        
        if domain_caps is None:
            return False
            
        return getattr(domain_caps, feature, False)

    def require(self, provider_id: str, domain: str, feature: str):
        """Raises CapabilityValidationError if the provider does not support the feature."""
        if not self.supports(provider_id, domain, feature):
            raise CapabilityValidationError(f"Provider '{provider_id}' does not support the '{feature}' capability in domain '{domain}'.")

    def get_models(self, provider_id: str) -> List[str]:
        if provider_id in self._cache:
            return self._cache[provider_id].get("models", [])
        meta = self.registry.get_metadata(provider_id)
        return meta.models if meta else []

    def get_voices(self, provider_id: str) -> List[Dict[str, Any]]:
        if provider_id in self._cache:
            return self._cache[provider_id].get("voices", [])
        meta = self.registry.get_metadata(provider_id)
        return meta.voices if meta else []

    def get_limits(self, provider_id: str) -> Dict[str, Any]:
        meta = self.registry.get_metadata(provider_id)
        return meta.limits if meta else {}

    def get_provider_diagnostics(self) -> List[Dict[str, Any]]:
        """Returns diagnostic data for all providers."""
        diagnostics = []
        for provider in self.registry.list_providers():
            pid = provider.provider_id
            cache_info = self._cache.get(pid, {})
            diag = {
                "provider_id": pid,
                "name": provider.display_name,
                "type": provider.provider_type,
                "version": provider.version,
                "reachable": cache_info.get("reachable", "Unknown"),
                "last_refreshed": cache_info.get("last_refreshed", "Never"),
                "models_count": len(self.get_models(pid)),
                "voices_count": len(self.get_voices(pid))
            }
            diagnostics.append(diag)
        return diagnostics
