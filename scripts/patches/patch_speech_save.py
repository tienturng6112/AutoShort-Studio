import re
with open('frontend/ui/settings_window.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update save_settings to save speech_provider instead of tts_provider
old_save = '''            "tts_provider": "Kira" if self.tts_provider_combo.currentIndex() == 1 else "Edge TTS",'''

new_save = '''            "speech_provider": self._get_speech_provider_id(),'''
text = text.replace(old_save, new_save)

# 2. Add _get_speech_provider_id helper method
helper_method = '''    def _get_speech_provider_id(self):
        text = self.tts_provider_combo.currentText()
        if "Gemini Speech" in text: return "gemini"
        if "ElevenLabs" in text: return "elevenlabs"
        if "Kira" in text: return "kira"
        if "OmniVoice" in text: return "omnivoice"
        return "edge"
        
    def _set_speech_provider_from_id(self, provider_id):
        provider_id = provider_id.lower()
        mapping = {
            "gemini": "Gemini Speech",
            "elevenlabs": "ElevenLabs",
            "kira": "Kira",
            "omnivoice": "OmniVoice (Experimental)",
            "edge": "Edge TTS"
        }
        target_text = mapping.get(provider_id, "Edge TTS")
        idx = self.tts_provider_combo.findText(target_text)
        if idx != -1:
            self.tts_provider_combo.setCurrentIndex(idx)

    def save_settings'''
text = text.replace('    def save_settings', helper_method)

# 3. Update load_settings to load speech_provider instead of tts_provider
old_load = '''                    idx = self.tts_provider_combo.findText(settings["tts_provider"])
                    if idx != -1: self.tts_provider_combo.setCurrentIndex(idx)'''
new_load = '''                    sp_prov = settings.get("speech_provider", settings.get("tts_provider", "edge"))
                    self._set_speech_provider_from_id(sp_prov)'''
text = text.replace(old_load, new_load)

# Fix the bug where load_settings tries to access settings["tts_provider"] if it exists but might be missing
text = re.sub(r'if \"tts_provider\" in settings:.*?if idx != -1: self\.tts_provider_combo\.setCurrentIndex\(idx\)', 
              '''sp_prov = settings.get("speech_provider", settings.get("tts_provider", "edge"))
                    self._set_speech_provider_from_id(sp_prov)''', text, flags=re.DOTALL)

with open('frontend/ui/settings_window.py', 'w', encoding='utf-8') as f:
    f.write(text)
