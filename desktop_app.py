import sys
import os
import subprocess
import json

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,
    QTextEdit, QFileDialog, QMessageBox, QGroupBox, QRadioButton,
    QFrame, QSplitter, QStackedWidget, QStatusBar, QListWidget
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QShortcut, QAction, QKeySequence, QIcon

from frontend.workspace.workspace_manager import WorkspaceManager
from backend.services.localization_service import LocalizationService

loc = LocalizationService()

from backend.services.queue_service import QueueService
from backend.services.recovery_service import RecoveryService
from backend.services.project_repository import ProjectRepository

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(loc.translate("app_window_title"))
        self.resize(1100, 700)
        self.project_dir = ""
        
        self.init_ui()
        self.apply_styles()
        
        self.update_ui_text()
        
        # Initialize Services
        self.queue_service = QueueService()
        self.queue_service.signals.project_output.connect(self.read_queue_output)
        self.queue_service.signals.project_finished.connect(self.queue_pipeline_finished)
        self.queue_service.signals.queue_updated.connect(self.update_queue_ui)
        self.queue_service.start()
        
        self.recovery_service = RecoveryService()
        self.check_recovery()

        # Keyboard shortcuts
        self.setup_shortcuts()
        
        wm = WorkspaceManager.get_instance()
        wm.language_changed.connect(self.retranslate_ui)

    def apply_styles(self):
        style_path = os.path.join(os.path.dirname(__file__), "frontend", "ui", "styles", "fluent.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            print("Stylesheet not found at", style_path)

    def init_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Toolbar
        self.init_top_toolbar(main_layout)

        # 2. Main Horizontal Splitter (Sidebar + Workspace + Provider Status)
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter, 1)

        # 3. Left Sidebar
        self.init_left_sidebar()
        self.main_splitter.addWidget(self.sidebar_widget)

        # 4. Main Workspace (StackedWidget)
        self.workspace_stack = QStackedWidget()
        self.main_splitter.addWidget(self.workspace_stack)

        # 5. Right Panel (Provider Status)
        self.init_right_panel()
        self.main_splitter.addWidget(self.right_panel)

        # Set default splitter sizes
        self.main_splitter.setSizes([200, 700, 200])

        # 6. Bottom Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_project = QLabel(loc.translate("lbl_ready"))
        self.status_queue = QLabel(loc.translate("status_queue").format(count=0))
        self.status_cpu = QLabel(loc.translate("status_cpu").format(usage="--"))
        self.status_ram = QLabel(loc.translate("status_ram").format(usage="--"))
        
        self.status_bar.addWidget(self.status_project)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.status_queue)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.status_cpu)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.status_ram)

        # Initialize Home Dashboard (Index 0)
        self.init_home_dashboard()
        
        # Load Workspace state (restore pages dynamically via WorkspaceManager)
        # Note: WorkspaceManager should now use self.workspace_stack
        WorkspaceManager.get_instance().set_main_workspace(self.workspace_stack)
        self.restore_layout_state()

    def init_top_toolbar(self, parent_layout):
        self.toolbar_widget = QWidget()
        self.toolbar_widget.setObjectName("TopToolbar")
        toolbar_layout = QHBoxLayout(self.toolbar_widget)
        toolbar_layout.setContentsMargins(15, 10, 15, 10)
        
        # Logo / Title
        self.title_label = QLabel(loc.translate("app_title"))
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4F46E5;")
        
        # Buttons
        self.btn_tb_open = QPushButton(loc.translate("tb_open"))
        self.btn_tb_recent = QPushButton(loc.translate("tb_recent"))
        self.btn_tb_settings = QPushButton(loc.translate("nav_settings"))
        self.btn_tb_settings.clicked.connect(lambda: self.switch_page("settings"))
        self.btn_tb_lang = QPushButton(loc.translate("tb_language"))
        self.btn_tb_theme = QPushButton(loc.translate("tb_theme"))

        toolbar_layout.addWidget(self.title_label)
        toolbar_layout.addSpacing(20)
        toolbar_layout.addWidget(self.btn_tb_open)
        toolbar_layout.addWidget(self.btn_tb_recent)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_tb_settings)
        toolbar_layout.addWidget(self.btn_tb_lang)
        toolbar_layout.addWidget(self.btn_tb_theme)
        
        parent_layout.addWidget(self.toolbar_widget)

    def init_left_sidebar(self):
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(5)

        self.nav_buttons = {}
        nav_items = [
            ("home", loc.translate("nav_home")),
            ("projects", loc.translate("nav_projects")),
            ("settings", loc.translate("nav_settings"))
        ]

        for key, text in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            if key == "home":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, k=key: self.switch_page(k))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        sidebar_layout.addStretch()
        
        self.btn_collapse = QPushButton(loc.translate("nav_collapse"))
        sidebar_layout.addWidget(self.btn_collapse)

    def init_right_panel(self):
        self.right_panel = QWidget()
        self.right_panel.setObjectName("Sidebar")
        rp_layout = QVBoxLayout(self.right_panel)
        rp_layout.setContentsMargins(10, 20, 10, 20)
        
        self.lbl_provider_status = QLabel(loc.translate("status_provider"))
        self.lbl_provider_status.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        rp_layout.addWidget(self.lbl_provider_status)
        
        # Mock Provider Cards for now
        providers = ["ChatAnywhere", "Edge TTS", "ElevenLabs"]
        for p in providers:
            card = QFrame()
            card.setProperty("class", "Card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 10, 10, 10)
            
            lbl_name = QLabel(p)
            lbl_name.setStyleSheet("font-weight: 600;")
            lbl_status = QLabel(loc.translate("lbl_ready"))
            lbl_status.setStyleSheet("color: #059669; font-size: 11px;")
            
            card_layout.addWidget(lbl_name)
            card_layout.addWidget(lbl_status)
            rp_layout.addWidget(card)
            
        rp_layout.addStretch()

    def init_home_dashboard(self):
        self.home_page = QWidget()
        home_layout = QVBoxLayout(self.home_page)
        home_layout.setContentsMargins(40, 40, 40, 40)
        
        # Header
        self.home_title = QLabel(loc.translate("app_title"))
        self.home_title.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 5px;")
        self.home_subtitle = QLabel(loc.translate("window_subtitle"))
        self.home_subtitle.setStyleSheet("color: #6B7280; font-size: 14px; margin-bottom: 20px;")
        
        home_layout.addWidget(self.home_title)
        home_layout.addWidget(self.home_subtitle)
        
        # Main Layout (Input + Quick Actions)
        content_layout = QHBoxLayout()
        
        # Left side: Input Area
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 20, 0)
        
        # Source Group
        self.input_group = QGroupBox(loc.translate("grp_input_source"))
        grp_layout = QVBoxLayout(self.input_group)
        
        row1 = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText(loc.translate("placeholder_input"))
        self.browse_btn = QPushButton(loc.translate("btn_browse"))
        self.browse_btn.clicked.connect(self.browse_file)
        row1.addWidget(self.input_edit)
        row1.addWidget(self.browse_btn)
        grp_layout.addLayout(row1)
        
        lang_layout = QHBoxLayout()
        self.src_combo = QComboBox()
        self.target_combo = QComboBox()
        
        self.languages = [
            (loc.translate("lang_auto"), "auto"),
            (loc.translate("lang_en"), "en"),
            (loc.translate("lang_vi"), "vi"),
            (loc.translate("lang_es"), "es"),
            (loc.translate("lang_fr"), "fr"),
            (loc.translate("lang_de"), "de"),
            (loc.translate("lang_ja"), "ja"),
            (loc.translate("lang_ko"), "ko"),
            (loc.translate("lang_zh"), "zh"),
            (loc.translate("lang_it"), "it"),
            (loc.translate("lang_ru"), "ru"),
            (loc.translate("lang_ar"), "ar"),
            (loc.translate("lang_hi"), "hi")
        ]
        
        for name, code in self.languages:
            self.src_combo.addItem(name, code)
            if code != "auto":
                self.target_combo.addItem(name, code)
                
        self.target_combo.setCurrentIndex(1) # Default to VI
        
        self.lbl_source = QLabel(loc.translate("lbl_source"))
        lang_layout.addWidget(self.lbl_source)
        lang_layout.addWidget(self.src_combo)
        self.lbl_target = QLabel(loc.translate("lbl_target"))
        lang_layout.addWidget(self.lbl_target)
        lang_layout.addWidget(self.target_combo)
        grp_layout.addLayout(lang_layout)
        
        input_layout.addWidget(self.input_group)
        
        # Output Mode
        self.out_group = QGroupBox(loc.translate("grp_output_mode"))
        out_layout = QHBoxLayout(self.out_group)
        self.mode_sub_voice = QRadioButton(loc.translate("mode_sub_voice"))
        self.mode_sub_only = QRadioButton(loc.translate("mode_sub_only"))
        self.mode_voice_only = QRadioButton(loc.translate("mode_voice_only"))
        self.mode_sub_audio = QRadioButton(loc.translate("mode_sub_audio"))
        
        self.mode_sub_voice.setChecked(True)
        out_layout.addWidget(self.mode_sub_voice)
        out_layout.addWidget(self.mode_sub_only)
        out_layout.addWidget(self.mode_voice_only)
        out_layout.addWidget(self.mode_sub_audio)
        
        input_layout.addWidget(self.out_group)
        
        # Start & Pause Buttons Layout
        btn_action_layout = QHBoxLayout()
        self.start_btn = QPushButton(loc.translate("btn_start_translation"))
        self.start_btn.setProperty("class", "Primary")
        self.start_btn.clicked.connect(self.start_pipeline)
        
        self.pause_btn = QPushButton(loc.translate("btn_pause", "Pause"))
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause_pipeline)
        
        btn_action_layout.addWidget(self.start_btn, stretch=1)
        btn_action_layout.addWidget(self.pause_btn)
        input_layout.addLayout(btn_action_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_label = QLabel(loc.translate("lbl_ready"))
        input_layout.addWidget(self.progress_label)
        input_layout.addWidget(self.progress_bar)
        
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        input_layout.addWidget(self.log_viewer)
        
        content_layout.addWidget(input_container, 2)
        
        # Right side: Quick Actions & Recent
        quick_container = QWidget()
        quick_layout = QVBoxLayout(quick_container)
        
        self.lbl_recent = QLabel(loc.translate("lbl_recent_projects"))
        self.lbl_recent.setStyleSheet("font-weight: bold; font-size: 14px;")
        quick_layout.addWidget(self.lbl_recent)
        
        self.recent_list = QListWidget()
        self.recent_list.setStyleSheet("border: 1px solid #E5E7EB; border-radius: 6px;")
        quick_layout.addWidget(self.recent_list)
        
        self.lbl_actions = QLabel(loc.translate("lbl_quick_actions"))
        self.lbl_actions.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 15px;")
        quick_layout.addWidget(self.lbl_actions)
        
        self.btn_new = QPushButton(loc.translate("btn_new_project"))
        self.btn_open = QPushButton(loc.translate("btn_open_folder"))
        self.btn_logs = QPushButton(loc.translate("btn_open_logs"))
        self.btn_open.clicked.connect(self.open_output_folder)
        
        quick_layout.addWidget(self.btn_new)
        quick_layout.addWidget(self.btn_open)
        quick_layout.addWidget(self.btn_logs)
        
        content_layout.addWidget(quick_container, 1)
        
        home_layout.addLayout(content_layout)
        
        self.workspace_stack.addWidget(self.home_page)
        
        self.load_output_mode()

    def switch_page(self, key):
        # Update sidebar selection
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
            
        if key == "home":
            self.workspace_stack.setCurrentWidget(self.home_page)
            return
            
        # For other keys, ask WorkspaceManager to load the page
        WorkspaceManager.get_instance().show_window(key, project_dir=self.project_dir)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(lambda: self.switch_page("home"))
        QShortcut(QKeySequence("Ctrl+,"), self).activated.connect(lambda: self.switch_page("settings"))
        # Ctrl+O, Ctrl+S, Ctrl+Shift+C etc can be mapped later

    def retranslate_ui(self):
        loc = LocalizationService()
        self.setWindowTitle(loc.translate("app_window_title"))
        self.title_label.setText(loc.translate("app_title"))
        self.btn_tb_open.setText(loc.translate("tb_open"))
        self.btn_tb_recent.setText(loc.translate("tb_recent"))
        self.btn_tb_settings.setText(loc.translate("nav_settings"))
        self.btn_tb_lang.setText(loc.translate("tb_language"))
        self.btn_tb_theme.setText(loc.translate("tb_theme"))
        
        self.btn_collapse.setText(loc.translate("nav_collapse") if self.nav_buttons["home"].text() != "" else ">")
        
        # Repopulate nav
        nav_keys = ["home", "projects", "settings"]
        nav_translations = [
            loc.translate("nav_home"), loc.translate("nav_projects"),
            loc.translate("nav_settings")
        ]
        if self.nav_buttons["home"].text() != "":
            for k, t in zip(nav_keys, nav_translations):
                self.nav_buttons[k].setText(t)

        
        self.home_title.setText(loc.translate("app_title"))
        self.home_subtitle.setText(loc.translate("window_subtitle"))
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

        
        self.input_group.setTitle(loc.translate("grp_input_source"))
        self.input_edit.setPlaceholderText(loc.translate("placeholder_input"))
        self.browse_btn.setText(loc.translate("btn_browse"))
        
        self.lbl_source.setText(loc.translate("lbl_source"))
        self.lbl_target.setText(loc.translate("lbl_target"))
        
        self.out_group.setTitle(loc.translate("grp_output_mode"))
        self.mode_sub_voice.setText(loc.translate("mode_sub_voice"))
        self.mode_sub_only.setText(loc.translate("mode_sub_only"))
        self.mode_voice_only.setText(loc.translate("mode_voice_only"))
        self.mode_sub_audio.setText(loc.translate("mode_sub_audio"))
        
        self.start_btn.setText(loc.translate("btn_start_translation"))
        self.progress_label.setText(loc.translate("lbl_ready"))
        
        # Repopulate language names
        for i in range(self.src_combo.count()):
            code = self.src_combo.itemData(i)
            if code:
                self.src_combo.setItemText(i, loc.translate(f"lang_{code}"))
        for i in range(self.target_combo.count()):
            code = self.target_combo.itemData(i)
            if code:
                self.target_combo.setItemText(i, loc.translate(f"lang_{code}"))
            
    def update_ui_text(self):
        self.retranslate_ui()

    def browse_file(self):
        filter_str = "Video Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.m4v *.ts *.wmv);;All Files (*.*)"
        file, _ = QFileDialog.getOpenFileName(self, loc.translate("title_select_video", "Select Video File"), "", filter_str)
        if file:
            import os
            norm_file = os.path.normpath(file)
            if os.path.exists(norm_file) and os.access(norm_file, os.R_OK):
                self.input_edit.setText(norm_file)
            else:
                self.input_edit.setText(file)

    def toggle_pause_pipeline(self):
        if not hasattr(self, 'pause_btn'):
            return
        current_text = self.pause_btn.text()
        if current_text in ["Pause", loc.translate("btn_pause", "Pause")]:
            self.queue_service.pause_queue()
            self.pause_btn.setText(loc.translate("btn_resume", "Resume"))
            self.log_viewer.append("[System] Processing paused.")
            self.progress_label.setText(loc.translate("status_paused", "Paused"))
        else:
            self.queue_service.resume_queue()
            self.pause_btn.setText(loc.translate("btn_pause", "Pause"))
            self.log_viewer.append("[System] Processing resumed.")

    def check_recovery(self):
        import os
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return
        uncompleted = self.recovery_service.detect_interrupted_projects()
        if uncompleted:
            latest = uncompleted[0]
            reply = QMessageBox.question(self, loc.translate("title_recover_project"), f"Project '{latest}' was not finished. Resume?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.resume_project_id = latest
                self.start_pipeline()
                
    def start_pipeline(self):
        input_val = self.input_edit.text().strip()
        is_resume = hasattr(self, 'resume_project_id') and self.resume_project_id is not None
        
        if not input_val and not is_resume:
            QMessageBox.warning(self, loc.translate("msg_warning"), loc.translate("msg_specify_input"))
            return

        if input_val and not is_resume and not (input_val.startswith("http://") or input_val.startswith("https://")):
            import os
            if not os.path.exists(input_val):
                QMessageBox.warning(self, loc.translate("msg_warning", "Warning"), f"File not found:\n{input_val}")
                return
            if not os.access(input_val, os.R_OK):
                QMessageBox.warning(self, loc.translate("msg_warning", "Warning"), f"File cannot be read:\n{input_val}")
                return

        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.pause_btn.setText(loc.translate("btn_pause", "Pause"))
        self.browse_btn.setEnabled(False)
        self.input_edit.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.progress_label.setText(loc.translate("status_queuing"))
        self.log_viewer.clear()
        
        repo = ProjectRepository()
        
        if is_resume:
            project_id = self.resume_project_id
            self.resume_project_id = None
        else:
            import time
            from backend.models.project_models import ProjectMetadata, ProjectSnapshot
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            project_id = f"proj_{timestamp}"
            
            mode = "Subtitle + Voice"
            if self.mode_sub_only.isChecked(): mode = "Subtitle Only"
            elif self.mode_voice_only.isChecked(): mode = "Voice Only"
            elif self.mode_sub_audio.isChecked(): mode = "Subtitle + Audio Files"
            
            wm = WorkspaceManager.get_instance()
            settings_page = wm._pages.get("settings")
            if not settings_page:
                from frontend.ui.settings_window import SettingsWindow
                settings_page = SettingsWindow()
                wm._pages["settings"] = settings_page
            
            selected_voice = ""
            active_provider = settings_page._state.speech_provider
            active_widget = settings_page.speech_widgets.get(active_provider)
            if active_widget and hasattr(active_widget, "voice_combo"):
                selected_voice = active_widget.voice_combo.currentData() or active_widget.voice_combo.currentText() or ""
            
            if not selected_voice:
                selected_voice = settings_page.global_voice_combo.currentData() or ""
                
            snapshot = ProjectSnapshot(output_mode=mode, global_voice=selected_voice)
            
            project = ProjectMetadata(
                project_id=project_id,
                project_name=f"Project {timestamp}",
                created_at=time.time(),
                modified_at=time.time(),
                input_video=input_val,
                settings_snapshot=snapshot,
                languages={
                    "source": self.src_combo.currentData(),
                    "target": self.target_combo.currentData()
                }
            )
            repo.save(project)
            
        self.log_viewer.append(f"[System] Enqueuing project {project_id}...")
        self.queue_service.enqueue(project_id)

    def read_queue_output(self, project_id, text):
        self.log_viewer.append(f"[{project_id}] {text}")
        if "Stage 1" in text or "Video Import" in text:
            self.progress_bar.setValue(10)
            self.progress_label.setText("Stage 1: Video Import")
        elif "Stage 2" in text or "Extracting audio" in text or "Audio Extraction" in text:
            self.progress_bar.setValue(20)
            self.progress_label.setText(loc.translate("msg_extracting_audio", "Stage 2: Audio Extraction"))
        elif "Stage 3" in text or "Transcribing" in text or "Speech Recognition" in text:
            self.progress_bar.setValue(35)
            self.progress_label.setText(loc.translate("msg_transcribing", "Stage 3: Speech Recognition"))
        elif "Stage 4" in text or "Translating" in text or "Translation" in text:
            self.progress_bar.setValue(55)
            self.progress_label.setText(loc.translate("msg_translating", "Stage 4: Translation"))
        elif "Stage 5" in text or "Timeline Alignment" in text:
            self.progress_bar.setValue(70)
            self.progress_label.setText("Stage 5: Timeline Alignment")
        elif "Stage 6" in text or "Synthesizing" in text or "Voice Synthesis" in text:
            self.progress_bar.setValue(85)
            self.progress_label.setText(loc.translate("msg_synthesizing", "Stage 6: Voice Synthesis"))
        elif "Stage 7" in text or "Export" in text:
            self.progress_bar.setValue(95)
            self.progress_label.setText("Stage 7: Export")
        elif "Stage 8" in text or "Render" in text or "Stitching" in text:
            self.progress_bar.setValue(100)
            self.progress_label.setText(loc.translate("msg_stitching", "Stage 8: Render"))

    def queue_pipeline_finished(self, project_id, exit_code):
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText(loc.translate("btn_pause", "Pause"))
        self.browse_btn.setEnabled(True)
        self.input_edit.setEnabled(True)
        
        if exit_code == 0:
            self.progress_bar.setValue(100)
            self.progress_label.setText(loc.translate("msg_finished_successfully"))
            import os
            if not os.environ.get("PYTEST_CURRENT_TEST"):
                QMessageBox.information(self, loc.translate("msg_success"), loc.translate("msg_video_complete"))
        else:
            self.progress_label.setText(loc.translate("msg_failed"))
            import os
            if not os.environ.get("PYTEST_CURRENT_TEST"):
                QMessageBox.critical(self, loc.translate("msg_error"), loc.translate("msg_pipeline_failed").format(code=exit_code))

    def update_queue_ui(self):
        pass

    def open_output_folder(self):
        projects_dir = os.path.abspath('projects')
        if os.path.exists(projects_dir):
            if sys.platform == 'win32':
                os.startfile(projects_dir)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', projects_dir])
            else:
                subprocess.Popen(['xdg-open', projects_dir])

    def load_output_mode(self):
        settings_path = "config/workspace.json"
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    mode = data.get("output_mode", "Sub & Voice")
                    if mode == "Sub & Voice":
                        self.mode_sub_voice.setChecked(True)
                    elif mode == "Sub Only":
                        self.mode_sub_only.setChecked(True)
                    elif mode == "Voice Only":
                        self.mode_voice_only.setChecked(True)
                    elif mode == "Sub + Audio":
                        self.mode_sub_audio.setChecked(True)
            except Exception: pass


    def closeEvent(self, event):
        if hasattr(self, "queue_service") and self.queue_service:
            try:
                self.queue_service.stop()
            except Exception:
                pass
        wm = WorkspaceManager.get_instance()
        geom = self.geometry()
        wm._layout_data['mainwindow_geom'] = [geom.x(), geom.y(), geom.width(), geom.height()]
        wm._layout_data['splitter_state'] = self.main_splitter.sizes()
        wm._flush_save()
        super().closeEvent(event)

    def restore_layout_state(self):
        wm = WorkspaceManager.get_instance()
        if 'mainwindow_geom' in wm._layout_data:
            geom = wm._layout_data['mainwindow_geom']
            try:
                if isinstance(geom, (list, tuple)) and len(geom) == 4:
                    from PySide6.QtCore import QRect
                    from PySide6.QtWidgets import QApplication
                    
                    target_rect = QRect(*geom)
                    screens = QApplication.screens()
                    is_valid = any(screen.geometry().intersects(target_rect) for screen in screens)
                    
                    if is_valid:
                        self.setGeometry(*geom)
                    else:
                        self.resize(1100, 700)
                        self.move(100, 100)
                else:
                    self.resize(1100, 700)
                    self.move(100, 100)
            except Exception:
                self.resize(1100, 700)
                self.move(100, 100)
        if 'splitter_state' in wm._layout_data:
            try:
                self.main_splitter.setSizes(wm._layout_data['splitter_state'])
            except Exception: pass


if __name__ == '__main__':
    import traceback
    try:
        from backend.core.migration import migrate_settings
        import os
        migrate_settings(os.path.join("config", "settings.json"))
        
        # --- Provider Registration Validation ---
        import inspect
        from backend.providers.translation.manager import TranslationProviderManager
        from backend.providers.speech.manager import SpeechProviderManager
        from backend.providers.llm.manager import LLMProviderManager
        
        print("=== STARTING PROVIDER LIFECYCLE VALIDATION ===")
        startup_errors = []
        
        # 1. Validate Translation
        validation_manager = TranslationProviderManager()
        providers_to_validate = ["chatanywhere", "deepl"]
        
        class MockLLMService:
            def __init__(self):
                class MockManager:
                    def get(self, provider_id):
                        return None
                self._manager = MockManager()
            async def chat(self, *args, **kwargs):
                return "OK"
                
        mock_llm = MockLLMService()
        dummy_settings = {
            "chatanywhere": {"api_key": "dummy", "base_url": "http://dummy"},
            "deepl": {"api_key": "dummy"},
            "elevenlabs": {"api_key": "dummy"}
        }
        
        for pid in providers_to_validate:
            try:
                p = validation_manager.create_provider(pid, dummy_settings, mock_llm)
                if inspect.isabstract(p.__class__):
                    startup_errors.append(f"Translation Provider {pid} class {p.__class__.__name__} is abstract (missing abstract methods).")
                count = sum(1 for x in validation_manager.list() if x == pid)
                if count != 1:
                    startup_errors.append(f"Translation Provider {pid} registered {count} times.")
            except Exception as e:
                startup_errors.append(f"Failed to create Translation Provider {pid}: {str(e)}")

        # 2. Validate Speech
        speech_manager = SpeechProviderManager()
        speech_providers = ["elevenlabs", "edge"]
        for pid in speech_providers:
            try:
                p = speech_manager.create_provider(pid, dummy_settings)
                if inspect.isabstract(p.__class__):
                    startup_errors.append(f"Speech Provider {pid} class {p.__class__.__name__} is abstract (missing abstract methods).")
                count = sum(1 for x in speech_manager.list() if x == pid)
                if count != 1:
                    startup_errors.append(f"Speech Provider {pid} registered {count} times.")
            except Exception as e:
                startup_errors.append(f"Failed to create Speech Provider {pid}: {str(e)}")

        # 3. Validate LLM
        llm_manager = LLMProviderManager()
        llm_providers = ["llm"]
        for pid in llm_providers:
            try:
                p = llm_manager.create_provider(pid, dummy_settings)
                if inspect.isabstract(p.__class__):
                    startup_errors.append(f"LLM Provider {pid} class {p.__class__.__name__} is abstract (missing abstract methods).")
                count = sum(1 for x in llm_manager.list() if x == pid)
                if count != 1:
                    startup_errors.append(f"LLM Provider {pid} registered {count} times.")
            except Exception as e:
                startup_errors.append(f"Failed to create LLM Provider {pid}: {str(e)}")

        if startup_errors:
            print("\nPROVIDER VALIDATION FAILED:")
            for err in startup_errors:
                print(f"- {err}")
            sys.exit(1)
        else:
            print("All providers validated successfully (Concrete, Unique, Creatable, Activated).\n")
            
        app = QApplication(sys.argv)
        
        import qasync
        import asyncio
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        window = MainWindow()
        window.show()
        
        with loop:
            loop.run_forever()
    except Exception as e:
        print("Startup Failed:\n")
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
