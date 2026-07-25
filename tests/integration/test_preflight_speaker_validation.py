import sys
import os
import json
import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication, QMessageBox

app = QApplication.instance() or QApplication(sys.argv)
from desktop_app import MainWindow
from backend.models.project_models import ProjectMetadata, ProjectSnapshot

@pytest.fixture
def mock_mainwindow():
    window = MainWindow()
    # Mock UI elements so we don't need real inputs
    window.input_edit.setText("test.mp4")
    window.resume_project_id = "test_project"
    return window

def test_preflight_validation_blocks_unconfigured_speaker(mock_mainwindow, tmp_path):
    # Setup mock project and transcript
    proj_dir = tmp_path / "projects" / "test_project" / "subtitle"
    proj_dir.mkdir(parents=True)
    
    # Create transcript with Speaker_A having 2 segments
    transcript_data = {
        "segments": [
            {"speaker_id": "Speaker_A"},
            {"speaker_id": "Speaker_A"}
        ]
    }
    with open(proj_dir / "aligned_transcript.json", "w", encoding="utf-8") as f:
        json.dump(transcript_data, f)
        
    # Create settings with no voice for Speaker_A
    settings_dir = tmp_path / "config"
    settings_dir.mkdir(parents=True)
    with open(settings_dir / "settings.json", "w", encoding="utf-8") as f:
        json.dump({"speaker_voices": {}}, f)
        
    # Mock repository
    mock_repo = Mock()
    mock_project = ProjectMetadata(project_id="test_project", project_name="Test", created_at=0, modified_at=0)
    mock_project.settings_snapshot = ProjectSnapshot(output_mode="Subtitle + Voice")
    mock_repo.load.return_value = mock_project
    
    with patch("backend.services.project_repository.ProjectRepository", return_value=mock_repo):
        with patch("os.path.abspath", return_value=str(tmp_path / "projects")):
            # Patch os.path.join and exists appropriately? 
            # Actually, start_pipeline uses os.path.exists("config/settings.json") and os.path.join("projects", ...)
            # Let's mock os.path.exists and open to redirect to our tmp_path
            
            original_exists = os.path.exists
            def mock_exists(path):
                if "aligned_transcript.json" in str(path) or "transcript.json" in str(path):
                    return original_exists(str(tmp_path / path))
                if "settings.json" in str(path):
                    return original_exists(str(tmp_path / path))
                return original_exists(path)
                
            original_open = open
            def mock_open(path, *args, **kwargs):
                if "aligned_transcript.json" in str(path) or "transcript.json" in str(path):
                    return original_open(str(tmp_path / path), *args, **kwargs)
                if "settings.json" in str(path):
                    return original_open(str(tmp_path / path), *args, **kwargs)
                return original_open(path, *args, **kwargs)

            with patch("os.path.exists", side_effect=mock_exists):
                with patch("builtins.open", side_effect=mock_open):
                    with patch.object(QMessageBox, "exec", return_value=QMessageBox.Accepted):
                        with patch.object(QMessageBox, "clickedButton", return_value=None):
                            mock_mainwindow.start_pipeline()
                            
    # Should be blocked, meaning start_btn is re-enabled and resume_project_id is NOT None
    assert mock_mainwindow.start_btn.isEnabled() == True
    assert mock_mainwindow.resume_project_id == "test_project"

