import hashlib
import os
import shutil
from typing import Optional

class VoiceCache:
    """Caches synthesized speech audio clips to prevent redundant provider generation requests."""

    def __init__(self, cache_dir: str = "projects/voice_cache") -> None:
        self._dir = cache_dir
        os.makedirs(self._dir, exist_ok=True)

    def _make_hash(self, text: str, voice_name: str) -> str:
        """Generates MD5 hash token based on voice name and text content."""
        payload = f"{voice_name.strip()}:{text.strip()}"
        return hashlib.md5(payload.encode("utf-8")).hexdigest()

    def get(self, text: str, voice_name: str) -> Optional[str]:
        """Resolves absolute path of cached file if it exists.
        
        Args:
            text (str): Synthesized text content.
            voice_name (str): Target voice name key.
            
        Returns:
            Optional[str]: Absolute path to cached audio file, or None.
        """
        h = self._make_hash(text, voice_name)
        for ext in ["wav", "mp3"]:
            path = os.path.join(self._dir, f"{h}.{ext}")
            if os.path.exists(path):
                return os.path.abspath(path)
        return None

    def set(self, text: str, voice_name: str, source_audio_path: str) -> str:
        """Caches a synthesized file, copying it into the cache directory.
        
        Args:
            text (str): Synthesized text content.
            voice_name (str): Target voice name key.
            source_audio_path (str): Synthesized file path.
            
        Returns:
            str: Target cached file path.
        """
        h = self._make_hash(text, voice_name)
        ext = os.path.splitext(source_audio_path)[1].lstrip(".") or "wav"
        dest_path = os.path.join(self._dir, f"{h}.{ext}")
        
        shutil.copy2(source_audio_path, dest_path)
        return os.path.abspath(dest_path)

    def clear(self) -> None:
        """Purges cache folders."""
        if os.path.exists(self._dir):
            shutil.rmtree(self._dir)
            os.makedirs(self._dir, exist_ok=True)
