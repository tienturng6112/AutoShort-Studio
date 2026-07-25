import re
with open('backend/run_pipeline.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('if tts_type == "gemini_tts":', 'if tts_type == "gemini":')
text = text.replace('from backend.providers.speech.gemini_tts.gemini_tts_provider import GeminiTTSProvider', 'from backend.providers.speech.gemini.provider import GeminiSpeechProvider')
text = text.replace('config = settings.get("providers", {}).get("gemini_tts", {})', 'config = settings.get("providers", {}).get("gemini", {})')
text = text.replace('tts_provider = GeminiTTSProvider(api_key=config.get("api_key"), cache_dir=os.path.join(project_dir, "cache", "speech"))', 'tts_provider = GeminiSpeechProvider(api_key=config.get("api_key"), cache_dir=os.path.join(project_dir, "cache", "speech"))')

with open('backend/run_pipeline.py', 'w', encoding='utf-8') as f:
    f.write(text)
