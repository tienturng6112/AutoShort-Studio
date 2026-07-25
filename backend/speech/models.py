from typing import List, Optional
from pydantic import BaseModel, Field

class Word(BaseModel):
    """Word-level alignment metadata mapping timing and probability."""
    word: str = Field(..., description="The word text segment")
    start: float = Field(..., description="Start timestamp in seconds")
    end: float = Field(..., description="End timestamp in seconds")
    probability: float = Field(default=1.0, description="Confidence score from 0.0 to 1.0")


class Segment(BaseModel):
    """Segment-level transcription details containing a sentence or phrase."""
    id: int = Field(..., description="Unique segment sequential index")
    start: float = Field(..., description="Start timestamp of the segment")
    end: float = Field(..., description="End timestamp of the segment")
    text: str = Field(..., description="The transcribed segment text")
    words: List[Word] = Field(default_factory=list, description="Word-level details inside this segment")
    confidence: float = Field(default=1.0, description="Average confidence score of the segment")
    speaker_id: Optional[str] = Field(default=None, description="Speaker identification code (e.g. Speaker_A)")
    speaker_gender: Optional[str] = Field(default=None, description="Speaker gender (Male, Female, etc.)")
    voice: Optional[str] = Field(default=None, description="Assigned voice model or ID")
    emotion: Optional[dict] = Field(default=None, description="Emotion profile dictionary")
    metadata: dict = Field(default_factory=dict, description="Arbitrary custom fields/metadata")


class Transcript(BaseModel):
    """Full media transcription container, capturing texts, alignments, languages, and metrics."""
    text: str = Field(..., description="Full consolidated transcript text string")
    language: str = Field(..., description="Detected ISO language code (e.g. en, vi)")
    language_probability: float = Field(default=1.0, description="Language detection probability")
    duration: float = Field(..., description="Total audio duration analyzed")
    segments: List[Segment] = Field(default_factory=list, description="Chronological segments list")

    def to_json(self) -> str:
        """Serializes transcript to a JSON formatted string."""
        return self.model_dump_json(indent=2)

    def to_txt(self) -> str:
        """Extracts and outputs raw text lines from segments."""
        return "\n".join(seg.text.strip() for seg in self.segments)

    def to_srt(self) -> str:
        """Compiles timing segments to standard SRT format."""
        srt_lines = []
        for i, seg in enumerate(self.segments, start=1):
            start_time = self._format_timestamp(seg.start)
            end_time = self._format_timestamp(seg.end)
            srt_lines.append(f"{i}")
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(seg.text.strip())
            srt_lines.append("")
        return "\n".join(srt_lines)

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Formats seconds into SRT time representations: HH:MM:SS,mmm"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        msecs = int(round((seconds - int(seconds)) * 1000))
        # Handle rounding overflow
        if msecs == 1000:
            msecs = 0
            secs += 1
            if secs == 60:
                secs = 0
                mins += 1
                if mins == 60:
                    mins = 0
                    hrs += 1
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"
