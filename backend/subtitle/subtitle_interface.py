from abc import ABC, abstractmethod
from typing import Any, Dict, List

class ISubtitleEngine(ABC):
    """Port interface for turning word-timing logs into burnable subtitle files."""
    
    @abstractmethod
    def generate_srt(self, subtitle_data: List[Dict[str, Any]], output_path: str) -> str:
        """Compiles timing checkpoints to standard SRT format."""
        pass

    @abstractmethod
    def generate_ass(self, subtitle_data: List[Dict[str, Any]], output_path: str) -> str:
        """Compiles word timings to ASS format with custom fonts, colors, and word-highlighting codes."""
        pass
