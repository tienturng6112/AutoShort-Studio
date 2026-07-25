import sys
import pytest
from PySide6.QtWidgets import QApplication
from unittest.mock import Mock

from backend.models.project_models import ProjectMetadata, ExecutionState
from frontend.dialogs.recovery_dialog import RecoveryDialog

app = QApplication.instance() or QApplication(sys.argv)

def test_recovery_dialog_attribute_protection():
    # 1. Project with video (canonical field)
    p1 = ProjectMetadata(
        project_id="test1",
        project_name="With Video",
        created_at=100.0,
        modified_at=200.0,
        input_video="http://youtube.com/watch?v=123"
    )
    p1.execution_state.current_stage = "Stage 1"
    
    # 2. Project without video
    p2 = ProjectMetadata(
        project_id="test2",
        project_name="Without Video",
        created_at=100.0,
        modified_at=200.0
    )
    # 3. Old project format (Mocking an object without some fields)
    class OldProject:
        project_id = "test3"
        project_name = "Old Project"
        video_source = "C:/old/video.mp4"
        updated_at = "2023-10-01T12:00:00Z"
        execution_state = type('OldState', (), {'current_stage': 'Stage 3'})()
        
    p3 = OldProject()
    
    # 4. Interrupted project (Missing state)
    class InterruptedProject:
        project_id = "test4"
        # Missing project_name
        # Missing video_source / input_video
        # Missing updated_at / modified_at
        # Missing execution_state
        pass
        
    p4 = InterruptedProject()
    
    # 5. Migrated project
    p5 = ProjectMetadata(
        project_id="test5",
        project_name="Migrated",
        created_at=100.0,
        modified_at=200.0
    )
    # delete input_video attribute to simulate partial migration
    delattr(p5, 'input_video')

    projects = [p1, p2, p3, p4, p5]
    
    mock_recovery = Mock()
    mock_queue = Mock()
    
    # Should not raise AttributeError
    dialog = RecoveryDialog(projects, mock_recovery, mock_queue)
    
    # Verify counts
    assert dialog.list_widget.count() == 5
    
    # We can briefly verify display text
    text1 = dialog.list_widget.item(0).text()
    assert "http://youtube.com/watch?v=123" in text1
    
    text4 = dialog.list_widget.item(3).text()
    assert "Không rõ" in text4 or "Unknown" in text4
