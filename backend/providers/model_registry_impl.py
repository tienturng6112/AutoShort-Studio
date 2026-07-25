from typing import Dict, List, Optional
from backend.providers.manager import IProviderManager
from backend.providers.model_registry import IModelRegistry

class ModelRegistry(IModelRegistry):
    """Implementation of IModelRegistry holding dynamic in-memory model caches and aliases mappings."""
    
    def __init__(self, provider_manager: IProviderManager) -> None:
        self._manager = provider_manager
        self._cache: Dict[str, List[str]] = {}
        self._mappings: Dict[str, Dict[str, str]] = {}

    def cache_models(self, provider_id: str, models: List[str]) -> None:
        self._cache[provider_id] = models

    def get_cached_models(self, provider_id: str) -> List[str]:
        return self._cache.get(provider_id, [])

    async def refresh_models(self, provider_id: str) -> List[str]:
        provider = self._manager.get_provider(provider_id)
        if not provider:
            raise KeyError(f"Model registry error: Active provider instance '{provider_id}' not found.")
        models = await provider.list_models()
        self.cache_models(provider_id, models)
        return models

    def map_model(self, provider_id: str, internal_model_name: str, target_provider_model: str) -> None:
        if provider_id not in self._mappings:
            self._mappings[provider_id] = {}
        self._mappings[provider_id][internal_model_name] = target_provider_model

    def resolve_mapped_model(self, provider_id: str, internal_model_name: str) -> Optional[str]:
        return self._mappings.get(provider_id, {}).get(internal_model_name)
