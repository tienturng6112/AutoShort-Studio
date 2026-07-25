import os
import json
import time
from typing import List, Dict, Any
from backend.speech.models import Transcript
from backend.qa.models import QAReport, QAIssue, QAContext, QASeverity, BaseQARule
from backend.qa.rules import get_core_rules

class QAManager:
    def __init__(self):
        self.rules: List[BaseQARule] = get_core_rules()

    def register_rule(self, rule: BaseQARule):
        self.rules.append(rule)

    def run(self, project_id: str, transcript: Transcript, settings: dict, characters: dict, cap_manager=None) -> QAReport:
        start_time = time.time()
        context = QAContext(
            project_id=project_id,
            transcript=transcript,
            settings=settings,
            characters=characters,
            capabilities=cap_manager
        )
        
        all_issues: List[QAIssue] = []
        
        # Evaluate rules
        for rule in self.rules:
            issues = rule.evaluate(context)
            all_issues.extend(issues)
            
        # Attempt Auto-Fix
        for rule in self.rules:
            rule_issues = [i for i in all_issues if i.rule_name == rule.name]
            if rule_issues:
                rule.fix(context, rule_issues)
                
        # Tally stats
        report = QAReport(project_id=project_id, issues=all_issues)
        for issue in all_issues:
            report.total_issues += 1
            if issue.auto_fixed:
                report.fixed_count += 1
            
            if issue.severity == QASeverity.CRITICAL:
                report.critical_count += 1
            elif issue.severity == QASeverity.ERROR:
                report.error_count += 1
            elif issue.severity == QASeverity.WARNING:
                report.warning_count += 1
                
        report.execution_time_ms = (time.time() - start_time) * 1000
        return report

    def export(self, report: QAReport, export_path: str):
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
