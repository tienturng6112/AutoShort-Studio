with open('desktop_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
replacement = '''if __name__ == '__main__':
    import traceback
    try:
        from backend.core.migration import migrate_settings
        import os
        migrate_settings(os.path.join("config", "settings.json"))
        
        app = QApplication(sys.argv)'''

text = re.sub(r"if __name__ == '__main__':\n    import traceback\n    try:\n        app = QApplication\(sys\.argv\)", replacement, text)

with open('desktop_app.py', 'w', encoding='utf-8') as f:
    f.write(text)
