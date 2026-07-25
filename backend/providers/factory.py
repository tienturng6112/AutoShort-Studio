from abc import ABC, abstractmethod
from typing import Type
from backend.providers.base_provider import BaseProvider
from backend.providers.config import ProviderConfig

class IProviderFactory(ABC):
    """Port interface for dynamic initialization and instantiation of AI and Stock Provider adapters."""
    
    @abstractmethod
    def create_provider(self, provider_class: Type[BaseProvider], config: ProviderConfig) -> BaseProvider:
        """Creates and returns an instance of the provider class populated with config credentials.
        
        Args:
            provider_class (Type[BaseProvider]): Subclass of BaseProvider to instantiate.
            config (ProviderConfig): Settings model containing credentials, base URL, and timeouts.
            
        Returns:
            BaseProvider: Instantiated provider adapter instance.
        """
        pass
