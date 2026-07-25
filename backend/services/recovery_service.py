import logging
from typing import List
from backend.services.project_repository import ProjectRepository
from backend.models.project_models import ProjectMetadata

logger = logging.getLogger(__name__)

class RecoveryService:
    def __init__(self, repository: ProjectRepository = None):
        self.repository = repository or ProjectRepository()

    def detect_interrupted_projects(self) -> List[ProjectMetadata]:
        """
        Scans all projects. Any project whose execution status is 'Running'
        is considered interrupted by a crash or forced close.
        Returns the list of such projects.
        """
        interrupted = []
        for pid in self.repository.list_all_project_ids():
            try:
                project = self.repository.load(pid)
                if project.execution_state.status == "Running":
                    interrupted.append(project)
            except Exception as e:
                logger.error(f"Failed to check recovery for {pid}: {str(e)}")
        return interrupted

    def pause_interrupted_projects(self):
        """
        Automatically sets all interrupted projects to 'Paused' state
        so they don't remain stuck in 'Running' state across app restarts.
        """
        interrupted = self.detect_interrupted_projects()
        for project in interrupted:
            logger.info(f"Marking interrupted project {project.project_id} as Paused.")
            project.execution_state.status = "Paused"
            project.execution_state.last_error = "Project was unexpectedly interrupted."
            self.repository.save(project)

    def recover_project(self, project_id: str) -> bool:
        """
        Marks a specific project to be resumed. This primarily just sets status
        back to Waiting so QueueService can pick it up.
        """
        try:
            project = self.repository.load(project_id)
            if project.execution_state.status in ["Paused", "Failed", "Cancelled"]:
                project.execution_state.status = "Waiting"
                project.execution_state.last_error = None
                self.repository.save(project)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to recover project {project_id}: {str(e)}")
            return False
