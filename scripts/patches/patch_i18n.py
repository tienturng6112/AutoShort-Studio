import codecs
import json

new_en = {
    "capcut_config": "CapCut TTS Configuration",
    "lbl_enable": "Enable CapCut TTS",
    "default_voice": "Default Voice"
}

new_vi = {
    "capcut_config": "Cấu hình CapCut TTS",
    "lbl_enable": "Kích hoạt CapCut TTS",
    "default_voice": "Giọng mặc định"
}

for lang, new_data in [('en', new_en), ('vi', new_vi)]:
    path = f'resources/i18n/{lang}.json'
    with codecs.open(path, 'r', 'utf-8') as f:
        data = json.load(f)
    for k, v in new_data.items():
        data[k] = v
    with codecs.open(path, 'w', 'utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
print('Updated dictionary with CapCut strings.')
