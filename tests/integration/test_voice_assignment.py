import os
import json
import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from backend.services.project_repository import ProjectRepository
from backend.models.project_models import ProjectMetadata, ProjectSnapshot
from desktop_app import MainWindow

@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    
@pytest.fixture
def temp_project_dir(tmp_path):
    project_id = "test_voice_assignment"
    repo = ProjectRepository()
    
    project_dir = repo.get_project_dir(project_id)
    
    # Create mock aligned transcript
    sub_dir = os.path.join(project_dir, "subtitle")
    os.makedirs(sub_dir, exist_ok=True)
    
    with open(os.path.join(sub_dir, "aligned_transcript.json"), "w", encoding="utf-8") as f:
        json.dump({
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "Hello", "speaker_id": "Speaker_A"},
                {"start": 1.5, "end": 2.5, "text": "World", "speaker_id": "Speaker_B"}
            ]
        }, f)
        
    # Create mock project.json
    with open(repo.get_project_file_path(project_id), "w", encoding="utf-8") as f:
        json.dump({
            "project_id": project_id,
            "settings_snapshot": {"output_mode": "Subtitle + Voice"}
        }, f)
        
    yield project_id, project_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(project_dir, ignore_errors=True)
    if os.path.exists(repo.get_project_file_path(project_id)):
        os.remove(repo.get_project_file_path(project_id))

@patch("desktop_app.QMessageBox.exec")
@patch("desktop_app.QMessageBox.warning")
@patch("desktop_app.MainWindow.open_settings")
def test_preflight_validation_multiple_voices(mock_open_settings, mock_warning, mock_exec, temp_project_dir, tmp_path):
    project_id, base_path = temp_project_dir
    
    window = MainWindow()
    window.resume_project_id = project_id
    
    # Set settings with MULTI voice mode and missing voices
    os.makedirs("config", exist_ok=True)
    with open("config/settings.json", "w", encoding="utf-8") as f:
        json.dump({
            "voice_mode": "MULTI",
            "speaker_voices": {"Speaker_A": "alloy"} # Missing Speaker_B
        }, f)
        
    window.start_pipeline()
    
    # Should show warning because Speaker_B is unconfigured
    assert mock_exec.called

@patch("desktop_app.QMessageBox.exec")
@patch("desktop_app.QMessageBox.warning")
@patch("backend.services.queue_service.QueueService.enqueue")
def test_preflight_validation_single_voice(mock_enqueue, mock_warning, mock_exec, temp_project_dir, tmp_path):
    project_id, base_path = temp_project_dir
    
    window = MainWindow()
    window.resume_project_id = project_id
    
    # Set settings with SINGLE voice mode but missing individual speaker mapping
    os.makedirs("config", exist_ok=True)
    with open("config/settings.json", "w", encoding="utf-8") as f:
        json.dump({
            "voice_mode": "SINGLE",
            "global_voice": "alloy",
            "speaker_voices": {} # Missing mapping shouldn't matter in SINGLE mode
        }, f)
        
    window.start_pipeline()
    
    # Should NOT show warning, should proceed to enqueue
    assert not mock_warning.called
    assert mock_enqueue.called
    assert mock_enqueue.call_args[0][0] == project_id
