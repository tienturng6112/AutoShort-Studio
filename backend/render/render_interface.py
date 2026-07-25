from abc import ABC, abstractmethod
from backend.render.timeline_interface import ITimeline

class IRenderEngine(ABC):
    """Port interface for rendering timelines to video exports or preview frames."""
    
    @abstractmethod
    async def render_to_file(self, timeline: ITimeline, output_path: str) -> str:
        """Stitches track layers, mixes audio envelopes, burns subtitles, and exports an MP4/MOV file."""
        pass

    @abstractmethod
    async def generate_preview_frame(self, timeline: ITimeline, timestamp: float) -> bytes:
        """Synthesizes and returns raw visual frame bytes at a timeline timestamp (for visual scrubbing)."""
        pass
