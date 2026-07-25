import os
import json
import logging
import asyncio
from typing import Any, Dict, List, Tuple, Optional
from backend.tts.tts_provider import BaseTTSProvider
from backend.models.model_manager import ModelManager

logger = logging.getLogger("OmniVoiceProvider")

class OmniVoiceProvider(BaseTTSProvider):
    """Flagship Local AI Voice Engine for AutoShort Studio."""
    
    def __init__(self, config_path: str = "config/providers/omnivoice.json"):
        self.config_path = config_path
        self._enabled = True
        self._model_folder = "models/omnivoice"
        self._inference_device = "auto"
        self._cpu_threads = 4
        self._gpu_id = 0
        self._memory_limit_gb = 4.0
        self._streaming = False
        self._ref_audio_folder = "data/voices/clones"
        self.model_manager = ModelManager(self._model_folder)
        self.initialize()

    def initialize(self):
        """Lazy initialization of OmniVoice inference engine."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    c = json.load(f)
                    self._enabled = c.get("enabled", True)
                    self._model_folder = c.get("model_folder") or "models/omnivoice"
                    self._inference_device = c.get("inference_device") or "auto"
                    self._cpu_threads = c.get("cpu_threads", 4)
                    self._gpu_id = c.get("gpu_id", 0)
                    self._memory_limit_gb = c.get("memory_limit_gb", 4.0)
                    self._streaming = c.get("streaming", False)
                    self._ref_audio_folder = c.get("ref_audio_folder") or "data/voices/clones"
            except Exception as e:
                logger.error(f"Failed to load OmniVoice config: {e}")
        
        if not self._model_folder:
            self._model_folder = "models/omnivoice"
        if not self._ref_audio_folder:
            self._ref_audio_folder = "data/voices/clones"
            
        os.makedirs(self._model_folder, exist_ok=True)
        os.makedirs(self._ref_audio_folder, exist_ok=True)
        # Background loading of models is simulated here via async init or lazy load during generation.

    def shutdown(self):
        """Memory cleanup and engine cancellation."""
        logger.info("Shutting down OmniVoice Engine and releasing VRAM...")
        # Placeholder for torch.cuda.empty_cache() etc.

    async def test_connection(self) -> Dict[str, Any]:
        """Validates inference engine is ready locally."""
        hardware = self.model_manager.get_system_hardware()
        installed = self.model_manager.detect_installed_models()
        if not installed:
            return {
                "status": "Failed",
                "error": "No OmniVoice models installed in " + self._model_folder,
                "hardware": hardware
            }
        return {
            "status": "Ready",
            "models_loaded": len(installed),
            "inference_mode": hardware.get("inference_mode", "CPU"),
            "hardware": hardware
        }

    async def list_models(self) -> List[str]:
        installed = self.model_manager.detect_installed_models()
        return [m["id"] for m in installed] if installed else ["omnivoice-base-v1"]

    async def list_languages(self) -> List[str]:
        return ["en", "vi", "ja", "ko", "zh"]

    async def list_voices(self) -> List[Dict[str, Any]]:
        # Combining Presets, Designed, and Cloned voices
        voices = [
            {"voice_id": "preset:nova", "display_name": "Nova (Standard)", "gender": "Female", "language": "en", "provider_id": "OmniVoice"},
            {"voice_id": "preset:echo", "display_name": "Echo (Standard)", "gender": "Male", "language": "en", "provider_id": "OmniVoice"},
            {"voice_id": "preset:nam", "display_name": "Nam Minh (Standard)", "gender": "Male", "language": "vi", "provider_id": "OmniVoice"},
            {"voice_id": "preset:mai", "display_name": "Mai Phương (Standard)", "gender": "Female", "language": "vi", "provider_id": "OmniVoice"}
        ]
        
        # Load clones
        if os.path.exists(self._ref_audio_folder):
            for f in os.listdir(self._ref_audio_folder):
                if f.endswith(".wav") or f.endswith(".mp3"):
                    vid = f"clone:{os.path.splitext(f)[0]}"
                    voices.append({
                        "voice_id": vid,
                        "display_name": f"Clone: {os.path.splitext(f)[0]}",
                        "gender": "Unknown",
                        "language": "auto",
                        "provider_id": "OmniVoice"
                    })
        return voices

    async def clone_voice(self, ref_audio_path: str, reference_transcript: str = None, quality: str = "high") -> str:
        """Processes reference audio and returns a cloned voice ID."""
        import shutil
        import uuid
        clone_id = str(uuid.uuid4())[:8]
        dest = os.path.join(self._ref_audio_folder, f"clone_{clone_id}.wav")
        shutil.copy2(ref_audio_path, dest)
        return f"clone:clone_{clone_id}"

    async def design_voice(self, attributes: Dict[str, str]) -> str:
        """Designs a voice from parameters (Gender, Age, Pitch, Tone)."""
        import uuid
        design_id = f"design:{str(uuid.uuid4())[:8]}"
        # Store attributes mapping in memory or disk
        return design_id

    def supports(self, feature: str) -> bool:
        return feature in ["emotion", "speed", "voice_library", "voice_preview", "voice_clone", "voice_design", "offline"]

    async def _run_inference(self, text: str, voice_id: str, emotion: str, speed: float) -> bytes:
        """Core AI inference engine simulation."""
        # Simulated generation latency dependent on hardware
        import time
        hw = self.model_manager.get_system_hardware()
        delay = 2.0 if hw.get("inference_mode") == "CPU" else 0.5
        await asyncio.sleep(delay)
        
        # Return dummy 1 second WAV audio
        import io, wave
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(b'\\x00' * 24000)
        return wav_buf.getvalue()

    # --- BaseTTSProvider Adapter ---

    async def generate(self, text: str, voice_name: str, output_path: str, emotion_profile: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        if not self._enabled:
            raise ValueError("OmniVoice is disabled.")
            
        emotion = emotion_profile.get("emotion", "neutral") if emotion_profile else "neutral"
        speed = 1.0
        
        audio_bytes = await self._run_inference(text, voice_name, emotion, speed)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
            
        words = text.split()
        boundaries = [{"word": w, "start": i*0.5, "end": (i+1)*0.5} for i, w in enumerate(words)]
        return output_path, boundaries

    async def preview(self, text: str, voice_name: str, **kwargs) -> bytes:
        if not self._enabled:
            raise ValueError("OmniVoice is disabled.")
        return await self._run_inference(text, voice_name, "neutral", 1.0)

    async def validate_voice(self, voice_name: str, language: str) -> None:
        if voice_name.startswith("clone:") or voice_name.startswith("design:"):
            return
        voices = await self.list_voices()
        if any(v["voice_id"] == voice_name for v in voices):
            return
        raise ValueError(f"Voice '{voice_name}' is not supported by OmniVoice.")
