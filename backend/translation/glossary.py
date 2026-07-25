import json
import os
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

logger = logging.getLogger("GlossaryManager")

@dataclass
class GlossaryEntry:
    original: str
    translation: str
    category: str = "Custom"
    locked: bool = True
    comment: str = ""

    def to_dict(self):
        return {
            "original": self.original,
            "translation": self.translation,
            "category": self.category,
            "locked": self.locked,
            "comment": self.comment
        }
        
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            original=data.get("original", ""),
            translation=data.get("translation", ""),
            category=data.get("category", "Custom"),
            locked=data.get("locked", True),
            comment=data.get("comment", "")
        )


class GlossaryManager:
    """Manages custom terminology translation mappings, protected brand words, and forced translations."""
    
    def __init__(
        self, 
        project_id: Optional[str] = None,
        projects_dir: str = "projects",
        glossary: Optional[Dict[str, str]] = None, 
        protected_words: Optional[Set[str]] = None
    ) -> None:
        self.project_id = project_id
        self.config_dir = os.path.join(projects_dir, project_id, "config") if project_id else None
        self.glossary_file = os.path.join(self.config_dir, "glossary.json") if self.config_dir else None
        
        self.entries: Dict[str, GlossaryEntry] = {}
        
        # Legacy support
        self._glossary: Dict[str, str] = glossary or {}
        self._protected_words: Set[str] = protected_words or set()
        
        if self.glossary_file:
            self.load()

    def load(self):
        """Loads glossary from disk."""
        if self.glossary_file and os.path.exists(self.glossary_file):
            try:
                with open(self.glossary_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for entry_data in data.get("entries", []):
                        entry = GlossaryEntry.from_dict(entry_data)
                        self.entries[entry.original] = entry
            except Exception as e:
                logger.error(f"Failed to load glossary for {self.project_id}: {e}")

    def save(self):
        """Saves glossary to disk."""
        if not self.config_dir or not self.glossary_file:
            return
            
        os.makedirs(self.config_dir, exist_ok=True)
        try:
            with open(self.glossary_file, "w", encoding="utf-8") as f:
                data = {
                    "version": "1.1",
                    "entries": [entry.to_dict() for entry in self.entries.values()]
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save glossary for {self.project_id}: {e}")

    def add_entry(self, entry: GlossaryEntry) -> None:
        self.entries[entry.original] = entry
        self.save()

    def remove_entry(self, original_term: str) -> None:
        if original_term in self.entries:
            del self.entries[original_term]
            self.save()

    def get_locked_entries(self) -> List[GlossaryEntry]:
        return [entry for entry in self.entries.values() if entry.locked]

    def get_locked_translations(self) -> Dict[str, str]:
        """Returns a simple dict of locked translations for pipeline use."""
        result = self._glossary.copy()
        for entry in self.entries.values():
            if entry.locked:
                result[entry.original] = entry.translation
        return result

    # Legacy Methods for backward compatibility
    def add_terminology(self, source_term: str, target_translation: str) -> None:
        self._glossary[source_term] = target_translation
        self.add_entry(GlossaryEntry(
            original=source_term, 
            translation=target_translation, 
            category="Custom", 
            locked=True
        ))

    def add_protected_word(self, word: str) -> None:
        self._protected_words.add(word)

    def get_glossary(self) -> Dict[str, str]:
        return self.get_locked_translations()

    def get_protected_words(self) -> Set[str]:
        return self._protected_words

    def format_for_prompt(self) -> str:
        lines = []
        if self._protected_words:
            lines.append("GLOSSARY RULES - DO NOT TRANSLATE THESE PROTECTED WORDS:")
            for word in sorted(self._protected_words):
                lines.append(f"  - Keep '{word}' exactly as is")
                
        locked_glossary = self.get_locked_translations()
        if locked_glossary:
            lines.append("GLOSSARY RULES - FORCED TRANSLATIONS:")
            for src, tgt in sorted(locked_glossary.items()):
                lines.append(f"  - Translate '{src}' as '{tgt}'")
        return "\n".join(lines)
