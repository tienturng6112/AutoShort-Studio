import json
import codecs

new_en = {
    'status_queue': 'Queue: {count}',
    'status_cpu': 'CPU: {usage}%',
    'status_ram': 'RAM: {usage}MB',
    'status_provider': 'Provider Status',
    'lbl_recent_projects': 'Recent Projects',
    'lbl_quick_actions': 'Quick Actions',
    'btn_new_project': 'New Project',
    'btn_open_folder': 'Open Folder',
    'btn_open_logs': 'Open Logs',
    'lbl_ready': 'Ready'
}

new_vi = {
    'status_queue': 'Hàng đợi: {count}',
    'status_cpu': 'CPU: {usage}%',
    'status_ram': 'RAM: {usage}MB',
    'status_provider': 'Trạng thái API',
    'lbl_recent_projects': 'Dự án gần đây',
    'lbl_quick_actions': 'Thao tác nhanh',
    'btn_new_project': 'Dự án mới',
    'btn_open_folder': 'Mở thư mục',
    'btn_open_logs': 'Mở nhật ký',
    'lbl_ready': 'Sẵn sàng'
}

for lang, new_data in [('en', new_en), ('vi', new_vi)]:
    path = f'resources/i18n/{lang}.json'
    with codecs.open(path, 'r', 'utf-8') as f:
        data = json.load(f)
    for k, v in new_data.items():
        data[k] = v
    with codecs.open(path, 'w', 'utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
print('Updated dictionary with dashboard strings.')

with codecs.open('desktop_app.py', 'r', 'utf-8') as f:
    text = f.read()

# Replace hardcoded strings
text = text.replace('QLabel("Ready")', 'QLabel(loc.translate("lbl_ready"))')
text = text.replace('QLabel("Queue: 0")', 'QLabel(loc.translate("status_queue").format(count=0))')
text = text.replace('QLabel("CPU: --%")', 'QLabel(loc.translate("status_cpu").format(usage="--"))')
text = text.replace('QLabel("RAM: --MB")', 'QLabel(loc.translate("status_ram").format(usage="--"))')
text = text.replace('QLabel("Provider Status")', 'QLabel(loc.translate("status_provider"))')
text = text.replace('QLabel("Recent Projects")', 'QLabel(loc.translate("lbl_recent_projects"))')
text = text.replace('QLabel("Quick Actions")', 'QLabel(loc.translate("lbl_quick_actions"))')
text = text.replace('QPushButton("New Project")', 'QPushButton(loc.translate("btn_new_project"))')
text = text.replace('QPushButton("Open Folder")', 'QPushButton(loc.translate("btn_open_folder"))')
text = text.replace('QPushButton("Open Logs")', 'QPushButton(loc.translate("btn_open_logs"))')

# Add missing retrans updates
retrans_add = '''
        self.status_project.setText(loc.translate("lbl_ready"))
        self.status_queue.setText(loc.translate("status_queue").format(count=0))
        self.status_cpu.setText(loc.translate("status_cpu").format(usage="--"))
        self.status_ram.setText(loc.translate("status_ram").format(usage="--"))
        self.lbl_provider_status.setText(loc.translate("status_provider"))
        self.lbl_recent.setText(loc.translate("lbl_recent_projects"))
        self.lbl_actions.setText(loc.translate("lbl_quick_actions"))
        self.btn_new.setText(loc.translate("btn_new_project"))
        self.btn_open.setText(loc.translate("btn_open_folder"))
        self.btn_logs.setText(loc.translate("btn_open_logs"))
'''
text = text.replace('self.home_subtitle.setText(loc.translate("window_subtitle"))', 'self.home_subtitle.setText(loc.translate("window_subtitle"))' + retrans_add)

# Change local variables in init_home_dashboard to instance variables so they can be retranslated
text = text.replace('lbl_recent = QLabel(loc.translate("lbl_recent_projects"))', 'self.lbl_recent = QLabel(loc.translate("lbl_recent_projects"))')
text = text.replace('quick_layout.addWidget(lbl_recent)', 'quick_layout.addWidget(self.lbl_recent)')
text = text.replace('lbl_actions = QLabel(loc.translate("lbl_quick_actions"))', 'self.lbl_actions = QLabel(loc.translate("lbl_quick_actions"))')
text = text.replace('quick_layout.addWidget(lbl_actions)', 'quick_layout.addWidget(self.lbl_actions)')
text = text.replace('btn_new = QPushButton(loc.translate("btn_new_project"))', 'self.btn_new = QPushButton(loc.translate("btn_new_project"))')
text = text.replace('quick_layout.addWidget(btn_new)', 'quick_layout.addWidget(self.btn_new)')
text = text.replace('btn_open = QPushButton(loc.translate("btn_open_folder"))', 'self.btn_open = QPushButton(loc.translate("btn_open_folder"))')
text = text.replace('btn_open.clicked.connect(', 'self.btn_open.clicked.connect(')
text = text.replace('quick_layout.addWidget(btn_open)', 'quick_layout.addWidget(self.btn_open)')
text = text.replace('btn_logs = QPushButton(loc.translate("btn_open_logs"))', 'self.btn_logs = QPushButton(loc.translate("btn_open_logs"))')
text = text.replace('quick_layout.addWidget(btn_logs)', 'quick_layout.addWidget(self.btn_logs)')

with codecs.open('desktop_app.py', 'w', 'utf-8') as f:
    f.write(text)
print('Patched desktop_app.py with dashboard translations.')
