import os
import json
from typing import Any, Dict, List

class ChunkManager:
    """Orchestrates segment array splitting, tracking completed checkpoints to resume after errors."""
    
    def __init__(self, state_file_path: str, chunk_size: int = 10, max_retries: int = 3) -> None:
        self._state_file = state_file_path
        self._chunk_size = chunk_size
        self._max_retries = max_retries
        self._state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(self._state_file):
            try:
                with open(self._state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"completed_chunks": {}, "translations": {}}
        return {"completed_chunks": {}, "translations": {}}

    def _save_state(self) -> None:
        os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
        try:
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def split_segments(self, segments: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Splits a list of segment inputs into chunk sublists.
        
        Args:
            segments (List[Dict[str, Any]]): Entire list of transcript segments.
            
        Returns:
            List[List[Dict[str, Any]]]: Nested list of segment chunks.
        """
        return [segments[i : i + self._chunk_size] for i in range(0, len(segments), self._chunk_size)]

    def is_chunk_completed(self, chunk_index: int) -> bool:
        """Checks if the target chunk index was already processed.
        
        Args:
            chunk_index (int): Chunk index to check.
            
        Returns:
            bool: True if completed, False otherwise.
        """
        return str(chunk_index) in self._state["completed_chunks"]

    def get_chunk_translations(self, chunk_index: int) -> List[Dict[str, Any]]:
        """Loads cached translations matching the target chunk index.
        
        Args:
            chunk_index (int): Chunk index to load.
            
        Returns:
            List[Dict[str, Any]]: Translated segment list.
        """
        return self._state["translations"].get(str(chunk_index), [])

    def save_chunk_translations(self, chunk_index: int, translated_segments: List[Dict[str, Any]]) -> None:
        """Saves chunk translation progress to allow resuming if interrupted.
        
        Args:
            chunk_index (int): Chunk index to save.
            translated_segments (List[Dict[str, Any]]): Translated segment outputs.
        """
        self._state["completed_chunks"][str(chunk_index)] = True
        self._state["translations"][str(chunk_index)] = translated_segments
        self._save_state()

    def clear_state(self) -> None:
        """Purges progress checkpoints."""
        self._state = {"completed_chunks": {}, "translations": {}}
        self._save_state()

    @property
    def max_retries(self) -> int:
        """Gets maximum allowed retries."""
        return self._max_retries
