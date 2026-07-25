import codecs
with codecs.open('backend/tts/tts_provider.py', 'r', 'utf-8') as f:
    text = f.read()

capcut_branch = '''        elif provider_type == "CapCut TTS":
            from backend.providers.tts.capcut_provider import CapCutProvider
            return CapCutProvider(config_path="config/providers/capcut.json")
'''

if 'elif provider_type == "CapCut TTS":' not in text:
    text = text.replace('        else:\n            from backend.tts.edge_tts_provider', capcut_branch + '        else:\n            from backend.tts.edge_tts_provider')
    with codecs.open('backend/tts/tts_provider.py', 'w', 'utf-8') as f:
        f.write(text)
    print('Patched TTSProviderFactory')
else:
    print('TTSProviderFactory already patched')