def test_preflight_validation_allows_configured_speaker(mock_mainwindow, tmp_path):
    # Setup mock project and transcript
    proj_dir = tmp_path / "projects" / "test_project" / "subtitle"
    proj_dir.mkdir(parents=True)
    
    # Create transcript with Speaker_A
    transcript_data = {
        "segments": [
            {"speaker_id": "Speaker_A"}
        ]
    }
    with open(proj_dir / "aligned_transcript.json", "w", encoding="utf-8") as f:
        json.dump(transcript_data, f)
        
    # Create settings WITH voice for Speaker_A
    settings_dir = tmp_path / "config"
    settings_dir.mkdir(parents=True)
    with open(settings_dir / "settings.json", "w", encoding="utf-8") as f:
        json.dump({"speaker_voices": {"Speaker_A": "alloy"}}, f)
        
    mock_repo = Mock()
    mock_project = ProjectMetadata(project_id="test_project", project_name="Test", created_at=0, modified_at=0)
    mock_project.settings_snapshot = ProjectSnapshot(output_mode="Subtitle + Voice")
    mock_repo.load.return_value = mock_project
    
    with patch("backend.services.project_repository.ProjectRepository", return_value=mock_repo):
        original_exists = os.path.exists
        def mock_exists(path):
            if "aligned_transcript.json" in str(path) or "transcript.json" in str(path):
                return original_exists(str(tmp_path / path))
            if "settings.json" in str(path):
                return original_exists(str(tmp_path / path))
            return original_exists(path)
            
        original_open = open
        def mock_open(path, *args, **kwargs):
            if "aligned_transcript.json" in str(path) or "transcript.json" in str(path):
                return original_open(str(tmp_path / path), *args, **kwargs)
            if "settings.json" in str(path):
                return original_open(str(tmp_path / path), *args, **kwargs)
            return original_open(path, *args, **kwargs)

        with patch("os.path.exists", side_effect=mock_exists):
            with patch("builtins.open", side_effect=mock_open):
                # We mock queue_service to not actually do anything
                mock_mainwindow.queue_service = Mock()
                mock_mainwindow.start_pipeline()
                            
    # Should be allowed, meaning start_btn is disabled and resume_project_id is None
    assert mock_mainwindow.start_btn.isEnabled() == False
    assert mock_mainwindow.resume_project_id is None

def test_preflight_validation_allows_no_tts_mode(mock_mainwindow, tmp_path):
    # Setup mock project and transcript
    proj_dir = tmp_path / "projects" / "test_project" / "subtitle"
    proj_dir.mkdir(parents=True)
    
    transcript_data = {
        "segments": [{"speaker_id": "Speaker_A"}]
    }
    with open(proj_dir / "aligned_transcript.json", "w", encoding="utf-8") as f:
        json.dump(transcript_data, f)
        
    settings_dir = tmp_path / "config"
    settings_dir.mkdir(parents=True)
    with open(settings_dir / "settings.json", "w", encoding="utf-8") as f:
        json.dump({"speaker_voices": {}}, f)
        
    mock_repo = Mock()
    mock_project = ProjectMetadata(project_id="test_project", project_name="Test", created_at=0, modified_at=0)
    # NO TTS output mode
    mock_project.settings_snapshot = ProjectSnapshot(output_mode="Subtitle Only")
    mock_repo.load.return_value = mock_project
    
    with patch("backend.services.project_repository.ProjectRepository", return_value=mock_repo):
        original_exists = os.path.exists
        def mock_exists(path):
            if "aligned_transcript.json" in str(path) or "transcript.json" in str(path):
                return original_exists(str(tmp_path / path))
            if "settings.json" in str(path):
                return original_exists(str(tmp_path / path))
            return original_exists(path)
            
        original_open = open
        def mock_open(path, *args, **kwargs):
            if "aligned_transcript.json" in str(path) or "transcript.json" in str(path):
                return original_open(str(tmp_path / path), *args, **kwargs)
            if "settings.json" in str(path):
                return original_open(str(tmp_path / path), *args, **kwargs)
            return original_open(path, *args, **kwargs)

        with patch("os.path.exists", side_effect=mock_exists):
            with patch("builtins.open", side_effect=mock_open):
                mock_mainwindow.queue_service = Mock()
                mock_mainwindow.start_pipeline()
                            
    # Should be allowed because TTS is not required
    assert mock_mainwindow.start_btn.isEnabled() == False
    assert mock_mainwindow.resume_project_id is None
