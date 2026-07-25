import os
import json
import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class TranslationHistoryEvent:
    event_id: str
    segment_id: str
    previous_translation: str
    new_translation: str
    timestamp: str
    editor: str # System, User

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "segment_id": self.segment_id,
            "previous_translation": self.previous_translation,
            "new_translation": self.new_translation,
            "timestamp": self.timestamp,
            "editor": self.editor
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            event_id=data.get("event_id", ""),
            segment_id=data.get("segment_id", ""),
            previous_translation=data.get("previous_translation", ""),
            new_translation=data.get("new_translation", ""),
            timestamp=data.get("timestamp", ""),
            editor=data.get("editor", "System")
        )

class HistoryManager:
    """Manages translation history and Undo/Redo operations for a project."""
    def __init__(self, project_id: str, projects_dir: str = "projects"):
        self.project_id = project_id
        self.config_dir = os.path.join(projects_dir, project_id, "config")
        self.history_file = os.path.join(self.config_dir, "translation_history.json")
        self.events: List[TranslationHistoryEvent] = []
        
        self.undo_stack: List[TranslationHistoryEvent] = []
        self.redo_stack: List[TranslationHistoryEvent] = []
        self.load()

    def load(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for event_data in data.get("events", []):
                    event = TranslationHistoryEvent.from_dict(event_data)
                    self.events.append(event)
                    self.undo_stack.append(event)

    def save(self):
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.history_file, "w", encoding="utf-8") as f:
            data = {
                "version": "1.1",
                "events": [e.to_dict() for e in self.events]
            }
            json.dump(data, f, indent=2, ensure_ascii=False)

    def log_event(self, segment_id: str, previous: str, new: str, editor: str = "User"):
        event = TranslationHistoryEvent(
            event_id=str(uuid.uuid4()),
            segment_id=segment_id,
            previous_translation=previous,
            new_translation=new,
            timestamp=datetime.utcnow().isoformat(),
            editor=editor
        )
        self.events.append(event)
        self.undo_stack.append(event)
        self.redo_stack.clear()
        self.save()

    def undo(self) -> Optional[TranslationHistoryEvent]:
        if not self.undo_stack:
            return None
        event = self.undo_stack.pop()
        self.redo_stack.append(event)
        return event

    def redo(self) -> Optional[TranslationHistoryEvent]:
        if not self.redo_stack:
            return None
        event = self.redo_stack.pop()
        self.undo_stack.append(event)
        return event
