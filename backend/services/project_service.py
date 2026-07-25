import json
import os
import time
import shutil
from typing import Any, Dict, List, Optional

class ProjectService:
    """Service managing project lifecycles, scaffolding directories, and serializing states."""
    
    def __init__(self, projects_root: str = "projects", config_root: str = "config") -> None:
        self._root = projects_root
        self._config_root = config_root
        self._recent_file = os.path.join(self._config_root, "recent_projects.json")
        os.makedirs(self._root, exist_ok=True)
        os.makedirs(self._config_root, exist_ok=True)

    def _update_recent(self, project_id: str, name: str, path: str, extra_data: Dict = None):
        recent_data = {"recent": []}
        if os.path.exists(self._recent_file):
            try:
                with open(self._recent_file, "r", encoding="utf-8") as f:
                    recent_data = json.load(f)
            except Exception:
                pass

        # Remove existing if present to move to top
        recent_data["recent"] = [p for p in recent_data.get("recent", []) if p.get("project_id") != project_id]
        
        project_entry = {
            "project_id": project_id,
            "project_name": name,
            "path": path,
            "last_opened": time.time(),
            "pinned": False
        }
        if extra_data:
            project_entry.update(extra_data)
            
        recent_data["recent"].insert(0, project_entry)
        
        with open(self._recent_file, "w", encoding="utf-8") as f:
            json.dump(recent_data, f, indent=2, ensure_ascii=False)

    def _remove_from_recent(self, project_id: str):
        if not os.path.exists(self._recent_file):
            return
        try:
            with open(self._recent_file, "r", encoding="utf-8") as f:
                recent_data = json.load(f)
            recent_data["recent"] = [p for p in recent_data.get("recent", []) if p.get("project_id") != project_id]
            with open(self._recent_file, "w", encoding="utf-8") as f:
                json.dump(recent_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get_recent_projects(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self._recent_file):
            return []
        try:
            with open(self._recent_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("recent", [])
        except Exception:
            return []

    def load_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        project_dir = self.get_project_dir(project_id)
        json_path = os.path.join(project_dir, "project.json")
        if not os.path.exists(json_path):
            return None
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._update_recent(project_id, data.get("name", project_id), project_dir)
            return data
        except Exception:
            return None

    def save_project(self, project_id: str, data: Dict[str, Any]):
        project_dir = self.get_project_dir(project_id)
        json_path = os.path.join(project_dir, "project.json")
        data["modified_at"] = time.time()
        
        # Ensure dir exists just in case
        os.makedirs(project_dir, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        extra = {
            "status": data.get("status", "Waiting"),
            "progress": data.get("progress", 0),
            "output_mode": data.get("output_mode", "")
        }
        self._update_recent(project_id, data.get("name", project_id), project_dir, extra)

    def create_project(self, project_id: str, name: str, template_id: Optional[str] = None) -> Dict[str, Any]:
        """Creates the standardized clean subdirectories structure and generates the project.json descriptor."""
        project_dir = os.path.join(self._root, project_id)
        
        # 1. Scaffold standardized directory tree
        subdirs = [
            "video", "audio", "subtitle", "translation", 
            "tts", "render", "cache", "metadata", "logs"
        ]
        
        for folder in subdirs:
            os.makedirs(os.path.join(project_dir, folder), exist_ok=True)
            
        # 2. Compile project.json metadata
        now = time.time()
        project_data = {
            "id": project_id,
            "name": name,
            "status": "Waiting",
            "progress": 0,
            "current_stage": "",
            "created_at": now,
            "modified_at": now,
            "folders": {folder: os.path.join(project_dir, folder) for folder in subdirs},
            "pipeline_state": {}
        }
        
        json_path = os.path.join(project_dir, "project.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
            
        if template_id:
            from backend.template.template_manager import TemplateManager
            mgr = TemplateManager()
            tpl = mgr.load_template(template_id)
            if tpl:
                # Copy global config -> project config first, then override
                settings_path = os.path.join("config", "settings.json")
                if os.path.exists(settings_path):
                    shutil.copy2(settings_path, os.path.join(project_dir, "settings.json"))
                    
                # Apply Template payloads
                # This could overwrite settings.json completely or selectively
                # Based on the plan, we overwrite if we want a strict template
                with open(os.path.join(project_dir, "settings.json"), "w", encoding="utf-8") as f:
                    json.dump(tpl.payload.translation_settings, f)
                    
                with open(os.path.join(project_dir, "data/characters.json"), "w", encoding="utf-8") as f:
                    json.dump(tpl.payload.character_profiles, f)
            
        self._update_recent(project_id, name, project_dir)
        return project_data

    def delete_project(self, project_id: str) -> bool:
        project_dir = self.get_project_dir(project_id)
        if os.path.exists(project_dir):
            try:
                shutil.rmtree(project_dir)
                self._remove_from_recent(project_id)
                return True
            except Exception:
                return False
        return False

    def duplicate_project(self, original_id: str, new_id: str, new_name: str) -> Optional[Dict[str, Any]]:
        orig_dir = self.get_project_dir(original_id)
        new_dir = self.get_project_dir(new_id)
        if not os.path.exists(orig_dir):
            return None
            
        try:
            shutil.copytree(orig_dir, new_dir)
            # Update project.json
            json_path = os.path.join(new_dir, "project.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["id"] = new_id
                data["name"] = new_name
                now = time.time()
                data["created_at"] = now
                data["modified_at"] = now
                data["status"] = "Waiting"
                data["progress"] = 0
                
                subdirs = [
                    "video", "audio", "subtitle", "translation", 
                    "tts", "render", "cache", "metadata", "logs"
                ]
                data["folders"] = {folder: os.path.join(new_dir, folder) for folder in subdirs}
                
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
                self._update_recent(new_id, new_name, new_dir)
                return data
            return None
        except Exception:
            return None

    def get_project_dir(self, project_id: str) -> str:
        return os.path.join(self._root, project_id)
