import codecs

with codecs.open('frontend/ui/settings_window.py', 'r', 'utf-8') as f:
    text = f.read()

bad_patch = """        # ElevenLabs config
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

good_patch = """                    # ElevenLabs config
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

text = text.replace(bad_patch, good_patch)

bad_save_patch = """
        if hasattr(self, 'kira_base_url_edit'):
            settings["kira"]["base_url"] = self.kira_base_url_edit.text().strip()
            
        if hasattr(self, 'el_api_key_edit'):
            settings["elevenlabs"] = {
                "api_key": self.el_api_key_edit.text().strip(),
                "model": self.el_model_combo.currentText().strip()
            }
"""

good_save_patch = """
            if hasattr(self, 'kira_base_url_edit'):
                settings["kira"]["base_url"] = self.kira_base_url_edit.text().strip()
                
            if hasattr(self, 'el_api_key_edit'):
                settings["elevenlabs"] = {
                    "api_key": self.el_api_key_edit.text().strip(),
                    "model": self.el_model_combo.currentText().strip()
                }
"""

text = text.replace(bad_save_patch, good_save_patch)

with codecs.open('frontend/ui/settings_window.py', 'w', 'utf-8') as f:
    f.write(text)

print('Settings fixed!')
