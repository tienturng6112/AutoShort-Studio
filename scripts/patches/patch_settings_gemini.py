import re

with open('frontend/ui/settings_window.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add import
if 'GeminiSpeechSettingsWidget' not in text:
    text = text.replace('from frontend.ui.settings.translation_widgets import (', 
        'from frontend.ui.settings.speech_widgets import GeminiSpeechSettingsWidget\nfrom frontend.ui.settings.translation_widgets import (')

# 2. Add widget instantiation
insertion = '''        self.gemini_speech_widget = GeminiSpeechSettingsWidget()
        prov_layout.addWidget(self.gemini_speech_widget)
        
        self.elevenlabs_group = QGroupBox'''

text = text.replace('        self.elevenlabs_group = QGroupBox', insertion)

# 3. Add to load_settings
load_insertion = '''                    self.el_api_key_edit.setText(data.get("providers", {}).get("elevenlabs", {}).get("api_key", ""))
                    self.gemini_speech_widget.load_config(data.get("providers", {}).get("gemini", {}))
'''
text = re.sub(r'                    self\.el_api_key_edit\.setText\(data\.get\(\"providers\", \{\}\)\.get\(\"elevenlabs\", \{\}\)\.get\(\"api_key\", \"\"\)\)\n?', load_insertion, text)

# 4. Add to save_settings
save_insertion = '''            data["providers"]["elevenlabs"] = {
                "api_key": self.el_api_key_edit.text(),
                "model": self.el_model_combo.currentText()
            }
            data["providers"]["gemini"] = self.gemini_speech_widget.save_config()
'''
text = re.sub(r'            data\[\"providers\"\]\[\"elevenlabs\"\] = \{\n                \"api_key\": self\.el_api_key_edit\.text\(\),\n                \"model\": self\.el_model_combo\.currentText\(\)\n            \}\n?', save_insertion, text)

with open('frontend/ui/settings_window.py', 'w', encoding='utf-8') as f:
    f.write(text)
