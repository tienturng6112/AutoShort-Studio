import json
import os
import time
import logging
from typing import List, Optional, Dict
from backend.character.metadata import CharacterProfile
from backend.voice.voice_manager import VoiceManager

logger = logging.getLogger("CharacterManager")

class CharacterManager:
    def __init__(self, storage_path: str, voice_manager: Optional[VoiceManager] = None):
        self.storage_path = storage_path
        self.voice_manager = voice_manager
        self._cache: Dict[str, CharacterProfile] = {}
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("version") == 1:
                        for char_dict in data.get("characters", []):
                            profile = CharacterProfile(**char_dict)
                            self._cache[profile.character_id] = profile
            except Exception as e:
                logger.error(f"Failed to load character cache: {e}")

    def _save_cache(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = {
                "version": 1,
                "last_updated": time.time(),
                "characters": [p.model_dump() for p in self._cache.values()]
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save character cache: {e}")

    def create_character(self, display_name: str, **kwargs) -> CharacterProfile:
        """Creates and saves a new character profile."""
        profile = CharacterProfile(display_name=display_name, **kwargs)
        self._cache[profile.character_id] = profile
        self._save_cache()
        return profile

    def update_character(self, character_id: str, **kwargs) -> Optional[CharacterProfile]:
        """Updates properties of an existing character."""
        profile = self._cache.get(character_id)
        if not profile:
            return None
        
        update_data = profile.model_dump()
        update_data.update(kwargs)
        update_data["updated_at"] = time.time()
        
        new_profile = CharacterProfile(**update_data)
        self._cache[character_id] = new_profile
        self._save_cache()
        return new_profile

    def get_character(self, character_id: str) -> Optional[CharacterProfile]:
        """Looks up a character by exact ID."""
        return self._cache.get(character_id)

    def resolve_speaker(self, speaker_label: str) -> CharacterProfile:
        """
        Takes a raw label (e.g. 'Speaker_A') and searches the 'aliases' of all characters.
        If found, returns the matching character. If not, auto-generates a new one.
        """
        for profile in self._cache.values():
            if speaker_label == profile.character_id or speaker_label in profile.aliases or speaker_label == profile.display_name:
                return profile
                
        # Auto-generate if not found
        display_name = speaker_label.replace("_", " ")
        profile = self.create_character(display_name=display_name, aliases=[speaker_label])
        return profile

    def list_characters(self, **filters) -> List[CharacterProfile]:
        """Lists characters, applying optional filters like gender or language."""
        results = []
        for profile in self._cache.values():
            match = True
            for k, v in filters.items():
                if getattr(profile, k, None) != v:
                    match = False
                    break
            if match:
                results.append(profile)
        return results

    def merge(self, source_id: str, target_id: str) -> Optional[CharacterProfile]:
        """
        Merges source_id into target_id.
        All aliases and settings from source are migrated.
        source_id is then deleted.
        """
        if source_id not in self._cache or target_id not in self._cache:
            return None
            
        source = self._cache[source_id]
        target = self._cache[target_id]
        
        # Combine aliases
        new_aliases = list(set(target.aliases + source.aliases))
        
        # Merge properties conservatively
        new_gender = target.gender if target.gender != "Unknown" else source.gender
        
        target.aliases = new_aliases
        target.gender = new_gender
        target.updated_at = time.time()
        
        del self._cache[source_id]
        self._save_cache()
        return target
        
    def assign_voice(self, character_id: str, voice_id: str, provider_id: str):
        """Assigns a preferred voice to the character."""
        profile = self._cache.get(character_id)
        if profile:
            profile.preferred_voice = voice_id
            profile.preferred_provider = provider_id
            profile.updated_at = time.time()
            self._save_cache()
            
    def export_pack(self, file_path: str):
        """Exports all characters to a portable JSON pack."""
        data = {
            "version": 1,
            "characters": [p.model_dump() for p in self._cache.values()]
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
    def import_pack(self, file_path: str):
        """Imports characters from a portable JSON pack."""
        if not os.path.exists(file_path):
            return
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for char_dict in data.get("characters", []):
            profile = CharacterProfile(**char_dict)
            self._cache[profile.character_id] = profile
            
        self._save_cache()

    def lazy_migrate_settings(self, speaker_voices: Dict[str, str]):
        """
        Used for backward compatibility. Given a dictionary of speaker_voices from
        old project settings, it creates characters if they don't already exist.
        """
        changed = False
        for speaker_label, voice_id in speaker_voices.items():
            # Check if any character has this alias
            found = False
            for p in self._cache.values():
                if speaker_label in p.aliases:
                    found = True
                    break
            
            if not found:
                # Create stub
                display_name = speaker_label.replace("_", " ")
                profile = CharacterProfile(
                    display_name=display_name,
                    aliases=[speaker_label],
                    preferred_voice=voice_id
                )
                self._cache[profile.character_id] = profile
                changed = True
                
        if changed:
            self._save_cache()
