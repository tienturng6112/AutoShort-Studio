import codecs
with codecs.open('desktop_app.py', 'r', 'utf-8') as f:
    text = f.read()

if 'QLabel("Recent Projects")' in text:
    print('Recent Projects STILL hardcoded!')
    text = text.replace('lbl_recent = QLabel("Recent Projects")', 'self.lbl_recent = QLabel(loc.translate("lbl_recent_projects"))')
    text = text.replace('quick_layout.addWidget(lbl_recent)', 'quick_layout.addWidget(self.lbl_recent)')
if 'QLabel("Quick Actions")' in text:
    print('Quick Actions STILL hardcoded!')
    text = text.replace('lbl_actions = QLabel("Quick Actions")', 'self.lbl_actions = QLabel(loc.translate("lbl_quick_actions"))')
    text = text.replace('quick_layout.addWidget(lbl_actions)', 'quick_layout.addWidget(self.lbl_actions)')
if 'btn_new = QPushButton("New Project")' in text:
    print('New Project STILL hardcoded!')
    text = text.replace('btn_new = QPushButton("New Project")', 'self.btn_new = QPushButton(loc.translate("btn_new_project"))')
    text = text.replace('quick_layout.addWidget(btn_new)', 'quick_layout.addWidget(self.btn_new)')
if 'btn_open = QPushButton("Open Folder")' in text:
    print('Open Folder STILL hardcoded!')
    text = text.replace('btn_open = QPushButton("Open Folder")', 'self.btn_open = QPushButton(loc.translate("btn_open_folder"))')
    text = text.replace('btn_open.clicked.connect(', 'self.btn_open.clicked.connect(')
    text = text.replace('quick_layout.addWidget(btn_open)', 'quick_layout.addWidget(self.btn_open)')
if 'btn_logs = QPushButton("Open Logs")' in text:
    print('Open Logs STILL hardcoded!')
    text = text.replace('btn_logs = QPushButton("Open Logs")', 'self.btn_logs = QPushButton(loc.translate("btn_open_logs"))')
    text = text.replace('quick_layout.addWidget(btn_logs)', 'quick_layout.addWidget(self.btn_logs)')

if 'QLabel("Ready")' in text:
    text = text.replace('self.status_project = QLabel("Ready")', 'self.status_project = QLabel(loc.translate("lbl_ready"))')
if 'QLabel("Queue: 0")' in text:
    text = text.replace('self.status_queue = QLabel("Queue: 0")', 'self.status_queue = QLabel(loc.translate("status_queue").format(count=0))')
if 'QLabel("CPU: --%")' in text:
    text = text.replace('self.status_cpu = QLabel("CPU: --%")', 'self.status_cpu = QLabel(loc.translate("status_cpu").format(usage="--"))')
if 'QLabel("RAM: --MB")' in text:
    text = text.replace('self.status_ram = QLabel("RAM: --MB")', 'self.status_ram = QLabel(loc.translate("status_ram").format(usage="--"))')
if 'QLabel("Provider Status")' in text:
    text = text.replace('self.lbl_provider_status = QLabel("Provider Status")', 'self.lbl_provider_status = QLabel(loc.translate("status_provider"))')

with codecs.open('desktop_app.py', 'w', 'utf-8') as f:
    f.write(text)
print('Double checked translations')
