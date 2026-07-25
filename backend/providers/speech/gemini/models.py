from dataclasses import dataclass
from typing import Optional, List

@dataclass
class GeminiSpeechSettings:
    api_key: str
    model: str = "gemini-1.5-flash"
    voice: str = "Puck"
    language: str = "en-US"
    style: str = ""
    speed: float = 1.0
    pitch: float = 0.0

@dataclass
class GeminiModelInfo:
    name: str
    display_name: str
    supports_audio: bool
    capabilities: List[str]

@dataclass
class GeminiVoiceInfo:
    name: str
    gender: str = "Unknown"
