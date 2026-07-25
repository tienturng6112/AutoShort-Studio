import codecs
import re

with codecs.open('frontend/ui/settings_window.py', 'r', 'utf-8') as f:
    text = f.read()

# Patch load_settings
load_patch = """        # ElevenLabs config
        el_config = data.get("elevenlabs", {})
        if hasattr(self, 'el_api_key_edit'):
            self.el_api_key_edit.setText(el_config.get("api_key", ""))
            
            saved_el_model = el_config.get("model", "eleven_multilingual_v2")
            idx = self.el_model_combo.findText(saved_el_model)
            if idx != -1:
                self.el_model_combo.setCurrentIndex(idx)
            else:
                self.el_model_combo.setCurrentText(saved_el_model)
                
        # Kira base_url
        if hasattr(self, 'kira_base_url_edit'):
            self.kira_base_url_edit.setText(kira_config.get("base_url", "https://kiraai.vn/api/v1"))
"""

text = re.sub(r'        self\.kira_api_key_edit\.setText\(self\.kira_api_key\)', '        self.kira_api_key_edit.setText(self.kira_api_key)\n' + load_patch, text)

# Patch save_settings
save_patch = """
        if hasattr(self, 'kira_base_url_edit'):
            settings["kira"]["base_url"] = self.kira_base_url_edit.text().strip()
            
        if hasattr(self, 'el_api_key_edit'):
            settings["elevenlabs"] = {
                "api_key": self.el_api_key_edit.text().strip(),
                "model": self.el_model_combo.currentText().strip()
            }
"""

text = re.sub(r'            "speed": float\(self\.kira_speed_edit\.text\(\)\)\n        \}', '            "speed": float(self.kira_speed_edit.text())\n        }' + save_patch, text)

with codecs.open('frontend/ui/settings_window.py', 'w', 'utf-8') as f:
    f.write(text)
print('load/save settings patched')
