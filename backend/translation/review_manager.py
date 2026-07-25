import os
import json
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ReviewSegment:
    segment_id: str
    start_time: float
    end_time: float
    speaker: str
    original: str
    translated: str
    optimized: str
    confidence: float
    status: str = "AI Generated" # AI Generated, Reviewed, Approved, Locked, Needs Review
    comment: str = ""
    is_frozen: bool = False

    def to_dict(self):
        return {
            "segment_id": self.segment_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "speaker": self.speaker,
            "original": self.original,
            "translated": self.translated,
            "optimized": self.optimized,
            "confidence": self.confidence,
            "status": self.status,
            "comment": self.comment,
            "is_frozen": self.is_frozen
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            segment_id=data.get("segment_id", ""),
            start_time=data.get("start_time", 0.0),
            end_time=data.get("end_time", 0.0),
            speaker=data.get("speaker", ""),
            original=data.get("original", ""),
            translated=data.get("translated", ""),
            optimized=data.get("optimized", ""),
            confidence=data.get("confidence", 1.0),
            status=data.get("status", "AI Generated"),
            comment=data.get("comment", ""),
            is_frozen=data.get("is_frozen", False)
        )

class ReviewManager:
    """Manages the translation review state for a project."""
    def __init__(self, project_id: str, projects_dir: str = "projects"):
        self.project_id = project_id
        self.config_dir = os.path.join(projects_dir, project_id, "config")
        self.review_file = os.path.join(self.config_dir, "translation_review.json")
        self.segments: Dict[str, ReviewSegment] = {}
        self.load()

    def load(self):
        if os.path.exists(self.review_file):
            with open(self.review_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for seg_data in data.get("segments", []):
                    seg = ReviewSegment.from_dict(seg_data)
                    self.segments[seg.segment_id] = seg

    def save(self):
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.review_file, "w", encoding="utf-8") as f:
            data = {
                "version": "1.1",
                "segments": [seg.to_dict() for seg in self.segments.values()]
            }
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_segment(self, segment: ReviewSegment):
        self.segments[segment.segment_id] = segment
        self.save()

    def get_segment(self, segment_id: str) -> Optional[ReviewSegment]:
        return self.segments.get(segment_id)
        
    def get_all_segments(self) -> List[ReviewSegment]:
        return list(self.segments.values())
