from typing import List, Optional
from pydantic import BaseModel, Field
import time
import uuid

class CharacterProfile(BaseModel):
    character_id: str = Field(default_factory=lambda: f"char_{uuid.uuid4().hex[:8]}")
    display_name: str
    aliases: List[str] = Field(default_factory=list)
    gender: str = "Unknown"
    estimated_age: Optional[int] = None
    language: Optional[str] = None
    accent: Optional[str] = None
    preferred_voice: Optional[str] = None
    preferred_provider: Optional[str] = None
    emotion_profile: str = "Neutral"
    speech_rate: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    notes: Optional[str] = None
    favorite: bool = False
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
