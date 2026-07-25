import re
with open('frontend/ui/settings/speech_widgets.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add QCheckBox import if not present
if 'QCheckBox' not in text:
    text = text.replace('QGroupBox', 'QGroupBox, QCheckBox')

# 1. Add Use Custom Key checkbox and toggle logic
old_api_key_init = '''        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.capabilities_map = {}'''
new_api_key_init = '''        self.use_custom_key_chk = QCheckBox("Use custom API Key")
        self.use_custom_key_chk.toggled.connect(self._on_custom_key_toggled)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setVisible(False)
        self.capabilities_map = {}'''
text = text.replace(old_api_key_init, new_api_key_init)

# Replace the api_key form layout with a horizontal layout holding both
old_form_api = '''        form.addRow(loc.translate("lbl_api_key", "API Key:"), self.api_key_edit)'''
new_form_api = '''        api_layout = QVBoxLayout()
        api_layout.addWidget(self.use_custom_key_chk)
        api_layout.addWidget(self.api_key_edit)
        form.addRow(loc.translate("lbl_api_key", "API Key:"), api_layout)'''
text = text.replace(old_form_api, new_form_api)

# 2. _on_custom_key_toggled method
method_insertion = '''    def _on_custom_key_toggled(self, checked):
        self.api_key_edit.setVisible(checked)

    def test_connection'''
text = text.replace('    def test_connection', method_insertion)

old_test_worker = '''        self.worker = GeminiTestWorker(self.api_key_edit.text())'''
text = text.replace(old_test_worker, '''        key = self.api_key_edit.text() if self.use_custom_key_chk.isChecked() else ""
        if not key:
            import json, os
            try:
                with open(os.path.join("config", "settings.json"), "r") as f:
                    key = json.load(f).get("providers", {}).get("gemini", {}).get("api_key", "")
            except Exception: pass
        self.worker = GeminiTestWorker(key)''')

old_preview_worker = '''        self.pworker = GeminiPreviewWorker(
            self.api_key_edit.text(),'''
text = text.replace(old_preview_worker, '''        key = self.api_key_edit.text() if self.use_custom_key_chk.isChecked() else ""
        if not key:
            import json, os
            try:
                with open(os.path.join("config", "settings.json"), "r") as f:
                    key = json.load(f).get("providers", {}).get("gemini", {}).get("api_key", "")
            except Exception: pass
        self.pworker = GeminiPreviewWorker(
            key,''')

old_load = '''        self.api_key_edit.setText(conf.get("api_key", ""))'''
new_load = '''        use_custom = conf.get("use_custom_key", False)
        self.use_custom_key_chk.setChecked(use_custom)
        self.api_key_edit.setVisible(use_custom)
        self.api_key_edit.setText(conf.get("api_key", ""))'''
text = text.replace(old_load, new_load)

old_save = '''            "api_key": self.api_key_edit.text(),'''
new_save = '''            "use_custom_key": self.use_custom_key_chk.isChecked(),
            "api_key": self.api_key_edit.text() if self.use_custom_key_chk.isChecked() else "",'''
text = text.replace(old_save, new_save)

with open('frontend/ui/settings/speech_widgets.py', 'w', encoding='utf-8') as f:
    f.write(text)
