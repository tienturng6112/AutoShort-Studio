import os
import shutil

def replace_in_file(filepath, old, new):
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    if old in text:
        text = text.replace(old, new)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)

replace_in_file('backend/run_pipeline.py', '"characters.json"', '"data/characters.json"')
replace_in_file('backend/services/project_service.py', '"characters.json"', '"data/characters.json"')
replace_in_file('frontend/ui/settings_window.py', '"characters.json"', '"data/characters.json"')
replace_in_file('frontend/workspace/workspace_manager.py', '"characters.json"', '"data/characters.json"')

replace_in_file('frontend/ui/settings_window.py', '"resources/voices/clones"', '"data/voices/clones"')
replace_in_file('backend/providers/tts/omnivoice_provider.py', '"resources/voices/clones"', '"data/voices/clones"')

if os.path.exists('resources/voices/clones'):
    if not os.path.exists('data/voices'):
        os.makedirs('data/voices')
    if not os.path.exists('data/voices/clones'):
        shutil.move('resources/voices/clones', 'data/voices/clones')

print('Paths replaced.')
