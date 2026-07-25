from abc import ABC, abstractmethod
from typing import List, Optional
from backend.providers.base_provider import BaseProvider
from backend.providers.metadata import ProviderMetadata

class IProviderManager(ABC):
    """Port interface managing instantiation lifetimes, listings, and default active configurations of providers."""
    
    @abstractmethod
    def register_provider(self, provider_id: str, provider_instance: BaseProvider, metadata: ProviderMetadata) -> None:
        """Registers an active provider adapter instance into memory.
        
        Args:
            provider_id (str): Unique registered provider identifier key.
            provider_instance (BaseProvider): Concrete provider adapter instance.
            metadata (ProviderMetadata): Capability matrix tags matching provider.
        """
        pass

    @abstractmethod
    def unregister_provider(self, provider_id: str) -> None:
        """Purges a registered provider instance from the manager.
        
        Args:
            provider_id (str): Target provider key.
        """
        pass

    @abstractmethod
    def get_provider(self, provider_id: str) -> Optional[BaseProvider]:
        """Retrieves the active provider adapter instance matching the ID.
        
        Args:
            provider_id (str): Unique provider identifier key.
            
        Returns:
            Optional[BaseProvider]: Adapter instance if registered, otherwise None.
        """
        pass

    @abstractmethod
    def list_providers(self) -> List[ProviderMetadata]:
        """Lists all registered providers and their metadata.
        
        Returns:
            List[ProviderMetadata]: Capability descriptors list of active providers.
        """
        pass

    @abstractmethod
    def set_active_provider(self, provider_id: str) -> None:
        """Sets the system-wide default active provider.
        
        Args:
            provider_id (str): Target provider key.
        """
        pass

    @abstractmethod
    def get_active_provider(self) -> Optional[BaseProvider]:
        """Returns the default active provider instance.
        
        Returns:
            Optional[BaseProvider]: Default provider instance, or None if none configured.
        """
        pass
