import os
import time
from typing import Any, Callable, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from backend.speech.base_speech_provider import BaseSpeechProvider
from backend.speech.cancellation import CancellationToken
from backend.speech.model_manager import SpeechModelManager
from backend.speech.models import Transcript

class SpeechBenchmark(BaseModel):
    """Execution telemetry captured for performance audits."""
    model: str = Field(..., description="Whisper model size identifier")
    device: str = Field(..., description="Target hardware runner (cpu/cuda)")
    execution_time_seconds: float = Field(..., description="Raw processing time in seconds")
    realtime_factor: float = Field(..., description="Execution speed ratio (execution_time / duration)")
    memory_usage_mb: float = Field(default=0.0, description="RSS memory overhead in MB")


class SpeechService:
    """Orchestrates speech recognition steps, checking hardware accelerators, and saving exports formats."""

    def __init__(
        self, 
        speech_provider: BaseSpeechProvider, 
        model_manager: SpeechModelManager
    ) -> None:
        self._provider = speech_provider
        self._model_manager = model_manager

    def detect_best_device(self) -> str:
        """Checks PyTorch availability to return CUDA/GPU if present, otherwise CPU."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    def _get_memory_usage_mb(self) -> float:
        """Queries process resident set size (RSS) memory consumption."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0

    async def transcribe_audio(
        self, 
        audio_path: str, 
        model_size: str, 
        output_dir: str,
        progress_callback: Optional[Callable[[float], None]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Tuple[Transcript, SpeechBenchmark]:
        """Downloads/resolves target models, transcribes files, and writes TXT/JSON/SRT formats.
        
        Returns:
            Tuple[Transcript, SpeechBenchmark]: Output transcript entity and performance metrics.
        """
        # 1. Resolve hardware device and model weights path
        device = self.detect_best_device()
        model_path = self._model_manager.get_model_path(model_size)
        
        # 2. Transcribe and measure latency/memory telemetry
        start_time = time.perf_counter()
        mem_before = self._get_memory_usage_mb()
        
        transcript = await self._provider.transcribe(
            audio_path=audio_path,
            model_path=model_path,
            device=device,
            progress_callback=progress_callback,
            cancellation_token=cancellation_token
        )
        
        end_time = time.perf_counter()
        mem_after = self._get_memory_usage_mb()
        
        duration = end_time - start_time
        rtf = duration / transcript.duration if transcript.duration > 0 else 0.0
        
        benchmark = SpeechBenchmark(
            model=model_size,
            device=device,
            execution_time_seconds=duration,
            realtime_factor=rtf,
            memory_usage_mb=max(mem_after - mem_before, 0.0)
        )
        
        # 3. Export formatting files
        os.makedirs(output_dir, exist_ok=True)
        
        # Save transcript.json
        with open(os.path.join(output_dir, "transcript.json"), "w", encoding="utf-8") as f:
            f.write(transcript.to_json())
            
        # Save transcript.txt
        with open(os.path.join(output_dir, "transcript.txt"), "w", encoding="utf-8") as f:
            f.write(transcript.to_txt())
            
        # Save transcript.srt
        with open(os.path.join(output_dir, "transcript.srt"), "w", encoding="utf-8") as f:
            f.write(transcript.to_srt())
            
        return transcript, benchmark
