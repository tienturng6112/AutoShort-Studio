import codecs
import json

with codecs.open('frontend/ui/settings_window.py', 'r', 'utf-8') as f:
    text = f.read()

# 1. Add capcut_group UI to init_ui
capcut_ui = '''        
        self.capcut_group = QGroupBox(loc.translate("capcut_config"))
        self.capcut_layout = QFormLayout()
        self.capcut_enabled_cb = QCheckBox(loc.translate("lbl_enable"))
        self.capcut_base_url = QLineEdit()
        self.capcut_default_voice = QLineEdit()
        self.capcut_default_speed = QLineEdit("1.0")
        self.capcut_test_btn = QPushButton(loc.translate("test_connection"))
        self.capcut_test_btn.clicked.connect(self.test_capcut_connection)
        self.capcut_status_label = QLabel(loc.translate("status_idle"))
        self.capcut_layout.addRow(self.capcut_enabled_cb)
        self.capcut_layout.addRow(loc.translate("base_url") + ":", self.capcut_base_url)
        self.capcut_layout.addRow(loc.translate("default_voice") + ":", self.capcut_default_voice)
        self.capcut_layout.addRow(loc.translate("speed") + ":", self.capcut_default_speed)
        ctest_layout = QHBoxLayout()
        ctest_layout.addWidget(self.capcut_test_btn)
        ctest_layout.addWidget(self.capcut_status_label)
        self.capcut_layout.addRow(ctest_layout)
        self.capcut_group.setLayout(self.capcut_layout)
        prov_layout.addWidget(self.capcut_group)
'''
if 'self.capcut_group =' not in text:
    text = text.replace('prov_layout.addWidget(self.edge_tts_group)', 'prov_layout.addWidget(self.edge_tts_group)\n' + capcut_ui)

# 2. Add update_ui_text for capcut
capcut_ui_text = '''
        if hasattr(self, 'capcut_group'):
            self.capcut_group.setTitle(loc.translate("capcut_config"))
            self.capcut_enabled_cb.setText(loc.translate("lbl_enable"))
            if self.capcut_layout.labelForField(self.capcut_base_url):
                self.capcut_layout.labelForField(self.capcut_base_url).setText(loc.translate("base_url") + ":")
            if self.capcut_layout.labelForField(self.capcut_default_voice):
                self.capcut_layout.labelForField(self.capcut_default_voice).setText(loc.translate("default_voice") + ":")
            if self.capcut_layout.labelForField(self.capcut_default_speed):
                self.capcut_layout.labelForField(self.capcut_default_speed).setText(loc.translate("speed") + ":")
            self.capcut_test_btn.setText(loc.translate("test_connection"))
'''
if 'self.capcut_group.setTitle' not in text:
    text = text.replace('self.kira_group.setTitle(loc.translate("kira_config"))', 'self.kira_group.setTitle(loc.translate("kira_config"))\n' + capcut_ui_text)

# 3. Add load_settings logic
capcut_load = '''
                    # CapCut config
                    capcut_path = os.path.join("config", "providers", "capcut.json")
                    if os.path.exists(capcut_path) and hasattr(self, 'capcut_enabled_cb'):
                        try:
                            with open(capcut_path, "r", encoding="utf-8") as f:
                                cdata = json.load(f)
                                self.capcut_enabled_cb.setChecked(cdata.get("enabled", False))
                                self.capcut_base_url.setText(cdata.get("base_url", "https://api.capcut.com/tts/v1"))
                                self.capcut_default_voice.setText(cdata.get("default_voice", "default"))
                                self.capcut_default_speed.setText(str(cdata.get("default_speed", 1.0)))
                        except Exception:
                            pass
'''
if 'capcut_path = os.path.join' not in text:
    text = text.replace('el_config = data.get("elevenlabs", {})', capcut_load + '\n                    el_config = data.get("elevenlabs", {})')

# 4. Add save_settings logic
capcut_save = '''
            # Save CapCut config
            capcut_path = os.path.join("config", "providers", "capcut.json")
            if hasattr(self, 'capcut_enabled_cb'):
                os.makedirs(os.path.dirname(capcut_path), exist_ok=True)
                cdata = {}
                if os.path.exists(capcut_path):
                    try:
                        with open(capcut_path, "r", encoding="utf-8") as f:
                            cdata = json.load(f)
                    except Exception: pass
                
                cdata["enabled"] = self.capcut_enabled_cb.isChecked()
                cdata["base_url"] = self.capcut_base_url.text()
                cdata["default_voice"] = self.capcut_default_voice.text()
                try:
                    cdata["default_speed"] = float(self.capcut_default_speed.text())
                except ValueError:
                    cdata["default_speed"] = 1.0
                    
                with open(capcut_path, "w", encoding="utf-8") as f:
                    json.dump(cdata, f, indent=4, ensure_ascii=False)
'''
if '# Save CapCut config' not in text:
    text = text.replace('with open(settings_path, "w", encoding="utf-8") as f:', capcut_save + '\n            with open(settings_path, "w", encoding="utf-8") as f:')

# 5. Add test_capcut_connection method
capcut_test_method = '''
    def test_capcut_connection(self):
        self.capcut_status_label.setText(loc.translate("status_testing"))
        import asyncio
        from backend.providers.tts.capcut_provider import CapCutProvider
        try:
            # Re-read from UI values directly for test
            provider = CapCutProvider()
            provider._enabled = self.capcut_enabled_cb.isChecked()
            provider._base_url = self.capcut_base_url.text()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(provider.test_connection())
            loop.close()
            
            if success:
                self.capcut_status_label.setText("<font color='green'>" + loc.translate("status_connected") + "</font>")
            else:
                self.capcut_status_label.setText("<font color='red'>" + loc.translate("status_failed") + "</font>")
        except Exception as e:
            self.capcut_status_label.setText("<font color='red'>Error: " + str(e) + "</font>")
'''
if 'def test_capcut_connection' not in text:
    text += '\n' + capcut_test_method

with codecs.open('frontend/ui/settings_window.py', 'w', 'utf-8') as f:
    f.write(text)
print('Patched settings_window.py for CapCut')
