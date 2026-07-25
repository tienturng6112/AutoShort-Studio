import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

class PromptService:
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir).resolve()
        if not self.prompts_dir.exists():
            # Fallback path if running from inside app folder
            self.prompts_dir = Path("../prompts").resolve()
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_prompt_path(self, group: str) -> Path:
        return self.prompts_dir / f"{group}.yaml"
        
    def load_prompt(self, group: str) -> Optional[Dict[str, Any]]:
        file_path = self._get_prompt_path(group)
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading prompt {group}: {e}")
            return None
            
    def save_prompt(self, group: str, system: str, user: str) -> bool:
        file_path = self._get_prompt_path(group)
        try:
            data = {
                "system": system.strip(),
                "user": user.strip()
            }
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            print(f"Error saving prompt {group}: {e}")
            return False
            
    def list_groups(self) -> List[str]:
        try:
            return [f.stem for f in self.prompts_dir.glob("*.yaml")]
        except Exception:
            return []
        
    def format_prompt(self, group: str, variables: Dict[str, Any]) -> Dict[str, str]:
        prompt_data = self.load_prompt(group)
        if not prompt_data:
            raise ValueError(f"Prompt template group '{group}' not found.")
            
        system_tmpl = prompt_data.get("system", "")
        user_tmpl = prompt_data.get("user", "")
        
        # Simple template formatting that handles missing keys without throwing errors
        def safe_format(tmpl: str, args: Dict[str, Any]) -> str:
            res = tmpl
            for k, v in args.items():
                res = res.replace(f"{{{k}}}", str(v))
            return res
            
        return {
            "system": safe_format(system_tmpl, variables),
            "user": safe_format(user_tmpl, variables)
        }
