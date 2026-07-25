import re

with open('frontend/ui/settings_window.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Inject save_status_label in init_ui
init_anchor = '''        self.cancel_btn = QPushButton(loc.translate("btn_cancel"))
        self.cancel_btn.clicked.connect(self.close)'''
        
init_code = '''        self.cancel_btn = QPushButton(loc.translate("btn_cancel"))
        self.cancel_btn.clicked.connect(self.close)
        
        self.save_status_label = QLabel("")'''

if 'self.save_status_label = QLabel' not in text:
    text = text.replace(init_anchor, init_code)

layout_anchor = '''        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)'''
        
layout_code = '''        btn_layout.addWidget(self.save_status_label)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)'''
        
if 'btn_layout.addWidget(self.save_status_label)' not in text:
    text = text.replace(layout_anchor, layout_code)

# 2. Update save_settings
old_save = '''            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
            self.close()
        except Exception as e:
            QMessageBox.critical(self, loc.translate("msg_save_error"), f"Failed to save settings: {str(e)}")'''
            
new_save = '''            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
            
            self.save_status_label.setText("<font color='green'>✓ Settings saved successfully.</font>")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2500, self.save_status_label.clear)
        except Exception as e:
            QMessageBox.critical(self, loc.translate("msg_save_error"), f"Failed to save settings: {str(e)}")'''

if old_save in text:
    text = text.replace(old_save, new_save)
    
with open('frontend/ui/settings_window.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Settings UX patched.")
