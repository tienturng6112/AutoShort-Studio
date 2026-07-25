from typing import Dict, List, Optional, Type
from backend.providers.base_provider import BaseProvider
from backend.providers.metadata import ProviderMetadata
from backend.providers.registry import IProviderRegistry

class ProviderRegistry(IProviderRegistry):
    """Implementation of IProviderRegistry mapping classes, metadata, and default system choices."""
    
    def __init__(self) -> None:
        self._classes: Dict[str, Type[BaseProvider]] = {}
        self._metadata: Dict[str, ProviderMetadata] = {}
        self._instances: Dict[str, BaseProvider] = {}
        self._active_provider_id: Optional[str] = None

    def register_provider(self, provider_class: Type[BaseProvider], metadata: ProviderMetadata) -> None:
        provider_id = metadata.provider_id
        self._classes[provider_id] = provider_class
        self._metadata[provider_id] = metadata

    def get_available_providers(self) -> List[ProviderMetadata]:
        return list(self._metadata.values())

    def resolve_provider(self, name: str) -> BaseProvider:
        if name in self._instances:
            return self._instances[name]
        if name not in self._classes:
            raise KeyError(f"Provider registry error: Provider '{name}' has not been registered.")
        
        provider_class = self._classes[name]
        # Instantiates standard adapter constructor stubs
        instance = provider_class(name=name)
        self._instances[name] = instance
        return instance

    def set_active_provider(self, name: str) -> None:
        if name not in self._classes:
            raise KeyError(f"Provider registry error: Provider '{name}' has not been registered.")
        self._active_provider_id = name

    def get_active_provider(self) -> Optional[BaseProvider]:
        if not self._active_provider_id:
            return None
        return self.resolve_provider(self._active_provider_id)

    def lookup_by_capability(self, capability_name: str) -> List[ProviderMetadata]:
        matching = []
        for meta in self._metadata.values():
            caps = meta.capabilities
            if getattr(caps, capability_name, False):
                matching.append(meta)
        return matching
