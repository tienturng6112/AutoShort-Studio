import re

with open('frontend/ui/settings/speech_widgets.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add capabilities_label underneath model_layout
old_model_layout = '''        model_layout.addWidget(self.model_combo, 1)
        model_layout.addWidget(self.refresh_model_btn)'''
new_model_layout = '''        model_layout.addWidget(self.model_combo, 1)
        model_layout.addWidget(self.refresh_model_btn)
        self.capabilities_label = QLabel()
        self.capabilities_label.setStyleSheet("color: gray; font-size: 11px;")'''
text = text.replace(old_model_layout, new_model_layout)

# 2. Add capabilities_label to form
old_form_model = '''        form.addRow(loc.translate("lbl_model", "Model:"), model_layout)'''
new_form_model = '''        form.addRow(loc.translate("lbl_model", "Model:"), model_layout)
        form.addRow("", self.capabilities_label)'''
text = text.replace(old_form_model, new_form_model)

# 3. Store capabilities in self
old_init = '''        self.api_key_edit.setEchoMode(QLineEdit.Password)'''
new_init = '''        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.capabilities_map = {}'''
text = text.replace(old_init, new_init)

# 4. Bind combobox index change to update capabilities
old_combo = '''        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)'''
new_combo = '''        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)'''
text = text.replace(old_combo, new_combo)

# 5. Method _on_model_changed
on_model_changed = '''    def _on_model_changed(self, text):
        caps = self.capabilities_map.get(text, [])
        if caps:
            self.capabilities_label.setText(" ".join(f"✓ {c}" for c in caps))
        else:
            self.capabilities_label.setText("")

    def _on_test_finished'''
text = text.replace('    def _on_test_finished', on_model_changed)

# 6. Update capabilities_map in test_finished and refresh_finished
text = text.replace('models = res.get(\'models\', [])', 'models = res.get(\'models\', []); self.capabilities_map.update(res.get(\'capabilities\', {}))')
text = text.replace('models = res.get("models", [])', 'models = res.get("models", []); self.capabilities_map.update(res.get(\'capabilities\', {}))')

with open('frontend/ui/settings/speech_widgets.py', 'w', encoding='utf-8') as f:
    f.write(text)
