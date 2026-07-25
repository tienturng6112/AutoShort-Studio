import codecs
with codecs.open('desktop_app.py', 'r', 'utf-8') as f:
    text = f.read()

text = text.replace('providers = ["ChatAnywhere", "Edge TTS", "ElevenLabs", "Kira AI"]', 'providers = ["ChatAnywhere", "Edge TTS", "ElevenLabs", "Kira AI", "CapCut TTS"]')

with codecs.open('desktop_app.py', 'w', 'utf-8') as f:
    f.write(text)
print('Patched desktop_app.py Provider Panel')
