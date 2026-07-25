import os
import time
from backend.models.project_models import ProjectMetadata, ProjectSnapshot, ExecutionState
from backend.services.project_repository import ProjectRepository
from backend.services.project_history_service import ProjectHistoryService

def run_tests():
    print("Testing Milestone 1 Components...")
    
    # 1. Project Models
    snapshot = ProjectSnapshot(translation_provider="DeepL")
    state = ExecutionState(status="Running", progress_percent=50)
    
    metadata = ProjectMetadata(
        project_id="test_proj_001",
        project_name="Test Project",
        created_at=time.time(),
        modified_at=time.time(),
        settings_snapshot=snapshot,
        execution_state=state
    )
    
    assert metadata.settings_snapshot.translation_provider == "DeepL"
    assert metadata.execution_state.status == "Running"
    print("[PASS] Project Models")
    
    # 2. Project Repository
    repo = ProjectRepository(projects_dir="test_projects")
    assert repo.save(metadata) == True
    assert repo.save(metadata) == True # Save twice to generate backup
    
    loaded = repo.load("test_proj_001")
    assert loaded.project_name == "Test Project"
    assert loaded.execution_state.progress_percent == 50
    assert "test_proj_001" in repo.list_all_project_ids()
    
    # Test atomic backup recovery
    file_path = repo.get_project_file_path("test_proj_001")
    os.remove(file_path) # Delete primary to force backup load
    loaded_backup = repo.load("test_proj_001")
    assert loaded_backup.project_name == "Test Project"
    
    # Cleanup repo
    repo.delete("test_proj_001")
    print("[PASS] Project Repository")
    
    # 3. Project History Service
    history = ProjectHistoryService(app_data_dir="test_projects")
    history.record_project_opened("test_proj_001", time.time())
    history.pin_project("test_proj_001")
    
    pinned = history.get_pinned_projects()
    assert "test_proj_001" in pinned
    
    recent = history.get_history()
    assert len(recent) == 1
    assert recent[0]["project_id"] == "test_proj_001"
    
    history.unpin_project("test_proj_001")
    history.remove_project("test_proj_001")
    
    assert "test_proj_001" not in history.get_pinned_projects()
    assert len(history.get_history()) == 0
    print("[PASS] Project History Service")
    
    # Clean up history dir
    import shutil
    shutil.rmtree("test_projects", ignore_errors=True)

if __name__ == "__main__":
    run_tests()
