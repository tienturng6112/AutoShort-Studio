import json
import os
from typing import Dict, List

class ProfileService:
    """Manages system-level pipeline configuration templates (Profiles)."""
    
    DEFAULT_PROFILES = {
        "Fast": {
            "translation_provider": "ChatAnywhere",
            "chatanywhere": {"model": "gpt-3.5-turbo"},
            "speech_enhancement": "off",
            "tts_provider": "Edge TTS"
        },
        "Standard": {
            "translation_provider": "ChatAnywhere",
            "chatanywhere": {"model": "gpt-4o-mini"},
            "speech_enhancement": "off",
            "tts_provider": "Edge TTS"
        },
        "Cinema": {
            "translation_provider": "ChatAnywhere",
            "chatanywhere": {"model": "gpt-4o"},
            "speech_enhancement": "demucs",
            "tts_provider": "Edge TTS"
        },
        "Anime": {
            "translation_provider": "DeepL",
            "deepl": {"model": "default"},
            "speech_enhancement": "off",
            "tts_provider": "Edge TTS"
        },
        "Documentary": {
            "translation_provider": "ChatAnywhere",
            "chatanywhere": {"model": "gpt-4o-mini"},
            "speech_enhancement": "demucs",
            "tts_provider": "Edge TTS"
        },
        "Podcast": {
            "translation_provider": "ChatAnywhere",
            "chatanywhere": {"model": "gpt-4o-mini"},
            "speech_enhancement": "demucs",
            "tts_provider": "Edge TTS"
        }
    }

    def __init__(self, config_dir: str = "config") -> None:
        self.config_dir = config_dir
        self.profiles_path = os.path.join(self.config_dir, "profiles.json")
        self._ensure_config_exists()

    def _ensure_config_exists(self) -> None:
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
            
        if not os.path.exists(self.profiles_path):
            try:
                with open(self.profiles_path, "w", encoding="utf-8") as f:
                    json.dump({"profiles": self.DEFAULT_PROFILES}, f, indent=4)
            except Exception:
                pass

    def get_profiles(self) -> List[str]:
        """Returns a list of all defined profile names."""
        profiles = self._load_data().get("profiles", {})
        return list(profiles.keys())

    def get_profile_settings(self, profile_name: str) -> Dict:
        """Returns the configuration dictionary for the specified profile."""
        profiles = self._load_data().get("profiles", {})
        return profiles.get(profile_name, {})

    def _load_data(self) -> Dict:
        if os.path.exists(self.profiles_path):
            try:
                with open(self.profiles_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"profiles": self.DEFAULT_PROFILES}
