import json
import os
from typing import Dict, Optional

class ImportCache:
    """Cache registry preventing duplicate downloads of remote or local media assets."""
    
    def __init__(self, cache_file_path: str = "projects/import_cache.json") -> None:
        self._cache_file = cache_file_path
        self._cache: Dict[str, str] = self._load()

    def _load(self) -> Dict[str, str]:
        if os.path.exists(self._cache_file):
            try:
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
        try:
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get(self, source: str) -> Optional[str]:
        """Resolves cached local target path if it exists on disk.
        
        Args:
            source (str): Source path or YouTube URL.
            
        Returns:
            Optional[str]: Cached local path key, or None.
        """
        local_path = self._cache.get(source)
        if local_path and os.path.exists(local_path):
            return local_path
        return None

    def set(self, source: str, local_path: str) -> None:
        """Registers a source link mapping to local paths.
        
        Args:
            source (str): Source path or URL.
            local_path (str): Download target path.
        """
        self._cache[source] = local_path
        self._save()

    def clear(self) -> None:
        """Flushes cache registries."""
        self._cache.clear()
        self._save()
