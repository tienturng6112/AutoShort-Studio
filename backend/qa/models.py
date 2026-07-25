from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from backend.speech.models import Transcript

class QASeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class QAIssue(BaseModel):
    issue_id: str
    rule_name: str
    severity: QASeverity
    message: str
    segment_id: Optional[int] = None
    character_id: Optional[str] = None
    auto_fixed: bool = False
    fix_description: str = ""

class QAReport(BaseModel):
    project_id: str
    total_issues: int = 0
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    fixed_count: int = 0
    issues: List[QAIssue] = []
    execution_time_ms: float = 0.0

class QAContext(BaseModel):
    project_id: str
    transcript: Transcript
    settings: Dict[str, Any]
    characters: Dict[str, Any]
    capabilities: Any = None # ProviderCapabilityManager

class BaseQARule:
    name: str = "BaseRule"
    
    def evaluate(self, context: QAContext) -> List[QAIssue]:
        """Analyzes the context and returns a list of issues found."""
        return []
        
    def fix(self, context: QAContext, issues: List[QAIssue]) -> None:
        """Attempts to auto-fix the issues it reported."""
        pass
