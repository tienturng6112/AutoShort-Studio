import os
import re

files = [
    'desktop_app.py',
    'frontend/ui/settings_window.py',
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

strings = set()
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            text = file.read()
            # simple regex to grab literal strings in quotes
            # we also want to look for things like QLabel("..."), QPushButton("..."), setWindowTitle("...")
            matches = re.findall(r'(?:setWindowTitle|setText|QLabel|QPushButton|QAction|QMessageBox\.(?:warning|information|critical|question))\([\'"]([^\'"]+)[\'"]', text)
            for m in matches:
                strings.add(m)
    except Exception as e:
        print(f"Error reading {f}: {e}")

for s in sorted(list(strings)):
    if len(s) > 1 and not s.startswith('#'):
        print(s)
