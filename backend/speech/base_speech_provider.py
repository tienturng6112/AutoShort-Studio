from abc import ABC, abstractmethod
from typing import Callable, Optional
from backend.speech.cancellation import CancellationToken
from backend.speech.models import Transcript

class BaseSpeechProvider(ABC):
    """Port interface for Speech-to-Text translation and transcription engines."""
    
    @abstractmethod
    async def transcribe(
        self, 
        audio_path: str, 
        model_path: str, 
        device: str, 
        progress_callback: Optional[Callable[[float], None]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Transcript:
        """Translates and transcribes WAV audio into structured segment-level transcripts.
        
        Args:
            audio_path (str): Path to input WAV file.
            model_path (str): Path to locally stored model weights.
            device (str): Target processing hardware (e.g. cpu, cuda).
            progress_callback (Optional[Callable[[float], None]]): Callable receiving progress percentage (0.0 - 100.0).
            cancellation_token (Optional[CancellationToken]): Token to check for cancelled states.
            
        Returns:
            Transcript: Domain schema container.
        """
        pass
