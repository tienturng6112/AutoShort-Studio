import time
import os
from typing import Any, Dict, List, Tuple, Optional
from backend.providers.speech.base_speech_provider import BaseSpeechProvider
from .client import GeminiSpeechClient
from .cache import GeminiAudioCache
from .models import GeminiSpeechSettings

class GeminiSpeechProvider(BaseSpeechProvider):
    def __init__(self, api_key: str, cache_dir: Optional[str] = None):
        self.api_key = api_key
        self.client = GeminiSpeechClient(api_key=api_key)
        self.cache = GeminiAudioCache(cache_dir or "cache/speech/gemini")

    async def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "message": "API Key is empty", "status_code": 401}
            
        start = time.perf_counter()
        try:
            models = await self.client.list_models()
            audio_models = [m for m in models if m.supports_audio]
            latency = int((time.perf_counter() - start) * 1000)
            
            if not audio_models:
                return {
                    "success": False,
                    "message": "This API endpoint does not expose speech-capable models for your API key.",
                    "status_code": 200,
                    "latency_ms": latency
                }
                
            return {
                "success": True, 
                "message": "Connected", 
                "status_code": 200, 
                "latency_ms": latency, 
                "models": [m.name for m in audio_models], "capabilities": {m.name: m.capabilities for m in audio_models}
            }
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return {"success": False, "message": str(e), "latency_ms": latency}

    async def list_models(self) -> List[str]:
        models = await self.client.list_models()
        return [m.name for m in models if m.supports_audio]

    async def list_voices(self) -> List[Dict[str, Any]]:
        voices = await self.client.list_voices()
        return [{"name": v.name, "gender": v.gender} for v in voices]

    async def generate(self, text: str, voice_name: str, output_path: str, emotion_profile: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        # Emotion profile could override settings if needed, but for now we extract from kwargs or use defaults
        model = emotion_profile.get("model", "gemini-1.5-flash") if emotion_profile else "gemini-1.5-flash"
        language = emotion_profile.get("language", "en-US") if emotion_profile else "en-US"
        speed = float(emotion_profile.get("speed", 1.0)) if emotion_profile else 1.0
        pitch = float(emotion_profile.get("pitch", 0.0)) if emotion_profile else 0.0

        cached_path = self.cache.get(text, model, voice_name, language, speed, pitch)
        if cached_path:
            # Check if output_path is different from cache path
            if cached_path != output_path:
                import shutil
                shutil.copy2(cached_path, output_path)
            return output_path, []

        audio_bytes = await self.client.generate_speech(text, model, voice_name, language, speed, pitch)
        
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
            
        cache_dest = self.cache.set_path(text, model, voice_name, language, speed, pitch)
        if cache_dest != output_path:
            import shutil
            shutil.copy2(output_path, cache_dest)
            
        return output_path, []

    async def preview(self, text: str, voice_name: str, **kwargs) -> bytes:
        emotion_profile = kwargs.get("emotion_profile")
        model = emotion_profile.get("model", "gemini-1.5-flash") if emotion_profile else "gemini-1.5-flash"
        language = emotion_profile.get("language", "en-US") if emotion_profile else "en-US"
        speed = float(emotion_profile.get("speed", 1.0)) if emotion_profile else 1.0
        pitch = float(emotion_profile.get("pitch", 0.0)) if emotion_profile else 0.0
        
        return await self.client.generate_speech(text, model, voice_name, language, speed, pitch)

    async def validate_voice(self, voice_name: str, language: str) -> None:
        voices = await self.client.list_voices()
        for v in voices:
            if v.name == voice_name:
                return
        raise ValueError(f"Voice {voice_name} not found.")
