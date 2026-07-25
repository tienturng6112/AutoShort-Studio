from abc import ABC, abstractmethod
from typing import Generator, List, Optional

class BaseProvider(ABC):
    """Port interface for AI Chat and Embedding Providers."""
    
    def __init__(self, name: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def test_connection(self) -> bool:
        """Verifies connection to the external AI Provider."""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """Queries and returns list of available models from provider."""
        pass

    @abstractmethod
    async def chat(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        model: Optional[str] = None, 
        json_mode: bool = False
    ) -> str:
        """Executes a standard chat completion request."""
        pass

    @abstractmethod
    async def stream_chat(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        model: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Executes a streaming chat completion yielding text tokens."""
        pass

    @abstractmethod
    async def embeddings(self, text: str) -> List[float]:
        """Computes vector embeddings for input text."""
        pass
