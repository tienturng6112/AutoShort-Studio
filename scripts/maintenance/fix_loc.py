import codecs
import re
import os

files = [
    'frontend/ui/character_browser_window.py',
    'frontend/ui/voice_browser_window.py',
    'frontend/ui/emotion_editor_window.py',
    'frontend/ui/qa_dashboard_window.py',
    'frontend/ui/template_browser_window.py',
    'frontend/ui/provider_diagnostics_window.py',
    'frontend/ui/translation_review_window.py',
    'frontend/dialogs/project_manager_dialog.py',
    'frontend/dialogs/recovery_dialog.py'
]

for filepath in files:
    if not os.path.exists(filepath):
        continue
        
    with codecs.open(filepath, 'r', 'utf-8') as f:
        content = f.read()

    # Find the __init__ signature
    init_match = re.search(r'(def __init__\([^)]*\):)', content)
    if init_match:
        init_sig = init_match.group(1)
        
        # Check if we already injected loc
        if 'loc = LocalizationService()' not in content:
            # We inject loc = LocalizationService() right after __init__
            content = content.replace(init_sig, init_sig + '\n        loc = LocalizationService()')
            
            with codecs.open(filepath, 'w', 'utf-8') as f:
                f.write(content)
            print(f"Fixed {filepath}")
            
print("Loc inject finished")
