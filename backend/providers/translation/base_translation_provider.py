from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseTranslationProvider(ABC):
    """Port interface representing a provider-agnostic translation engine."""
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Verifies connection to the external Translation Provider.
        Returns standard dict: {"success": bool, "message": str, "status_code": int|None, "latency_ms": int|None, "models": list|None}
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """Queries and returns list of available translation models from provider."""
        pass

    @abstractmethod
    async def translate_segments(
        self, 
        segments: List[Dict[str, Any]], 
        target_lang: str, 
        glossary: Optional[Dict[str, str]] = None,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Translates a list of text segments while keeping segment IDs intact.
        
        Args:
            segments (List[Dict[str, Any]]): Input segments, e.g. [{"id": 0, "text": "Hello"}]
            target_lang (str): Destination language code (e.g., 'vi', 'es').
            glossary (Optional[Dict[str, str]]): Terminology replacements.
            context (Optional[str]): Preceding scene dialogue and speaker summaries for contextual translation.
            
        Returns:
            List[Dict[str, Any]]: Translated segments preserving IDs, e.g. [{"id": 0, "text": "Hola"}]
        """
        pass
