import os
import json
import logging

logger = logging.getLogger(__name__)

class LocalizationService:
    _instance = None
    _dict = {}
    _lang = "vi"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalizationService, cls).__new__(cls)
            cls._instance._base_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..", "resources", "i18n")
            cls._instance.reload()
        return cls._instance

    def reload(self):
        settings_path = os.path.join("config", "settings.json")
        lang = "vi"
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    lang = data.get("language", "vi")
            except Exception:
                pass
        self._lang = lang
        self._load_language(lang)

    def _load_language(self, lang_code):
        file_path = os.path.join(self._base_dir, f"{lang_code}.json")
        en_path = os.path.join(self._base_dir, "en.json")
        
        self._dict = {}
        
        # Load English fallback first
        if os.path.exists(en_path):
            try:
                with open(en_path, "r", encoding="utf-8") as f:
                    self._dict.update(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load fallback en.json: {e}")
                
        # Load target language
        if os.path.exists(file_path) and lang_code != "en":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self._dict.update(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load language file {lang_code}.json: {e}")

    def change_language(self, lang_code):
        settings_path = os.path.join("config", "settings.json")
        data = {}
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
        
        data["language"] = lang_code
        os.makedirs("config", exist_ok=True)
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass
            
        self._lang = lang_code
        self._load_language(lang_code)

    def translate(self, key, default=None):
        return self._dict.get(key, default if default is not None else key)
