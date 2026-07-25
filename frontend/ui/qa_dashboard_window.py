from backend.services.localization_service import LocalizationService

loc = LocalizationService()

import os
import json
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt

class QADashboardWindow(QWidget):
    def __init__(self, project_dir: str):
        super().__init__()
        self.project_dir = project_dir
        self.report_path = os.path.join(self.project_dir, "logs", "qa_report.json")
        self.init_ui()
        self.load_report()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Summary Header
        self.summary_label = QLabel(loc.translate("msg_loading_qa"))
        self.summary_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.summary_label)
        
        # Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([loc.translate("col_severity"), loc.translate("col_rule"), loc.translate("col_target"), loc.translate("col_message")])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        # Bottom controls
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton(loc.translate("btn_refresh"))
        self.refresh_btn.clicked.connect(self.load_report)
        
        self.resume_btn = QPushButton(loc.translate("btn_resume_pipeline"))
        self.resume_btn.setStyleSheet("background-color: #10B981; color: white; font-weight: bold;")
        self.resume_btn.clicked.connect(self.resume_pipeline)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.resume_btn)
        
        layout.addLayout(btn_layout)

    def load_report(self):
        self.table.setRowCount(0)
        if not os.path.exists(self.report_path):
            self.summary_label.setText(loc.translate("msg_no_qa_report"))
            return
            
        try:
            with open(self.report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
                
            crit = report.get("critical_count", 0)
            err = report.get("error_count", 0)
            warn = report.get("warning_count", 0)
            fixed = report.get("fixed_count", 0)
            
            self.summary_label.setText(f"QA Summary: {crit} Critical | {err} Errors | {warn} Warnings ({fixed} Auto-Fixed)")
            
            issues = report.get("issues", [])
            for issue in issues:
                # Skip auto-fixed ones in the main view, or just show them in gray
                if issue.get("auto_fixed"):
                    continue
                    
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                sev = issue.get("severity", "")
                rule = issue.get("rule_name", "")
                msg = issue.get("message", "")
                target = ""
                
                if issue.get("character_id"):
                    target = f"Character: {issue.get('character_id')}"
                elif issue.get("segment_id") is not None:
                    target = f"Segment {issue.get('segment_id')}"
                    
                self.table.setItem(row, 0, QTableWidgetItem(sev))
                self.table.setItem(row, 1, QTableWidgetItem(rule))
                self.table.setItem(row, 2, QTableWidgetItem(target))
                self.table.setItem(row, 3, QTableWidgetItem(msg))
                
        except Exception as e:
            self.summary_label.setText(f"Error loading report: {str(e)}")

    def resume_pipeline(self):
        # We check if there are still critical issues
        if not os.path.exists(self.report_path):
            self.close()
            return
            
        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
            if report.get("critical_count", 0) > 0:
                QMessageBox.warning(self, loc.translate("msg_cannot_resume"), loc.translate("msg_resolve_critical"))
                return
                
        # If clear, we can trigger desktop_app's resume
        QMessageBox.information(self, loc.translate("lbl_ready"), "All critical issues resolved. You can now resume the pipeline from the main window.")
        self.close()
