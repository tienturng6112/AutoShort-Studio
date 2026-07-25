import json
import os
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

logger = logging.getLogger("TranslationMemory")

@dataclass
class MemoryEntry:
    original: str
    translation: str
    usage_count: int = 1
    confidence: float = 1.0
    last_used: str = "" # ISO format string
    source: str = "Auto TM" # User Edited, Auto TM, Glossary
    locked: bool = False

    def to_dict(self) -> dict:
        return {
            "original": self.original,
            "translation": self.translation,
            "usage_count": self.usage_count,
            "confidence": self.confidence,
            "last_used": self.last_used,
            "source": self.source,
            "locked": self.locked
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            original=data.get("original", ""),
            translation=data.get("translation", ""),
            usage_count=data.get("usage_count", 1),
            confidence=data.get("confidence", 1.0),
            last_used=data.get("last_used", ""),
            source=data.get("source", "Auto TM"),
            locked=data.get("locked", False)
        )

class TranslationMemory:
    """Manages project-level translation consistency memory."""
    
    def __init__(self, project_id: str, projects_dir: str = "projects"):
        self.project_id = project_id
        self.config_dir = os.path.join(projects_dir, project_id, "config")
        self.memory_file = os.path.join(self.config_dir, "translation_memory.json")
        self.memory: Dict[str, Dict[str, Any]] = {
            "terminology": {}, # Original text -> translated text (legacy)
            "characters": {},  # Character ID -> { "name": "Translated Name", "pronoun": "anh/em" }
            "history": []      # Recent interactions to maintain flow
        }
        self.segments: Dict[str, MemoryEntry] = {}
        self.load()

    def load(self):
        """Loads translation memory from disk."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Load legacy dicts if exist
                    for key in ["terminology", "characters", "history"]:
                        if key in data:
                            self.memory[key] = data[key]
                    
                    # Load new segments if exist
                    for seg_data in data.get("segments", []):
                        entry = MemoryEntry.from_dict(seg_data)
                        self.segments[entry.original] = entry
            except Exception as e:
                logger.error(f"Failed to load translation memory for {self.project_id}: {e}")

    def save(self):
        """Saves translation memory to disk."""
        os.makedirs(self.config_dir, exist_ok=True)
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                data_to_save = {
                    "version": "1.1",
                    "terminology": self.memory["terminology"],
                    "characters": self.memory["characters"],
                    "history": self.memory["history"],
                    "segments": [entry.to_dict() for entry in self.segments.values()]
                }
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save translation memory for {self.project_id}: {e}")

    def add_term(self, source: str, translation: str, source_type: str = "Auto TM", locked: bool = False):
        """Adds a terminology mapping (legacy adapter & new entry adapter)."""
        # Legacy
        self.memory["terminology"][source] = translation
        
        # New
        now_str = datetime.utcnow().isoformat()
        if source in self.segments:
            entry = self.segments[source]
            # Don't overwrite if existing is User Edited and new is Auto TM
            if entry.source == "User Edited" and source_type != "User Edited" and not locked:
                return
            entry.translation = translation
            entry.usage_count += 1
            entry.last_used = now_str
            if locked or source_type == "User Edited":
                entry.source = source_type
            entry.locked = locked or entry.locked
        else:
            self.segments[source] = MemoryEntry(
                original=source,
                translation=translation,
                usage_count=1,
                last_used=now_str,
                source=source_type,
                locked=locked
            )
        self.save()
        
    def log_usage(self, original_text: str):
        """Increments usage count for an existing memory segment."""
        if original_text in self.segments:
            self.segments[original_text].usage_count += 1
            self.segments[original_text].last_used = datetime.utcnow().isoformat()
            self.save()
            
    def get_translation(self, original_text: str) -> Optional[str]:
        if original_text in self.segments:
            return self.segments[original_text].translation
        return self.memory["terminology"].get(original_text)

    def add_character_mapping(self, char_id: str, name: str, pronoun: str):
        """Registers a consistent character mapping and pronoun preference."""
        self.memory["characters"][char_id] = {
            "name": name,
            "pronoun": pronoun
        }
        self.save()

    def get_context_string(self) -> str:
        """Serializes memory into a string for LLM injection."""
        lines = []
        if self.memory["terminology"]:
            lines.append("Consistent Terminology to use:")
            for src, tgt in self.memory["terminology"].items():
                lines.append(f"- {src} -> {tgt}")
                
        if self.memory["characters"]:
            lines.append("\nCharacter Pronouns:")
            for char_id, info in self.memory["characters"].items():
                lines.append(f"- {char_id} (Name: {info['name']}) -> Use Pronoun: {info['pronoun']}")
                
        return "\n".join(lines)
