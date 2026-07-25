with open('backend/providers/speech/gemini/provider.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('Connected, but no audio-capable models found.', 'This API endpoint does not expose speech-capable models for your API key.')

with open('backend/providers/speech/gemini/provider.py', 'w', encoding='utf-8') as f:
    f.write(text)
