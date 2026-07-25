from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class ProjectSnapshot:
    translation_provider: str = ""
    translation_model: str = ""
    tts_provider: str = ""
    tts_model: str = ""
    processing_profile: str = ""
    output_mode: str = "Subtitle + Voice"
    voice_mode: str = "SINGLE"
    global_voice: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "translation_provider": self.translation_provider,
            "translation_model": self.translation_model,
            "tts_provider": self.tts_provider,
            "tts_model": self.tts_model,
            "processing_profile": self.processing_profile,
            "output_mode": self.output_mode,
            "voice_mode": self.voice_mode,
            "global_voice": self.global_voice
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectSnapshot':
        if not data:
            return cls()
        return cls(
            translation_provider=data.get("translation_provider", ""),
            translation_model=data.get("translation_model", ""),
            tts_provider=data.get("tts_provider", ""),
            tts_model=data.get("tts_model", ""),
            processing_profile=data.get("processing_profile", ""),
            output_mode=data.get("output_mode", "Subtitle + Voice"),
            voice_mode=data.get("voice_mode", "SINGLE"),
            global_voice=data.get("global_voice", "")
        )

@dataclass
class ExecutionState:
    status: str = "Waiting" # Waiting, Running, Paused, Completed, Failed, Cancelled
    progress_percent: int = 0
    current_stage: str = ""
    last_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "progress_percent": self.progress_percent,
            "current_stage": self.current_stage,
            "last_error": self.last_error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionState':
        if not data:
            return cls()
        return cls(
            status=data.get("status", "Waiting"),
            progress_percent=data.get("progress_percent", 0),
            current_stage=data.get("current_stage", ""),
            last_error=data.get("last_error")
        )

@dataclass
class ProjectMetadata:
    project_id: str
    project_name: str
    created_at: float
    modified_at: float
    input_video: str = ""
    video_hash: str = ""
    settings_snapshot: ProjectSnapshot = field(default_factory=ProjectSnapshot)
    languages: Dict[str, str] = field(default_factory=lambda: {"source": "en", "target": "vi"})
    speaker_mapping: Dict[str, str] = field(default_factory=dict)
    voice_mapping: Dict[str, str] = field(default_factory=dict)
    pipeline_state: Dict[str, bool] = field(default_factory=lambda: {
        "stage_1_import": False,
        "stage_2_denoise": False,
        "stage_3_speech": False,
        "stage_4_translate": False,
        "stage_5_align": False,
        "stage_6_tts": False,
        "stage_7_export": False,
        "stage_8_render": False
    })
    execution_state: ExecutionState = field(default_factory=ExecutionState)
    cache_version: str = "1.0"
    project_schema_version: str = "1.0"
    application_version: str = "0.1A"
    
    # Optional fields for backward compatibility or additional metadata storage
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "input_video": self.input_video,
            "video_hash": self.video_hash,
            "settings_snapshot": self.settings_snapshot.to_dict(),
            "languages": self.languages,
            "speaker_mapping": self.speaker_mapping,
            "voice_mapping": self.voice_mapping,
            "pipeline_state": self.pipeline_state,
            "execution_state": self.execution_state.to_dict(),
            "cache_version": self.cache_version,
            "project_schema_version": self.project_schema_version,
            "application_version": self.application_version,
            "extra_metadata": self.extra_metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectMetadata':
        return cls(
            project_id=data.get("project_id", ""),
            project_name=data.get("project_name", ""),
            created_at=data.get("created_at", 0.0),
            modified_at=data.get("modified_at", 0.0),
            input_video=data.get("input_video", ""),
            video_hash=data.get("video_hash", ""),
            settings_snapshot=ProjectSnapshot.from_dict(data.get("settings_snapshot", {})),
            languages=data.get("languages", {"source": "en", "target": "vi"}),
            speaker_mapping=data.get("speaker_mapping", {}),
            voice_mapping=data.get("voice_mapping", {}),
            pipeline_state=data.get("pipeline_state", {
                "stage_1_import": False,
                "stage_2_denoise": False,
                "stage_3_speech": False,
                "stage_4_translate": False,
                "stage_5_align": False,
                "stage_6_tts": False,
                "stage_7_export": False,
                "stage_8_render": False
            }),
            execution_state=ExecutionState.from_dict(data.get("execution_state", {})),
            cache_version=data.get("cache_version", "1.0"),
            project_schema_version=data.get("project_schema_version", data.get("cache_version", "1.0")),
            application_version=data.get("application_version", "0.1A"),
            extra_metadata=data.get("extra_metadata", {})
        )
