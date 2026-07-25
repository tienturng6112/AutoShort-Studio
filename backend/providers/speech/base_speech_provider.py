from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional

class BaseSpeechProvider(ABC):
    """Port interface for Speech Synthesis (TTS) Providers."""
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Verifies connection to the external Speech Provider.
        Returns standard dict: {"success": bool, "message": str, "status_code": int|None, "latency_ms": int|None, "models": list|None}
        """
        pass

    @abstractmethod
    async def list_voices(self) -> List[Dict[str, Any]]:
        """Returns details on supported voices (gender, locale, name)."""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """Queries and returns list of available TTS models from provider."""
        pass

    @abstractmethod
    async def generate(self, text: str, voice_name: str, output_path: str, emotion_profile: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Synthesizes text to speech.
        Returns: Tuple of (audio_file_path, word_boundaries_list)
        """
        pass

    @abstractmethod
    async def preview(self, text: str, voice_name: str, **kwargs) -> bytes:
        """Synthesizes and returns raw audio bytes representing a short preview."""
        pass

    @abstractmethod
    async def validate_voice(self, voice_name: str, language: str) -> None:
        """
        Validates whether the voice is supported for the target language.
        Raises ValueError if validation fails.
        """
        pass
