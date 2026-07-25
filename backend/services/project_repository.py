import os
import json
import logging
from backend.models.project_models import ProjectMetadata

logger = logging.getLogger(__name__)

class ProjectRepository:
    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = os.path.abspath(projects_dir)
        os.makedirs(self.projects_dir, exist_ok=True)

    def get_project_dir(self, project_id: str) -> str:
        if hasattr(project_id, "project_id"):
            project_id = getattr(project_id, "project_id")
        return os.path.join(self.projects_dir, str(project_id))

    def get_project_file_path(self, project_id: str) -> str:
        if hasattr(project_id, "project_id"):
            project_id = getattr(project_id, "project_id")
        return os.path.join(self.get_project_dir(str(project_id)), "project.json")

    def save(self, project: ProjectMetadata) -> bool:
        """
        Saves the project metadata to project.json atomically.
        """
        try:
            project_dir = self.get_project_dir(project.project_id)
            os.makedirs(project_dir, exist_ok=True)
            
            # Ensure required subdirectories exist
            for sub in ["video", "audio", "subtitle", "translation", "tts", "render", "cache", "metadata", "logs"]:
                os.makedirs(os.path.join(project_dir, sub), exist_ok=True)

            file_path = self.get_project_file_path(project.project_id)
            tmp_path = file_path + ".tmp"
            bak_path = file_path + ".bak"

            # Create backup of existing file
            if os.path.exists(file_path):
                import shutil
                shutil.copy2(file_path, bak_path)

            data = project.to_dict()

            # Write to tmp file first
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # Atomic replace
            os.replace(tmp_path, file_path)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save project {project.project_id}: {str(e)}")
            return False

    def load(self, project_id: str) -> ProjectMetadata:
        """
        Loads the project metadata from project.json.
        Attempts recovery from .bak if the primary file is corrupted or missing.
        """
        if hasattr(project_id, "project_id"):
            project_id = getattr(project_id, "project_id")
        file_path = self.get_project_file_path(str(project_id))
        bak_path = file_path + ".bak"

        data = None
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load primary project.json for {project_id}: {str(e)}")
                data = None

        if data is None and os.path.exists(bak_path):
            try:
                with open(bak_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"Recovered project {project_id} from backup.")
                # Restore the main file
                import shutil
                shutil.copy2(bak_path, file_path)
            except Exception as e:
                logger.error(f"Failed to load backup project.json.bak for {project_id}: {str(e)}")
                data = None

        if data is None:
            raise FileNotFoundError(f"Project metadata not found or corrupted for {project_id}")

        return ProjectMetadata.from_dict(data)

    def delete(self, project_id: str) -> bool:
        project_dir = self.get_project_dir(project_id)
        if not os.path.exists(project_dir):
            return True
            
        import shutil
        try:
            shutil.rmtree(project_dir)
            return True
        except Exception as e:
            logger.error(f"Failed to delete project directory {project_id}: {str(e)}")
            return False

    def list_all_project_ids(self) -> list:
        if not os.path.exists(self.projects_dir):
            return []
            
        project_ids = []
        for d in os.listdir(self.projects_dir):
            if os.path.isdir(os.path.join(self.projects_dir, d)):
                if os.path.exists(self.get_project_file_path(d)):
                    project_ids.append(d)
        return project_ids
