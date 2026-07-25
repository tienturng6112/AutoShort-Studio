from typing import List
from backend.speech.models import Segment

class SceneBuilder:
    """Groups linear sequential subtitle segments into conversational scenes."""
    
    def __init__(self, max_gap_seconds: float = 2.0, max_chars: int = 1000) -> None:
        self.max_gap_seconds = max_gap_seconds
        self.max_chars = max_chars

    def build_scenes(self, segments: List[Segment]) -> List[List[Segment]]:
        """
        Processes a list of Segment objects and groups them into discrete scenes.
        
        Args:
            segments: List of Segments sorted chronologically.
            
        Returns:
            A list of scenes, where each scene is a list of Segments.
        """
        if not segments:
            return []
            
        scenes = []
        current_scene = []
        current_chars = 0
        
        for seg in segments:
            seg_chars = len(seg.text)
            
            if not current_scene:
                current_scene.append(seg)
                current_chars += seg_chars
                continue
                
            prev_seg = current_scene[-1]
            gap = seg.start - prev_seg.end
            
            # Break scene if silence gap is too large
            break_by_gap = gap > self.max_gap_seconds
            
            # Break scene if the character budget is exceeded
            break_by_budget = (current_chars + seg_chars) > self.max_chars
            
            # Note: Speaker changes are preserved in the same scene 
            # to allow LLM to see conversation context unless gap/budget forces a split.
            
            if break_by_gap or break_by_budget:
                scenes.append(current_scene)
                current_scene = [seg]
                current_chars = seg_chars
            else:
                current_scene.append(seg)
                current_chars += seg_chars
                
        if current_scene:
            scenes.append(current_scene)
            
        return scenes
