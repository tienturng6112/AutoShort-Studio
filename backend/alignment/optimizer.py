from typing import List
from backend.speech.models import Segment

class TimelineOptimizer:
    """Optimizes start/end timestamps to prevent overlap collisions and duration errors."""

    def __init__(self, min_duration: float = 0.2) -> None:
        self._min_duration = min_duration

    def optimize_timestamps(self, segments: List[Segment]) -> List[Segment]:
        """Adjusts start/end timings to remove overlaps and correct negative/zero durations.
        
        Args:
            segments (List[Segment]): Input segments.
            
        Returns:
            List[Segment]: Optimized segments.
        """
        if not segments:
            return []

        optimized_list = []
        
        # Adjust first segment
        first = segments[0]
        start = max(first.start, 0.0)
        end = max(first.end, start + self._min_duration)
        
        current = Segment(
            id=first.id,
            start=start,
            end=end,
            text=first.text,
            words=first.words,
            confidence=first.confidence,
            speaker_id=first.speaker_id,
            speaker_gender=first.speaker_gender,
            voice=first.voice,
            emotion=first.emotion,
            metadata=first.metadata.copy() if first.metadata else {}
        )
        optimized_list.append(current)

        for next_seg in segments[1:]:
            start = next_seg.start
            end = next_seg.end
            
            # 1. Prevent overlap with previous segment's end time
            if start < current.end:
                start = current.end
                
            # 2. Prevent negative or zero durations
            if (end - start) < self._min_duration:
                end = start + self._min_duration
                
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
            optimized_list.append(current)

        return optimized_list
