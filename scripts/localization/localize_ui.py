import json
import codecs

new_en = {
    'nav_home': 'Home',
    'nav_projects': 'Projects',
    'nav_translation': 'Translation',
    'nav_voice': 'Voice',
    'nav_characters': 'Characters',
    'nav_emotion': 'Emotion',
    'nav_templates': 'Templates',
    'nav_qa': 'QA',
    'nav_diagnostics': 'Diagnostics',
    'nav_settings': 'Settings',
    'nav_collapse': 'Collapse',
    'tb_open': 'Open',
    'tb_recent': 'Recent',
    'tb_language': 'Language',
    'tb_theme': 'Theme'
}

new_vi = {
    'nav_home': 'Trang chủ',
    'nav_projects': 'Dự án',
    'nav_translation': 'Dịch thuật',
    'nav_voice': 'Giọng đọc',
    'nav_characters': 'Nhân vật',
    'nav_emotion': 'Cảm xúc',
    'nav_templates': 'Mẫu dự án',
    'nav_qa': 'Chất lượng',
    'nav_diagnostics': 'Hệ thống',
    'nav_settings': 'Cài đặt',
    'nav_collapse': 'Thu gọn',
    'tb_open': 'Mở',
    'tb_recent': 'Gần đây',
    'tb_language': 'Ngôn ngữ',
    'tb_theme': 'Giao diện'
}

for lang, new_data in [('en', new_en), ('vi', new_vi)]:
    path = f'resources/i18n/{lang}.json'
    with codecs.open(path, 'r', 'utf-8') as f:
        data = json.load(f)
    for k, v in new_data.items():
        data[k] = v
    with codecs.open(path, 'w', 'utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
print('Updated dictionary with navigation strings.')

with codecs.open('desktop_app.py', 'r', 'utf-8') as f:
    text = f.read()

# Update init_top_toolbar
text = text.replace('QPushButton("Open")', 'QPushButton(loc.translate("tb_open"))')
text = text.replace('QPushButton("Recent")', 'QPushButton(loc.translate("tb_recent"))')
text = text.replace('QPushButton("Settings")', 'QPushButton(loc.translate("nav_settings"))')
text = text.replace('QPushButton("Language")', 'QPushButton(loc.translate("tb_language"))')
text = text.replace('QPushButton("Theme")', 'QPushButton(loc.translate("tb_theme"))')

# Update nav items list
nav_items_old = '''        nav_items = [
            ("home", "Home"),
            ("projects", "Projects"),
            ("translation_review", "Translation"),
            ("voices", "Voice"),
            ("characters", "Characters"),
            ("emotions", "Emotion"),
            ("templates", "Templates"),
            ("qa", "QA"),
            ("diagnostics", "Diagnostics"),
            ("settings", "Settings")
        ]'''
nav_items_new = '''        nav_items = [
            ("home", loc.translate("nav_home")),
            ("projects", loc.translate("nav_projects")),
            ("translation_review", loc.translate("nav_translation")),
            ("voices", loc.translate("nav_voice")),
            ("characters", loc.translate("nav_characters")),
            ("emotions", loc.translate("nav_emotion")),
            ("templates", loc.translate("nav_templates")),
            ("qa", loc.translate("nav_qa")),
            ("diagnostics", loc.translate("nav_diagnostics")),
            ("settings", loc.translate("nav_settings"))
        ]'''
text = text.replace(nav_items_old, nav_items_new)
text = text.replace('self.btn_collapse = QPushButton("Collapse")', 'self.btn_collapse = QPushButton(loc.translate("nav_collapse"))')
text = text.replace("self.btn_collapse.setText('Collapse')", 'self.btn_collapse.setText(loc.translate("nav_collapse"))')

# Add missing retrans
retrans_add = '''
        self.btn_tb_open.setText(loc.translate("tb_open"))
        self.btn_tb_recent.setText(loc.translate("tb_recent"))
        self.btn_tb_settings.setText(loc.translate("nav_settings"))
        self.btn_tb_lang.setText(loc.translate("tb_language"))
        self.btn_tb_theme.setText(loc.translate("tb_theme"))
        
        self.btn_collapse.setText(loc.translate("nav_collapse") if self.nav_buttons["home"].text() != "" else ">")
        
        # Repopulate nav
        nav_keys = ["home", "projects", "translation_review", "voices", "characters", "emotions", "templates", "qa", "diagnostics", "settings"]
        nav_translations = [
            loc.translate("nav_home"), loc.translate("nav_projects"), loc.translate("nav_translation"),
            loc.translate("nav_voice"), loc.translate("nav_characters"), loc.translate("nav_emotion"),
            loc.translate("nav_templates"), loc.translate("nav_qa"), loc.translate("nav_diagnostics"),
            loc.translate("nav_settings")
        ]
        if self.nav_buttons["home"].text() != "":
            for k, t in zip(nav_keys, nav_translations):
                self.nav_buttons[k].setText(t)
'''
text = text.replace('self.title_label.setText(loc.translate("app_title"))', 'self.title_label.setText(loc.translate("app_title"))' + retrans_add)

with codecs.open('desktop_app.py', 'w', 'utf-8') as f:
    f.write(text)
print('Patched desktop_app.py with translations.')
