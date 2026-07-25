import yaml
from typing import Any, Dict

class PromptLoader:
    """Loads version-controlled prompt templates from YAML files in the prompts catalog."""
    
    @classmethod
    def load_from_yaml(cls, file_path: str) -> Dict[str, Any]:
        """Loads and parses a YAML prompt configuration file.
        
        Args:
            file_path (str): Target file path.
            
        Returns:
            Dict[str, Any]: Dictionary mapping prompt keys to templates.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or {}
