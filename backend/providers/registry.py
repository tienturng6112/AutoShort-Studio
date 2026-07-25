from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type
from backend.providers.base_provider import BaseProvider
from backend.providers.metadata import ProviderMetadata

class IProviderRegistry(ABC):
    """Port interface representing the AI Provider Registry for dynamic discovery."""
    
    @abstractmethod
    def register_provider(self, provider_class: Type[BaseProvider], metadata: ProviderMetadata) -> None:
        """Dynamically registers a provider class and its feature metadata.
        
        Args:
            provider_class (Type[BaseProvider]): Class definition subclassing BaseProvider.
            metadata (ProviderMetadata): Feature compatibility matrix values.
        """
        pass

    @abstractmethod
    def get_available_providers(self) -> List[ProviderMetadata]:
        """Discovers and returns capability metadata for all registered providers.
        
        Returns:
            List[ProviderMetadata]: Registered provider capability descriptors list.
        """
        pass

    @abstractmethod
    def resolve_provider(self, name: str) -> BaseProvider:
        """Resolves, instantiates, and returns a registered provider strategy instance by name.
        
        Args:
            name (str): Unique registered provider name.
            
        Returns:
            BaseProvider: Instantiated provider adapter.
        """
        pass

    @abstractmethod
    def set_active_provider(self, name: str) -> None:
        """Sets the default system active provider.
        
        Args:
            name (str): Registered provider name.
        """
        pass

    @abstractmethod
    def get_active_provider(self) -> Optional[BaseProvider]:
        """Resolves and returns the currently selected active provider instance.
        
        Returns:
            Optional[BaseProvider]: Active default provider, or None if empty.
        """
        pass

    @abstractmethod
    def lookup_by_capability(self, capability_name: str) -> List[ProviderMetadata]:
        """Queries and returns metadata descriptors of all providers supporting the specified capability key.
        
        Args:
            capability_name (str): Property key name of ProviderCapabilities (e.g. supports_stream).
            
        Returns:
            List[ProviderMetadata]: List of matching provider metadata configurations.
        """
        pass
