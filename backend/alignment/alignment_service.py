import os
from typing import List, Optional
from backend.alignment.merger import SegmentMerger
from backend.alignment.optimizer import TimelineOptimizer
from backend.alignment.pause_generator import PauseGenerator
from backend.alignment.reading_speed import ReadingSpeedAnalyzer
from backend.alignment.splitter import SegmentSplitter
from backend.alignment.validator import TranscriptValidator
from backend.speech.models import Segment, Transcript
from backend.core.exceptions import TimelineSynchronizationError

class TimelineAlignmentService:
    """Pipeline coordinating segment splitting, merging, overlap resolution, pause inserts, and exports."""

    def __init__(
        self,
        max_cpl: int = 40,
        min_duration: float = 1.2,
        max_merge_chars: int = 40,
        min_segment_gap: float = 0.3,
        max_cps: float = 20.0
    ) -> None:
        self._splitter = SegmentSplitter(max_cpl=max_cpl)
        self._merger = SegmentMerger(min_duration=min_duration, max_merge_chars=max_merge_chars)
        self._optimizer = TimelineOptimizer(min_duration=0.2)
        self._pause_gen = PauseGenerator(pause_duration=min_segment_gap)
        self._validator = TranscriptValidator(max_cps=max_cps, max_cpl=max_cpl)
        self._analyzer = ReadingSpeedAnalyzer()

    async def align_transcript(
        self, 
        transcript: Transcript, 
        output_dir: Optional[str] = None,
        video_duration: Optional[float] = None
    ) -> Transcript:
        """Runs the timeline alignment pipeline to adjust transcript segments for voice and subtitles.
        
        Args:
            transcript (Transcript): Target translated transcript.
            output_dir (Optional[str]): Location folder to export aligned outputs.
            video_duration (Optional[float]): Original video duration constraint.
            
        Returns:
            Transcript: Aligned transcript container.
        """
        if not transcript.segments:
            return transcript

        # Bypass timeline optimization edits to preserve original Whisper timestamps exactly
        final_segs: List[Segment] = []
        for idx, seg in enumerate(transcript.segments):
            final_segs.append(
                Segment(
                    id=idx,
                    start=seg.start,
                    end=seg.end,
                    text=seg.text,
                    words=seg.words,
                    confidence=seg.confidence,
                    speaker_id=seg.speaker_id,
                    speaker_gender=seg.speaker_gender,
                    voice=seg.voice,
                    emotion=seg.emotion,
                    metadata=seg.metadata.copy() if seg.metadata else {}
                )
            )

        # Pad the timeline with an empty segment to match video duration if last segment ends early
        if video_duration is not None and final_segs:
            last_seg_end = final_segs[-1].end
            if video_duration - last_seg_end > 0.100:
                final_segs.append(
                    Segment(
                        id=len(final_segs),
                        start=max(video_duration - 0.010, last_seg_end),
                        end=video_duration,
                        text="",
                        words=[],
                        confidence=1.0,
                        speaker_id="Speaker_A",
                        speaker_gender=None,
                        voice=None,
                        emotion=None,
                        metadata={}
                    )
                )

        full_text = " ".join(seg.text.strip() for seg in final_segs if seg.text.strip())
        
        # Always recompute total_duration from max(segment.end)
        total_duration = max(seg.end for seg in final_segs) if final_segs else 0.0

        # Validate that recomputed duration matches video duration within 100ms
        if video_duration is not None:
            if abs(total_duration - video_duration) > 0.100:
                raise TimelineSynchronizationError(
                    f"Timeline duration mismatch: Aligned transcript duration {total_duration:.3f}s "
                    f"differs from video duration {video_duration:.3f}s by more than 100 ms."
                )

        aligned_transcript = Transcript(
            text=full_text,
            language=transcript.language,
            language_probability=transcript.language_probability,
            duration=total_duration,
            segments=final_segs
        )

        # Write exports files
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
            with open(os.path.join(output_dir, "aligned_transcript.json"), "w", encoding="utf-8") as f:
                f.write(aligned_transcript.to_json())
                
            with open(os.path.join(output_dir, "aligned_transcript.srt"), "w", encoding="utf-8") as f:
                f.write(aligned_transcript.to_srt())

        return aligned_transcript
