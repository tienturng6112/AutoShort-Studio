from typing import Dict, List, Optional
from backend.providers.base_provider import BaseProvider
from backend.providers.metadata import ProviderMetadata
from backend.providers.manager import IProviderManager

class ProviderManager(IProviderManager):
    """Implementation of IProviderManager coordinates running provider lifecycle mapping registries."""
    
    def __init__(self) -> None:
        self._instances: Dict[str, BaseProvider] = {}
        self._metadata: Dict[str, ProviderMetadata] = {}
        self._active_provider_id: Optional[str] = None

    def register_provider(self, provider_id: str, provider_instance: BaseProvider, metadata: ProviderMetadata) -> None:
        self._instances[provider_id] = provider_instance
        self._metadata[provider_id] = metadata

    def unregister_provider(self, provider_id: str) -> None:
        if provider_id in self._instances:
            del self._instances[provider_id]
        if provider_id in self._metadata:
            del self._metadata[provider_id]
        if self._active_provider_id == provider_id:
            self._active_provider_id = None

    def get_provider(self, provider_id: str) -> Optional[BaseProvider]:
        return self._instances.get(provider_id)

    def list_providers(self) -> List[ProviderMetadata]:
        return list(self._metadata.values())

    def set_active_provider(self, provider_id: str) -> None:
        if provider_id not in self._instances:
            raise KeyError(f"Provider manager error: Provider instance '{provider_id}' is not loaded.")
        self._active_provider_id = provider_id

    def get_active_provider(self) -> Optional[BaseProvider]:
        if not self._active_provider_id:
            return None
        return self._instances.get(self._active_provider_id)
