import json
import os
from typing import Dict, Optional

class TranslationCache:
    """Caches segment-level translations to prevent redundant provider requests."""
    
    def __init__(self, cache_file_path: str = "projects/translation_cache.json") -> None:
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

    def _make_key(self, source_text: str, target_lang: str) -> str:
        return f"{target_lang.strip().lower()}:{source_text.strip()}"

    def get(self, source_text: str, target_lang: str) -> Optional[str]:
        """Loads cached translation matching the source text and target language.
        
        Args:
            source_text (str): Source text segment.
            target_lang (str): Destination language code.
            
        Returns:
            Optional[str]: Cached translated text, or None.
        """
        key = self._make_key(source_text, target_lang)
        return self._cache.get(key)

    def set(self, source_text: str, target_lang: str, translated_text: str) -> None:
        """Saves a segment translation inside the cache mapping.
        
        Args:
            source_text (str): Source text segment.
            target_lang (str): Destination language code.
            translated_text (str): Translated output text.
        """
        key = self._make_key(source_text, target_lang)
        self._cache[key] = translated_text
        self._save()

    def clear(self) -> None:
        """Purges cache entries."""
        self._cache.clear()
        self._save()
