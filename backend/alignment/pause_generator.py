from typing import List
from backend.speech.models import Segment

class PauseGenerator:
    """Insures minimum silence/pause intervals exist between consecutive segments."""

    def __init__(self, pause_duration: float = 0.3) -> None:
        self._pause_duration = pause_duration

    def insert_pauses(self, segments: List[Segment]) -> List[Segment]:
        """Inserts configurable pause intervals, shifting subsequent segments forward.
        
        Args:
            segments (List[Segment]): Input segments.
            
        Returns:
            List[Segment]: Adjusted segments with pauses.
        """
        if len(segments) <= 1:
            return segments

        paused_list = [segments[0]]
        current = segments[0]

        for next_seg in segments[1:]:
            duration = max(next_seg.end - next_seg.start, 0.0)
            
            # Enforce start time gap of at least pause_duration from previous segment's end time
            start = max(next_seg.start, current.end + self._pause_duration)
            end = start + duration
            
            current = Segment(
                id=next_seg.id,
                start=start,
                end=end,
                text=next_seg.text,
                words=next_seg.words,
                confidence=next_seg.confidence,
                speaker_id=next_seg.speaker_id,
                speaker_gender=next_seg.speaker_gender,
                voice=next_seg.voice,
                emotion=next_seg.emotion,
                metadata=next_seg.metadata.copy() if next_seg.metadata else {}
            )
            paused_list.append(current)

        return paused_list
