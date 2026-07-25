import enum
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, JSON, Enum as SqlEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class ProjectStatus(enum.Enum):
    """Execution status for automated video project pipelines."""
    DRAFT = "draft"
    QUEUING = "queuing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"

class ProviderTable(Base):
    __tablename__ = "providers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    api_key: Mapped[Optional[str]] = mapped_column(String(255))
    base_url: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class ModelTable(Base):
    __tablename__ = "models"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    provider_id: Mapped[str] = mapped_column(String(36), ForeignKey("providers.id"))
    name: Mapped[str] = mapped_column(String(100))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

class ProjectTable(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    status: Mapped[ProjectStatus] = mapped_column(SqlEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ProjectFileTable(Base):
    __tablename__ = "project_files"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(50))  # script, raw_asset, output

class AssetTable(Base):
    __tablename__ = "assets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"))
    type: Mapped[str] = mapped_column(String(20))  # audio, video, image
    path: Mapped[str] = mapped_column(String(500))
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

class VoiceTable(Base):
    __tablename__ = "voices"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    provider: Mapped[str] = mapped_column(String(50))  # edge, elevenlabs, etc.
    name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(20))

class PromptTable(Base):
    __tablename__ = "prompts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    group: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))
    template: Mapped[str] = mapped_column(JSON)

class WorkflowTable(Base):
    __tablename__ = "workflows"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    nodes_graph: Mapped[Dict[str, Any]] = mapped_column(JSON)

class HistoryTable(Base):
    __tablename__ = "history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"))
    action: Mapped[str] = mapped_column(String(100))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class LogTable(Base):
    __tablename__ = "logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(10))
    message: Mapped[str] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class SettingTable(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

class TemplateTable(Base):
    __tablename__ = "templates"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    config: Mapped[Dict[str, Any]] = mapped_column(JSON)

class RenderQueueTable(Base):
    __tablename__ = "render_queue"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"))
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
