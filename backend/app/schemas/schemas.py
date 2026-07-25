from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

# Provider schemas
class ProviderCreate(BaseModel):
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = True

class ProviderUpdate(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = None

class ProviderResponse(BaseModel):
    id: str
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Project schemas
class ProjectCreate(BaseModel):
    name: str
    aspect_ratio: str = "9:16"  # 9:16, 16:9, 1:1
    config: Optional[Dict[str, Any]] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    aspect_ratio: str
    status: str
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Setting schemas
class SettingUpdate(BaseModel):
    key: str
    value: Any

# Prompt schemas
class PromptUpdate(BaseModel):
    group: str
    system: str
    user: str
