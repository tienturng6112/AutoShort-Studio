import re
with open('frontend/ui/settings_window.py', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'self\.tts_provider_combo\.setCurrentText.*', text)
if match: print('load:', match.group(0))

match = re.search(r'data\["speech_provider"\].*', text)
if match: print('save:', match.group(0))
