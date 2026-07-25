from typing import Optional, List
from pydantic import BaseModel, Field

class VoiceMetadata(BaseModel):
    voice_id: str
    provider_id: str
    display_name: str
    language: str
    locale: Optional[str] = None
    gender: str = "Unknown"
    age: Optional[str] = None
    style: Optional[str] = None
    accent: Optional[str] = None
    emotion_support: bool = False
    sample_rate: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    preview_supported: bool = False
    favorite: bool = False
    installed: bool = True
    last_used: Optional[float] = None
    quality_score: float = 0.0
