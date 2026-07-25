import os
import time
import subprocess
import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QMenu, QLabel, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont
from backend.services.project_repository import ProjectRepository
from backend.services.project_history_service import ProjectHistoryService
from backend.services.localization_service import LocalizationService

loc = LocalizationService()

from backend.models.project_models import ProjectMetadata

class ProjectManagerDialog(QDialog):
    def __init__(self, queue_service, parent=None):
        super().__init__(parent)
        self.setWindowTitle(loc.translate("title_project_manager"))
        self.setMinimumSize(1000, 600)
        
        self.queue_service = queue_service
        self.repository = ProjectRepository()
        self.history_service = ProjectHistoryService()
        
        self.selected_project_id = None
        self.resume_requested = False
        
        self.init_ui()
        self.load_projects()
        self.load_queue()
        
        # Refresh timer for queue
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_queue)
        self.timer.start(2000)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        
        # -----------------------------
        # Tab 1: Project Library
        # -----------------------------
        self.library_tab = QWidget()
        library_layout = QVBoxLayout(self.library_tab)
        
        self.lib_table = QTableWidget(0, 6)
        self.lib_table.setHorizontalHeaderLabels([
            "Project Name", 
            "Status", 
            "Progress", 
            "Current Stage", 
            "Last Opened", 
            "Output Mode"
        ])
        self.lib_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.lib_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.lib_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.lib_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.lib_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.lib_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.lib_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.lib_table.setSelectionMode(QTableWidget.SingleSelection)
        self.lib_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.lib_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lib_table.customContextMenuRequested.connect(self.show_library_context_menu)
        self.lib_table.itemDoubleClicked.connect(self.on_lib_double_click)
        
        library_layout.addWidget(self.lib_table)
        self.tabs.addTab(self.library_tab, loc.translate("tab_project_library"))
        
        # -----------------------------
        # Tab 2: Execution Queue
        # -----------------------------
        self.queue_tab = QWidget()
        queue_layout = QVBoxLayout(self.queue_tab)
        
        self.queue_status_label = QLabel(loc.translate("status_queue_running"))
        self.queue_status_label.setStyleSheet("font-weight: bold; color: #4F46E5; margin-bottom: 5px;")
        queue_layout.addWidget(self.queue_status_label)
        
        self.queue_table = QTableWidget(0, 4)
        self.queue_table.setHorizontalHeaderLabels([loc.translate("col_order"), loc.translate("col_project_name"), loc.translate("col_execution_status"), loc.translate("col_action")])
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.queue_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.queue_table.setSelectionMode(QTableWidget.SingleSelection)
        self.queue_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.queue_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.queue_table.customContextMenuRequested.connect(self.show_queue_context_menu)
        
        queue_layout.addWidget(self.queue_table)
        
        # Queue Controls
        q_btn_layout = QHBoxLayout()
        self.pause_q_btn = QPushButton(loc.translate("btn_pause_queue"))
        self.pause_q_btn.clicked.connect(self.toggle_queue_pause)
        q_btn_layout.addStretch()
        q_btn_layout.addWidget(self.pause_q_btn)
        queue_layout.addLayout(q_btn_layout)
        
        self.tabs.addTab(self.queue_tab, loc.translate("tab_execution_queue"))
        
        main_layout.addWidget(self.tabs)

        # Main Buttons
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton(loc.translate("refresh") or loc.translate("btn_refresh"))
        self.refresh_btn.clicked.connect(self.load_projects)
        self.refresh_btn.clicked.connect(self.load_queue)
        
        self.close_btn = QPushButton(loc.translate("btn_close") or "Close")
        self.close_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.close_btn)
        main_layout.addLayout(btn_layout)
        
    def _format_timestamp(self, ts):
        if not ts: return "Unknown"
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


    def retranslate_ui(self):
        loc = LocalizationService()
        self.setWindowTitle(loc.translate("title_project_manager"))
        if hasattr(self, 'headers'):
            self.headers = ["ID", "Status", loc.translate("col_source"), loc.translate("col_target"), "Last Modified"]
            self.table.setHorizontalHeaderLabels(self.headers)
        if hasattr(self, 'resume_btn'): self.resume_btn.setText(loc.translate("btn_resume"))
        if hasattr(self, 'delete_btn'): self.delete_btn.setText(loc.translate("btn_delete_project"))
        if hasattr(self, 'unpin_btn'): self.unpin_btn.setText(loc.translate("btn_unpin_project"))

    def load_projects(self):
        self.lib_table.setRowCount(0)
        history = self.history_service.get_history()
        pinned = self.history_service.get_pinned_projects()
        
        # Aggregate logic
        project_entries = []
        for p in pinned:
            project_entries.append((p, True))
            
        for entry in history:
            pid = entry.get("project_id")
            if pid not in pinned:
                project_entries.append((pid, False))
                
        # Also discover orphans
        all_ids = set(self.repository.list_all_project_ids())
        known_ids = {p for p, _ in project_entries}
        for pid in all_ids:
            if pid not in known_ids:
                project_entries.append((pid, False))
                
        for pid, is_pinned in project_entries:
            try:
                proj = self.repository.load(pid)
            except Exception:
                continue
                
            row = self.lib_table.rowCount()
            self.lib_table.insertRow(row)
            
            name = proj.project_name
            if is_pinned:
                name = f"📌 {name}"
                
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, proj.project_id)
            if is_pinned:
                font = QFont()
                font.setBold(True)
                name_item.setFont(font)
            
            self.lib_table.setItem(row, 0, name_item)
            self.lib_table.setItem(row, 1, QTableWidgetItem(proj.execution_state.status))
            self.lib_table.setItem(row, 2, QTableWidgetItem(f"{proj.execution_state.progress_percent}%"))
            self.lib_table.setItem(row, 3, QTableWidgetItem(proj.execution_state.current_stage))
            
            # Find last opened ts
            ts = proj.modified_at
            for h in history:
                if h.get("project_id") == pid:
                    ts = h.get("last_opened", ts)
                    break
                    
            self.lib_table.setItem(row, 4, QTableWidgetItem(self._format_timestamp(ts)))
            self.lib_table.setItem(row, 5, QTableWidgetItem(proj.settings_snapshot.output_mode))

    def load_queue(self):
        # 1. Active project (if running via queue)
        active_id = self.queue_service._current_project_id
        
        # 2. Pending queue
        pending_ids = self.queue_service.get_queue_status()
        
        # 3. All other projects (we will find recently completed/failed to show in the queue history for visibility)
        history = self.history_service.get_history()
        recent_other = []
        for h in history[:10]: # Top 10 recent
            pid = h.get("project_id")
            if pid != active_id and pid not in pending_ids:
                try:
                    proj = self.repository.load(pid)
                    if proj.execution_state.status in ["Completed", loc.translate("msg_failed"), "Paused", "Cancelled"]:
                        recent_other.append(proj)
                except Exception:
                    pass
                    
        self.queue_table.setRowCount(0)
        
        # Add Active
        if active_id:
            try:
                proj = self.repository.load(active_id)
                self._add_queue_row("Active", proj, "Running", "#3B82F6")
            except Exception:
                pass
                
        # Add Pending
        for idx, pid in enumerate(pending_ids):
            try:
                proj = self.repository.load(pid)
                self._add_queue_row(f"{idx+1}", proj, "Pending", "#6B7280")
            except Exception:
                pass
                
        # Add Recent Others
        for proj in recent_other:
            color = "#10B981" if proj.execution_state.status == "Completed" else "#EF4444"
            if proj.execution_state.status in ["Paused", "Cancelled"]: color = "#F59E0B"
            self._add_queue_row("-", proj, proj.execution_state.status, color)

        if self.queue_service.is_paused:
            self.queue_status_label.setText(loc.translate("status_queue_paused"))
            self.queue_status_label.setStyleSheet("font-weight: bold; color: #F59E0B; margin-bottom: 5px;")
            self.pause_q_btn.setText(loc.translate("btn_resume_queue"))
        else:
            self.queue_status_label.setText(loc.translate("status_queue_running"))
            self.queue_status_label.setStyleSheet("font-weight: bold; color: #10B981; margin-bottom: 5px;")
            self.pause_q_btn.setText(loc.translate("btn_pause_queue"))

    def _add_queue_row(self, order_text, proj: ProjectMetadata, status_text, color_hex):
        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)
        
        order_item = QTableWidgetItem(order_text)
        order_item.setData(Qt.UserRole, proj.project_id)
        
        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(QColor(color_hex))
        
        font = QFont()
        font.setBold(True)
        status_item.setFont(font)
        
        self.queue_table.setItem(row, 0, order_item)
        self.queue_table.setItem(row, 1, QTableWidgetItem(proj.project_name))
        self.queue_table.setItem(row, 2, status_item)
        self.queue_table.setItem(row, 3, QTableWidgetItem(f"{proj.execution_state.progress_percent}% - {proj.execution_state.current_stage}"))

    def show_library_context_menu(self, pos):
        row = self.lib_table.rowAt(pos.y())
        if row < 0: return
            
        self.lib_table.selectRow(row)
        project_id = self.lib_table.item(row, 0).data(Qt.UserRole)
        project_name = self.lib_table.item(row, 0).text().replace("📌 ", "")
        
        menu = QMenu(self)
        
        open_action = QAction(loc.translate("btn_open_configure"), self)
        open_action.triggered.connect(lambda: self.resume_project(project_id))
        
        pinned = self.history_service.get_pinned_projects()
        is_pinned = project_id in pinned
        pin_action = QAction(loc.translate("btn_unpin_project") if is_pinned else "Pin Project", self)
        pin_action.triggered.connect(lambda: self.toggle_pin(project_id, is_pinned))
        
        queue_action = QAction(loc.translate("btn_queue_for_processing"), self)
        queue_action.triggered.connect(lambda: self.queue_project(project_id))
        
        folder_action = QAction(loc.translate("btn_reveal_explorer"), self)
        folder_action.triggered.connect(lambda: self.reveal_folder(project_id))
        
        del_action = QAction(loc.translate("btn_delete_project"), self)
        del_action.triggered.connect(lambda: self.delete_project(project_id))
        
        menu.addAction(open_action)
        menu.addAction(queue_action)
        menu.addSeparator()
        menu.addAction(pin_action)
        menu.addAction(folder_action)
        menu.addSeparator()
        menu.addAction(del_action)
        
        menu.exec_(self.lib_table.viewport().mapToGlobal(pos))

    def show_queue_context_menu(self, pos):
        row = self.queue_table.rowAt(pos.y())
        if row < 0: return
        self.queue_table.selectRow(row)
        project_id = self.queue_table.item(row, 0).data(Qt.UserRole)
        
        menu = QMenu(self)
        dequeue_action = QAction(loc.translate("btn_remove_from_queue"), self)
        dequeue_action.triggered.connect(lambda: self.dequeue_project(project_id))
        
        menu.addAction(dequeue_action)
        menu.exec_(self.queue_table.viewport().mapToGlobal(pos))

    def on_lib_double_click(self, item):
        row = item.row()
        project_id = self.lib_table.item(row, 0).data(Qt.UserRole)
        self.resume_project(project_id)

    def resume_project(self, project_id):
        self.history_service.record_project_opened(project_id, time.time())
        self.selected_project_id = project_id
        self.resume_requested = True
        self.accept()
        
    def queue_project(self, project_id):
        self.queue_service.enqueue(project_id)
        self.load_queue()
        self.tabs.setCurrentIndex(1)
        
    def toggle_pin(self, project_id, is_pinned):
        if is_pinned:
            self.history_service.unpin_project(project_id)
        else:
            self.history_service.pin_project(project_id)
        self.load_projects()

    def delete_project(self, project_id):
        reply = QMessageBox.question(self, loc.translate("msg_confirm_delete"), 
                                     "Are you sure you want to permanently delete this project? This cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.repository.delete(project_id)
            self.history_service.remove_project(project_id)
            self.load_projects()
            self.load_queue()
            
    def dequeue_project(self, project_id):
        self.queue_service.dequeue(project_id)
        self.load_queue()
        
    def toggle_queue_pause(self):
        if self.queue_service.is_paused:
            self.queue_service.resume_queue()
        else:
            self.queue_service.pause_queue()
        self.load_queue()

    def reveal_folder(self, project_id):
        project_dir = self.repository.get_project_dir(project_id)
        if os.path.exists(project_dir):
            if sys.platform == "win32":
                os.startfile(project_dir)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", project_dir])
            else:
                subprocess.Popen(["xdg-open", project_dir])
