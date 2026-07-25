import os
import time
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox
from backend.services.recovery_service import RecoveryService
from backend.services.queue_service import QueueService
from backend.services.project_repository import ProjectRepository
from backend.services.localization_service import LocalizationService

loc = LocalizationService()


class RecoveryDialog(QDialog):
    def __init__(self, interrupted_projects, recovery_service, queue_service, parent=None):
        super().__init__(parent)
        self.interrupted_projects = interrupted_projects
        self.recovery_service = recovery_service
        self.queue_service = queue_service
        
        self.loc = LocalizationService()
        self.setWindowTitle(self.loc.translate("recovery_title"))
        self.setMinimumWidth(500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        info_label = QLabel(self.loc.translate("recovery_info"))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self.list_widget = QListWidget()
        for p in self.interrupted_projects:
            video_name = ""
            input_video = getattr(p, "input_video", getattr(p, "video_source", ""))
            if input_video:
                if input_video.startswith("http"):
                    video_name = input_video
                else:
                    video_name = os.path.basename(input_video)
            else:
                video_name = self.loc.translate("unknown")
                
            exec_state = getattr(p, "execution_state", None)
            stage = getattr(exec_state, "current_stage", "") if exec_state else ""
            if not stage:
                stage = self.loc.translate("unknown")
            
            modified_time = getattr(p, "modified_at", None)
            updated_at = getattr(p, "updated_at", None)
            
            time_str = self.loc.translate("unknown")
            if modified_time is not None:
                try:
                    import datetime
                    dt = datetime.datetime.fromtimestamp(modified_time)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
            elif updated_at is not None:
                try:
                    import datetime
                    dt = datetime.datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
                
            display_text = f"{getattr(p, 'project_name', self.loc.translate('unknown'))}\n" \
                           f"• {self.loc.translate('recovery_video')}: {video_name}\n" \
                           f"• {self.loc.translate('recovery_stage')}: {stage}\n" \
                           f"• {self.loc.translate('recovery_modified')}: {time_str}"
            self.list_widget.addItem(display_text)
            
        layout.addWidget(self.list_widget)
        
        if len(self.interrupted_projects) == 1:
            self.list_widget.setCurrentRow(0)
            
        btn_layout = QHBoxLayout()
        
        self.resume_btn = QPushButton(self.loc.translate("recovery_resume"))
        resume_btn.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 6px;")
        self.resume_btn.clicked.connect(self.resume_selected)
        
        restart_btn = QPushButton(self.loc.translate("recovery_restart"))
        restart_btn.setStyleSheet("padding: 6px;")
        restart_btn.clicked.connect(self.restart_selected)
        
        self.cancel_btn = QPushButton(self.loc.translate("recovery_cancel"))
        cancel_btn.setStyleSheet("padding: 6px;")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.resume_btn)
        btn_layout.addWidget(restart_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
    def resume_selected(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        project = self.interrupted_projects[row]
        self.recovery_service.recover_project(project.project_id)
        self.queue_service.enqueue(project.project_id)
        msg = self.loc.translate("recovery_queued_resume").format(project.project_name)
        QMessageBox.information(self, self.loc.translate("recovered"), msg)
        self.accept()
        
    def restart_selected(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        project = self.interrupted_projects[row]
        # Restart means resetting pipeline state
        project.pipeline_state = {k: False for k in project.pipeline_state.keys()}
        project.execution_state.progress_percent = 0
        project.execution_state.current_stage = ""
        project.execution_state.status = "Waiting"
        self.recovery_service.repository.save(project)
        self.queue_service.enqueue(project.project_id)
        msg = self.loc.translate("recovery_queued_restart").format(project.project_name)
        QMessageBox.information(self, self.loc.translate("restarted"), msg)
        self.accept()
