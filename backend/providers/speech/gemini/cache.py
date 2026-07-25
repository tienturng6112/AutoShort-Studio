import os
import json
import hashlib
from typing import Optional

class GeminiAudioCache:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _generate_key(self, text: str, model: str, voice: str, language: str, speed: float, pitch: float) -> str:
        payload = f"{text}|{model}|{voice}|{language}|{speed}|{pitch}"
        return hashlib.md5(payload.encode("utf-8")).hexdigest()
        
    def get(self, text: str, model: str, voice: str, language: str, speed: float, pitch: float) -> Optional[str]:
        key = self._generate_key(text, model, voice, language, speed, pitch)
        path = os.path.join(self.cache_dir, f"{key}.wav")
        if os.path.exists(path):
            return path
        return None
        
    def set_path(self, text: str, model: str, voice: str, language: str, speed: float, pitch: float) -> str:
        key = self._generate_key(text, model, voice, language, speed, pitch)
        return os.path.join(self.cache_dir, f"{key}.wav")
