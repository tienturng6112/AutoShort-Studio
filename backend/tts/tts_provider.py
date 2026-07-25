from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional

class BaseTTSProvider(ABC):
    """Port interface for Speech Synthesis (TTS) Providers."""
    
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


# DEPRECATED: TTSProviderFactory has been removed.
# Use backend.providers.speech.manager.SpeechProviderManager.create_provider() instead.
# This is the sole TTS factory as of the Regression Stabilization Sprint.
