from pydantic import BaseModel, Field
from typing import Optional

class TranslationCapabilities(BaseModel):
    context_translation: bool = False
    translation_memory: bool = False
    glossary: bool = False
    confidence_score: bool = False
    streaming: bool = False
    batch_translation: bool = False
    json_schema: bool = False
    custom_system_prompt: bool = False
    temperature_control: bool = False

class TTSCapabilities(BaseModel):
    voice_library: bool = False
    voice_preview: bool = False
    voice_clone: bool = False
    emotion: bool = False
    speaker_style: bool = False
    speed_control: bool = False
    pitch_control: bool = False
    volume_control: bool = False
    ssml: bool = False
    streaming_audio: bool = False

class SubtitleCapabilities(BaseModel):
    subtitle_alignment: bool = False
    subtitle_merge: bool = False
    subtitle_export: bool = False
    subtitle_styles: bool = False

class ProviderCapabilities(BaseModel):
    """Capability indicators mapping features supported by a specific AI Provider."""
    supports_chat: bool = Field(default=False, description="Supports chat prompt completion requests")
    supports_stream: bool = Field(default=False, description="Supports streaming word token events")
    supports_json: bool = Field(default=False, description="Supports enforcing JSON/Structured Output constraints")
    supports_embeddings: bool = Field(default=False, description="Supports generating vector embeddings")
    supports_vision: bool = Field(default=False, description="Supports input analysis of visual media frames")
    supports_image_generation: bool = Field(default=False, description="Supports stock or AI image generation")
    supports_video_generation: bool = Field(default=False, description="Supports stock or AI video clip synthesis")
    supports_audio_generation: bool = Field(default=False, description="Supports synthesized TTS voice generation")
    supports_function_calling: bool = Field(default=False, description="Supports structured function/tool calling schemas")
    
    translation: Optional[TranslationCapabilities] = None
    tts: Optional[TTSCapabilities] = None
    subtitle: Optional[SubtitleCapabilities] = None
