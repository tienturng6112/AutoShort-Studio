import os
import sys
import time
from PySide6.QtCore import QCoreApplication
from backend.services.queue_service import QueueService
from backend.services.project_repository import ProjectRepository
from backend.models.project_models import ProjectMetadata, ProjectSnapshot, ExecutionState

def main():
    app = QCoreApplication(sys.argv)
    
    repo = ProjectRepository("test_projects")
    
    # Create mock project
    proj_id = "test_queue_001"
    proj = ProjectMetadata(
        project_id=proj_id,
        project_name="Test Queue",
        created_at=time.time(),
        modified_at=time.time(),
        settings_snapshot=ProjectSnapshot(),
        execution_state=ExecutionState(status="Waiting")
    )
    repo.save(proj)
    
    queue_service = QueueService(repository=repo)
    
    def on_started(pid):
        print(f"[{pid}] Started")
        
    def on_output(pid, text):
        print(f"[{pid}] OUTPUT: {text}")
        
    def on_finished(pid, exit_code):
        print(f"[{pid}] Finished with code {exit_code}")
        queue_service.stop()
        app.quit()
        
    queue_service.signals.project_started.connect(on_started)
    queue_service.signals.project_output.connect(on_output)
    queue_service.signals.project_finished.connect(on_finished)
    
    queue_service.start()
    queue_service.enqueue(proj_id)
    
    # This might fail immediately if --input isn't given to the script since it's a new project
    # But we're just checking if it launches and captures output.
    
    app.exec()
    
    import shutil
    shutil.rmtree("test_projects", ignore_errors=True)
    
if __name__ == "__main__":
    main()
