import uuid
from typing import List
from backend.qa.models import BaseQARule, QAIssue, QASeverity, QAContext

class MissingTranslationRule(BaseQARule):
    name = "Translation.Missing"

    def evaluate(self, context: QAContext) -> List[QAIssue]:
        issues = []
        for i, segment in enumerate(context.transcript.segments):
            if not segment.text_translated or segment.text_translated.strip() == "":
                issues.append(QAIssue(
                    issue_id=str(uuid.uuid4()),
                    rule_name=self.name,
                    severity=QASeverity.ERROR,
                    message=f"Segment {i} is missing translation.",
                    segment_id=i,
                    character_id=segment.speaker
                ))
        return issues
        
    def fix(self, context: QAContext, issues: List[QAIssue]) -> None:
        for issue in issues:
            if issue.severity == QASeverity.ERROR and issue.segment_id is not None:
                seg = context.transcript.segments[issue.segment_id]
                # Fallback to source text
                seg.text_translated = seg.text
                issue.auto_fixed = True
                issue.fix_description = "Fell back to original source text."

class MissingVoiceRule(BaseQARule):
    name = "Voice.Missing"

    def evaluate(self, context: QAContext) -> List[QAIssue]:
        issues = []
        # Gather all active speakers
        speakers = set(s.speaker for s in context.transcript.segments if s.speaker)
        for spk in speakers:
            char_data = context.characters.get(spk, {})
            voice_id = char_data.get("voice_id")
            if not voice_id:
                issues.append(QAIssue(
                    issue_id=str(uuid.uuid4()),
                    rule_name=self.name,
                    severity=QASeverity.CRITICAL,
                    message=f"Character '{spk}' has no voice assigned.",
                    character_id=spk
                ))
        return issues
        
    def fix(self, context: QAContext, issues: List[QAIssue]) -> None:
        for issue in issues:
            if issue.severity == QASeverity.CRITICAL and issue.character_id:
                # We do not auto-fix critical voice missing currently. Wait for user.
                pass

class SubtitleOverlapRule(BaseQARule):
    name = "Subtitle.Overlap"
    
    def evaluate(self, context: QAContext) -> List[QAIssue]:
        issues = []
        segs = context.transcript.segments
        for i in range(len(segs) - 1):
            if segs[i].end > segs[i+1].start:
                issues.append(QAIssue(
                    issue_id=str(uuid.uuid4()),
                    rule_name=self.name,
                    severity=QASeverity.ERROR,
                    message=f"Segment {i} overlaps with Segment {i+1} ({segs[i].end} > {segs[i+1].start}).",
                    segment_id=i
                ))
        return issues
        
    def fix(self, context: QAContext, issues: List[QAIssue]) -> None:
        for issue in issues:
            if issue.segment_id is not None:
                i = issue.segment_id
                segs = context.transcript.segments
                # Truncate end time to next start time
                segs[i].end = segs[i+1].start - 0.01
                issue.auto_fixed = True
                issue.fix_description = "Truncated end time to prevent overlap."

def get_core_rules() -> List[BaseQARule]:
    return [
        MissingTranslationRule(),
        MissingVoiceRule(),
        SubtitleOverlapRule()
    ]
