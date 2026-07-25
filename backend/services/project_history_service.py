import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ProjectHistoryService:
    def __init__(self, app_data_dir: str = "projects"):
        self.history_file = os.path.abspath(os.path.join(app_data_dir, "recent_projects.json"))
        os.makedirs(app_data_dir, exist_ok=True)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.history_file):
            self._save_data({
                "favorites": [],
                "pinned_projects": [],
                "history": []
            })

    def _load_data(self) -> Dict[str, Any]:
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load recent projects history: {str(e)}")
            return {
                "favorites": [],
                "pinned_projects": [],
                "history": []
            }

    def _save_data(self, data: Dict[str, Any]):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save recent projects history: {str(e)}")

    def record_project_opened(self, project_id: str, timestamp: float):
        data = self._load_data()
        
        # Remove if exists to update timestamp at the top
        history = [entry for entry in data.get("history", []) if entry.get("project_id") != project_id]
        
        # Insert at top
        history.insert(0, {
            "project_id": project_id,
            "last_opened": timestamp
        })
        
        # Keep only the last 50 projects
        data["history"] = history[:50]
        self._save_data(data)

    def remove_project(self, project_id: str):
        data = self._load_data()
        data["history"] = [entry for entry in data.get("history", []) if entry.get("project_id") != project_id]
        if project_id in data.get("pinned_projects", []):
            data["pinned_projects"].remove(project_id)
        if project_id in data.get("favorites", []):
            data["favorites"].remove(project_id)
        self._save_data(data)

    def pin_project(self, project_id: str):
        data = self._load_data()
        pinned = data.setdefault("pinned_projects", [])
        if project_id not in pinned:
            pinned.append(project_id)
            self._save_data(data)

    def unpin_project(self, project_id: str):
        data = self._load_data()
        pinned = data.setdefault("pinned_projects", [])
        if project_id in pinned:
            pinned.remove(project_id)
            self._save_data(data)

    def get_pinned_projects(self) -> List[str]:
        data = self._load_data()
        return data.get("pinned_projects", [])

    def get_history(self) -> List[Dict[str, Any]]:
        data = self._load_data()
        return data.get("history", [])
