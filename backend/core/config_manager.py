from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class ServerConfig(BaseModel):
    """Server hosting parameters."""
    host: str = Field(default="127.0.0.1", description="FastAPI server host address")
    port: int = Field(default=8000, description="Uvicorn port binding")
    reload: bool = Field(default=True, description="Enable dev auto-reloads")

class DatabaseConfig(BaseModel):
    """Database persistence parameters."""
    url: str = Field(default="sqlite+aiosqlite:///database/autoshort.db", description="SQLAlchemy connection URL")

class StorageConfig(BaseModel):
    """Local directories mapping targets."""
    assets_dir: str = Field(default="assets", description="Shared media assets path")
    projects_dir: str = Field(default="projects", description="User projects cache")
    voices_dir: str = Field(default="voices", description="Synthesized TTS storage")
    videos_dir: str = Field(default="videos", description="Exported video files path")
    logs_dir: str = Field(default="logs", description="Server logs directory")

class AppConfig(BaseModel):
    """Global configuration settings model validation schema."""
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    secrets_encryption_key: Optional[str] = Field(default=None, description="Key for AES-GCM settings encryption")

class IConfigManager(ABC):
    """Port interface for global configuration management and runtime setting updates."""
    
    @abstractmethod
    def load(self) -> AppConfig:
        """Loads and parses settings from yaml configurations.
        
        Returns:
            AppConfig: Validated settings model.
        """
        pass

    @abstractmethod
    def get(self) -> AppConfig:
        """Returns the current loaded in-memory configuration instance.
        
        Returns:
            AppConfig: Loaded configuration model.
        """
        pass

    @abstractmethod
    def update(self, key: str, value: Any) -> None:
        """Updates a configuration setting dynamically at runtime.
        
        Args:
            key (str): Configuration path key (e.g. server.port).
            value (Any): Target value setting.
        """
        pass
