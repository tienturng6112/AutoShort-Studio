from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAIProvider(ABC):
    @abstractmethod
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to the provider. Returns True if successful, False otherwise."""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """List models available from this provider."""
        pass

    @abstractmethod
    async def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        model: Optional[str] = None, 
        json_mode: bool = False
    ) -> str:
        """Generate text response from the provider."""
        pass
