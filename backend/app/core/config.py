import os
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite+aiosqlite:///database/autoshort.db"
    ASSETS_DIR: str = "assets"
    PROJECTS_DIR: str = "projects"
    VOICES_DIR: str = "voices"
    VIDEOS_DIR: str = "videos"
    LOGS_DIR: str = "logs"
    
    @classmethod
    def load_config(cls) -> "Settings":
        # Search for config in common locations
        config_path = Path("config/config.yaml")
        if not config_path.exists():
            config_path = Path("../config/config.yaml")
            
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    server = data.get("server", {})
                    database = data.get("database", {})
                    storage = data.get("storage", {})
                    
                    return cls(
                        HOST=server.get("host", "127.0.0.1"),
                        PORT=server.get("port", 8000),
                        DATABASE_URL=database.get("url", "sqlite+aiosqlite:///database/autoshort.db"),
                        ASSETS_DIR=storage.get("assets_dir", "assets"),
                        PROJECTS_DIR=storage.get("projects_dir", "projects"),
                        VOICES_DIR=storage.get("voices_dir", "voices"),
                        VIDEOS_DIR=storage.get("videos_dir", "videos"),
                        LOGS_DIR=storage.get("logs_dir", "logs"),
                    )
            except Exception as e:
                print(f"Error loading configuration: {e}. Falling back to default settings.")
        
        return cls()

settings = Settings.load_config()
