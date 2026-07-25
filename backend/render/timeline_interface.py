from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class ITimelineClip(ABC):
    """Port interface representing a generic media clip track item in the timeline."""
    
    @property
    @abstractmethod
    def start_time(self) -> float:
        pass
        
    @property
    @abstractmethod
    def duration(self) -> float:
        pass


class ITimelineLayer(ABC):
    """Port interface representing a track layer containing overlapping or sequential clips."""
    
    @property
    @abstractmethod
    def index(self) -> int:
        pass
        
    @abstractmethod
    def add_clip(self, clip: ITimelineClip) -> None:
        pass
        
    @abstractmethod
    def list_clips(self) -> List[ITimelineClip]:
        pass


class ITimeline(ABC):
    """Port interface representing the multi-track visual/audio composition graph."""
    
    @property
    @abstractmethod
    def aspect_ratio(self) -> str:
        pass

    @abstractmethod
    def get_layer(self, layer_index: int) -> ITimelineLayer:
        """Fetches or creates a composition track layer."""
        pass

    @abstractmethod
    def add_effect(self, clip_id: str, effect_name: str, params: Dict[str, Any]) -> None:
        """Attaches dynamic visual or volume effects to a timeline clip."""
        pass

    @abstractmethod
    def add_transition(self, clip_id_a: str, clip_id_b: str, transition_type: str, duration: float) -> None:
        """Applies a transition between two adjacent clips on a track layer."""
        pass

    @abstractmethod
    def add_subtitle_track(self, text: str, start_time: float, duration: float, highlight_words: Optional[List[Dict[str, Any]]] = None) -> None:
        """Adds structured subtitles data overlay tracks."""
        pass
