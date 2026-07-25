with open('frontend/ui/settings/speech_widgets.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_lang_code = '        self.lang_edit = QLineEdit("en-US")'
new_lang_code = '''        self.lang_edit = QComboBox()
        self.lang_edit.setEditable(True)
        languages = [
            "Auto Detect", "Vietnamese (vi-VN)", "English (en-US)", 
            "Japanese (ja-JP)", "Korean (ko-KR)", "Chinese Simplified (zh-CN)", 
            "Chinese Traditional (zh-TW)", "French (fr-FR)", "German (de-DE)", 
            "Spanish (es-ES)", "Portuguese (pt-BR)", "Russian (ru-RU)", 
            "Thai (th-TH)", "Indonesian (id-ID)"
        ]
        self.lang_edit.addItems(languages)
        self.lang_edit.setCurrentText("English (en-US)")'''
text = text.replace(old_lang_code, new_lang_code)

old_load_lang = '        self.lang_edit.setText(conf.get("language", "en-US"))'
new_load_lang = '        self.lang_edit.setCurrentText(conf.get("language", "English (en-US)"))'
text = text.replace(old_load_lang, new_load_lang)

old_save_lang = '            "language": self.lang_edit.text(),'
new_save_lang = '            "language": self.lang_edit.currentText(),'
text = text.replace(old_save_lang, new_save_lang)

old_preview_lang = '            self.lang_edit.text(),'
new_preview_lang = '            self.lang_edit.currentText(),'
text = text.replace(old_preview_lang, new_preview_lang)

with open('frontend/ui/settings/speech_widgets.py', 'w', encoding='utf-8') as f:
    f.write(text)
