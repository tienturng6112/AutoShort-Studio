with open('frontend/ui/settings/speech_widgets.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_test_run = '''        try:
            prov = GeminiSpeechProvider(api_key=self.api_key)'''
new_test_run = '''        try:
            key = self.api_key
            if not key:
                import json, os
                try:
                    with open(os.path.join("config", "settings.json"), "r") as f:
                        key = json.load(f).get("providers", {}).get("gemini", {}).get("api_key", "")
                except Exception: pass
            prov = GeminiSpeechProvider(api_key=key)'''
text = text.replace(old_test_run, new_test_run)

old_prev_run = '''        try:
            prov = GeminiSpeechProvider(api_key=self.api_key)'''
new_prev_run = '''        try:
            key = self.api_key
            if not key:
                import json, os
                try:
                    with open(os.path.join("config", "settings.json"), "r") as f:
                        key = json.load(f).get("providers", {}).get("gemini", {}).get("api_key", "")
                except Exception: pass
            prov = GeminiSpeechProvider(api_key=key)'''
text = text.replace(old_prev_run, new_prev_run)

with open('frontend/ui/settings/speech_widgets.py', 'w', encoding='utf-8') as f:
    f.write(text)
