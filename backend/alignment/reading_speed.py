from typing import Dict, Optional

class LanguageProfile:
    """Standard reading speed limits and profiles for a specific language."""
    
    def __init__(self, target_cps: float = 15.0, target_wpm: float = 150.0) -> None:
        self.target_cps = target_cps
        self.target_wpm = target_wpm


class ReadingSpeedAnalyzer:
    """Calculates reading speed metrics (CPS, WPM) based on language profiles."""

    def __init__(self, profiles: Optional[Dict[str, LanguageProfile]] = None) -> None:
        self._profiles = profiles or {
            "en": LanguageProfile(target_cps=15.0, target_wpm=150.0),
            "vi": LanguageProfile(target_cps=12.0, target_wpm=120.0),
            "es": LanguageProfile(target_cps=14.0, target_wpm=140.0),
            "default": LanguageProfile(target_cps=15.0, target_wpm=150.0)
        }

    def calculate_cps(self, text: str, duration: float) -> float:
        """Calculates Characters Per Second (CPS)."""
        if duration <= 0:
            return 0.0
        return len(text.strip()) / duration

    def calculate_wpm(self, text: str, duration: float) -> float:
        """Calculates Words Per Minute (WPM)."""
        if duration <= 0:
            return 0.0
        words_count = len(text.strip().split())
        return (words_count / duration) * 60.0

    def get_profile(self, language: str) -> LanguageProfile:
        """Retrieves reading profile constraints for a target language."""
        return self._profiles.get(language.strip().lower(), self._profiles["default"])
