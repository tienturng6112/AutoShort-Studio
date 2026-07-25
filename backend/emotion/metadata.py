from pydantic import BaseModel, Field
import time

class EmotionProfile(BaseModel):
    emotion_id: str = "Neutral"   # E.g., Happy, Sad, Angry, Excited, Calm
    intensity: float = 1.0        # Range 0.0 to 1.0
    confidence: float = 100.0     # Detection confidence score
    user_override: bool = False   # True if a user manually assigned this
    provider_supported: bool = False # Resolved at runtime against TTS capabilities
    created_at: float = Field(default_factory=time.time)
