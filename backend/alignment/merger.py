from typing import List
from backend.speech.models import Segment

class SegmentMerger:
    """Merges short consecutive segments to prevent visual stutter in subtitles."""

    def __init__(self, min_duration: float = 1.2, max_merge_chars: int = 40) -> None:
        self._min_duration = min_duration
        self._max_merge_chars = max_merge_chars

    def merge_segments(self, segments: List[Segment]) -> List[Segment]:
        """Iterates and merges short adjacent segments if their combined text fits limits.
        
        Args:
            segments (List[Segment]): Chronological segments list.
            
        Returns:
            List[Segment]: Merged segments list.
        """
        if not segments:
            return []

        merged_list = []
        current = segments[0]

        for next_seg in segments[1:]:
            curr_dur = current.end - current.start
            next_dur = next_seg.end - next_seg.start
            combined_len = len(current.text) + len(next_seg.text) + 1
            
            # Merge condition checks:
            # 1. Fits in line limits
            # 2. At least one is shorter than min duration
            if (combined_len <= self._max_merge_chars) and (
                curr_dur < self._min_duration or next_dur < self._min_duration
            ):
                current = Segment(
                    id=current.id,
                    start=current.start,
                    end=next_seg.end,
                    text=f"{current.text.strip()} {next_seg.text.strip()}",
                    words=current.words + next_seg.words,
                    confidence=min(current.confidence, next_seg.confidence),
                    speaker_id=current.speaker_id,
                    speaker_gender=current.speaker_gender,
                    voice=current.voice,
                    emotion=current.emotion,
                    metadata=current.metadata.copy() if current.metadata else {}
                )
            else:
                merged_list.append(current)
                current = next_seg

        merged_list.append(current)
        return merged_list
