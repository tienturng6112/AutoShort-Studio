import os
import sys
import json
import time
from typing import Dict

# Add workspace to path
workspace_root = r"t:\AutoShort Studio"
sys.path.insert(0, workspace_root)

from backend.services.project_repository import ProjectRepository
from backend.models.project_models import ProjectMetadata, ExecutionState, ProjectSnapshot
from backend.services.recovery_service import RecoveryService
from backend.services.queue_service import QueueService
from PySide6.QtWidgets import QApplication

def test_backward_compatibility():
    print("--- 1. Testing Backward Compatibility ---")
    repo = ProjectRepository(projects_dir=os.path.join(workspace_root, "projects"))
    
    # Create old format project manually
    old_project_id = "project_legacy_123"
    project_dir = repo.get_project_dir(old_project_id)
    os.makedirs(project_dir, exist_ok=True)
    
    old_data = {
        "project_id": old_project_id,
        "name": "Legacy Project", # note 'name' instead of 'project_name'
        "created_at": time.time(),
        "input_video": "test.mp4",
        "status": "Waiting", # note 'status' at root
        "pipeline": {
            "stage_1": True,
            "stage_2": False
        }
    }
    
    metadata_path = os.path.join(project_dir, "project.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(old_data, f)
        
    # Attempt to load using new repository
    project = repo.load(old_project_id)
    print(f"Loaded legacy project ID: {project.project_id}")
    print(f"Status in ExecutionState: {project.execution_state.status}")
    print("Backward compatibility check: PASSED (Loaded without crash)")
    
    repo.delete(old_project_id)
    print("Cleaned up legacy project.\n")

def test_recovery():
    print("--- 2. Testing Recovery Service ---")
    repo = ProjectRepository(projects_dir=os.path.join(workspace_root, "projects"))
    
    # Create a project that looks like it crashed
    crash_id = f"project_crashed_{int(time.time())}"
    project_dir = repo.get_project_dir(crash_id)
    os.makedirs(project_dir, exist_ok=True)
    
    exec_state = ExecutionState(status="Running", progress_percent=45, current_stage="Translation")
    project = ProjectMetadata(
        project_id=crash_id,
        project_name="Crashed Project",
        created_at=time.time(),
        modified_at=time.time(),
        execution_state=exec_state,
        settings_snapshot=ProjectSnapshot()
    )
    repo.save(project)
    
    # Run RecoveryService
    recovery = RecoveryService(repository=repo)
    interrupted = recovery.detect_interrupted_projects()
    
    assert len(interrupted) >= 1, "Failed to detect interrupted project!"
    found = False
    for p in interrupted:
        if p.project_id == crash_id:
            found = True
            break
    assert found, "Did not find our specific crashed project."
    print("Recovery detection: PASSED")
    
    # First pause all interrupted projects (like app startup does)
    recovery.pause_interrupted_projects()
    
    paused_project = repo.load(crash_id)
    assert paused_project.execution_state.status == "Paused", "Failed to pause interrupted project"
    print("Pause interrupted: PASSED")
    
    recovery.recover_project(crash_id)
    recovered_project = repo.load(crash_id)
    assert recovered_project.execution_state.status == "Waiting", f"Expected Waiting, got {recovered_project.execution_state.status}"
    print("Recovery modification to Waiting: PASSED\n")
    
    repo.delete(crash_id)

def test_queue_execution():
    print("--- 3. Testing Queue Service Execution (Mock) ---")
    app = QApplication.instance() or QApplication(sys.argv)
    repo = ProjectRepository(projects_dir=os.path.join(workspace_root, "projects"))
    queue = QueueService(repository=repo)
    
    proj_id_1 = f"project_q1_{int(time.time())}"
    proj_id_2 = f"project_q2_{int(time.time())}"
    
    p1 = ProjectMetadata(project_id=proj_id_1, project_name="Q1", created_at=time.time(), modified_at=time.time(), settings_snapshot=ProjectSnapshot(), execution_state=ExecutionState(status="Waiting"))
    p2 = ProjectMetadata(project_id=proj_id_2, project_name="Q2", created_at=time.time(), modified_at=time.time(), settings_snapshot=ProjectSnapshot(), execution_state=ExecutionState(status="Waiting"))
    
    repo.save(p1)
    repo.save(p2)
    
    queue.pause_queue() # prevent running
    queue.start()
    
    queue.enqueue(proj_id_1)
    queue.enqueue(proj_id_2)
    
    status = queue.get_queue_status()
    assert len(status) == 2, f"Queue length expected 2, got {len(status)}"
    assert status[0] == proj_id_1, "Order mismatch"
    print("Queue insertion & ordering: PASSED")
    
    queue.dequeue(proj_id_1)
    status = queue.get_queue_status()
    assert len(status) == 1, "Queue dequeue failed"
    assert status[0] == proj_id_2, "Queue dequeue removed wrong item"
    print("Queue dequeue: PASSED\n")
    
    queue.stop()
    repo.delete(proj_id_1)
    repo.delete(proj_id_2)

if __name__ == "__main__":
    try:
        test_backward_compatibility()
        test_recovery()
        test_queue_execution()
        print("ALL TESTS PASSED SUCCESSFULLY!")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)
