import json
import os

def migrate_settings(settings_path: str):
    if not os.path.exists(settings_path):
        return
        
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        modified = False
        
        # New structure
        if "providers" not in data:
            data["providers"] = {}
            modified = True
            
        # Providers to migrate
        provider_keys = ["chatanywhere", "deepl", "google", "gemini", "openai", "kira", "gemini_tts", "elevenlabs"]
        
        for key in provider_keys:
            if key in data:
                # Kira is now elevenlabs
                target_key = key
                if target_key not in data["providers"]:
                    data["providers"][target_key] = data[key]
                del data[key]
                modified = True
                
        # Rename tts_provider to speech_provider
        if "tts_provider" in data:
            tts_val = data["tts_provider"]
            if tts_val == "Edge TTS":
                data["speech_provider"] = "edge"
            elif tts_val == "Kira":
                data["speech_provider"] = "elevenlabs"
            else:
                data["speech_provider"] = tts_val.lower()
            del data["tts_provider"]
            modified = True
            
        # Ensure llm_provider exists
        if "llm_provider" not in data:
            data["llm_provider"] = "chatanywhere"
            modified = True
            
        # Normalize translation_provider
        if "translation_provider" in data:
            data["translation_provider"] = data["translation_provider"].lower()
            modified = True
            
        if modified:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                
    except Exception as e:
        print(f"Failed to migrate settings: {e}")
