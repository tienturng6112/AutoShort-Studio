with open('frontend/ui/settings/speech_widgets.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('group = QGroupBox, QCheckBox(loc.translate("gemini_speech_config", "Gemini Speech Configuration"))', 'group = QGroupBox(loc.translate("gemini_speech_config", "Gemini Speech Configuration"))')

with open('frontend/ui/settings/speech_widgets.py', 'w', encoding='utf-8') as f:
    f.write(text)
