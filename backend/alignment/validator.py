from typing import List, Set
from backend.speech.models import Transcript

class TranscriptValidator:
    """Validates transcript structures, identifying timing errors, overlaps, and rate limit violations."""

    def __init__(self, max_cps: float = 20.0, max_cpl: int = 50) -> None:
        self._max_cps = max_cps
        self._max_cpl = max_cpl

    def validate(self, transcript: Transcript) -> List[str]:
        """Audits transcripts, returning a list of validation error descriptions.
        
        Args:
            transcript (Transcript): Transcript to validate.
            
        Returns:
            List[str]: List of validation errors, empty if valid.
        """
        errors = []
        seen_ids: Set[int] = set()
        prev_end = 0.0

        for idx, seg in enumerate(transcript.segments):
            # 1. Duplicate ID validation
            if seg.id in seen_ids:
                errors.append(f"Segment index {idx} has duplicate ID: {seg.id}")
            seen_ids.add(seg.id)

            # 2. Timing boundary checks
            if seg.start < 0:
                errors.append(f"Segment {seg.id} has negative start timestamp: {seg.start}")
            if seg.end <= seg.start:
                errors.append(f"Segment {seg.id} has invalid duration (start: {seg.start}, end: {seg.end})")

            # 3. Overlap check
            if idx > 0 and seg.start < prev_end:
                errors.append(
                    f"Segment {seg.id} start time ({seg.start}) overlaps with previous segment's end time ({prev_end})"
                )
            
            if seg.end > seg.start:
                prev_end = seg.end

            # 4. Text completeness check
            if not seg.text.strip():
                errors.append(f"Segment {seg.id} contains empty text payload")

            # 5. CPL constraint check
            if len(seg.text) > self._max_cpl:
                errors.append(f"Segment {seg.id} exceeds CPL limit ({len(seg.text)} > {self._max_cpl})")

            # 6. CPS constraint check
            duration = seg.end - seg.start
            if duration > 0:
                cps = len(seg.text.strip()) / duration
                if cps > self._max_cps:
                    errors.append(f"Segment {seg.id} exceeds CPS limit ({cps:.2f} > {self._max_cps})")

        return errors
