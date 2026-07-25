import re
with open('frontend/ui/settings_window.py', 'r', encoding='utf-8') as f:
    text = f.read()

print('speech_provider:', re.findall(r'"speech_provider"', text))
print('tts_provider:', re.findall(r'"tts_provider"', text))
