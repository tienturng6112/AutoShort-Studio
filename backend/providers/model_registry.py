from abc import ABC, abstractmethod
from typing import List, Optional

class IModelRegistry(ABC):
    """Port interface mapping internal model names to provider model identifiers and caches."""
    
    @abstractmethod
    def cache_models(self, provider_id: str, models: List[str]) -> None:
        """Saves a raw list of models into the local in-memory registry cache.
        
        Args:
            provider_id (str): Provider identifier key.
            models (List[str]): List of models retrieved.
        """
        pass

    @abstractmethod
    def get_cached_models(self, provider_id: str) -> List[str]:
        """Loads cached models list for the target provider.
        
        Args:
            provider_id (str): Provider identifier key.
            
        Returns:
            List[str]: Cached model names list.
        """
        pass

    @abstractmethod
    async def refresh_models(self, provider_id: str) -> List[str]:
        """Polls list_models() from the provider and updates the cache registry.
        
        Args:
            provider_id (str): Provider identifier key.
            
        Returns:
            List[str]: Newly loaded model names list.
        """
        pass

    @abstractmethod
    def map_model(self, provider_id: str, internal_model_name: str, target_provider_model: str) -> None:
        """Maps a uniform internal model label (e.g. 'llm.fast') to provider-specific names (e.g. 'gpt-4o-mini').
        
        Args:
            provider_id (str): Target provider key.
            internal_model_name (str): Internal system label key.
            target_provider_model (str): Provider-specific model name.
        """
        pass

    @abstractmethod
    def resolve_mapped_model(self, provider_id: str, internal_model_name: str) -> Optional[str]:
        """Resolves mapped model identifier from the registry.
        
        Args:
            provider_id (str): Provider key.
            internal_model_name (str): Internal system label key.
            
        Returns:
            Optional[str]: Mapped model identifier name, or None if mapping doesn't exist.
        """
        pass
