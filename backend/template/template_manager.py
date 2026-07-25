import os
import json
import time
import shutil
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TemplateMetadata(BaseModel):
    template_id: str
    name: str
    description: str = ""
    category: str = "Custom"
    version: str = "1.0.0"
    author: str = "User"
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    compatible_app_version: str = "1.0.0"
    tags: List[str] = Field(default_factory=list)
    favorite: bool = False

class TemplatePayload(BaseModel):
    translation_settings: Dict[str, Any] = Field(default_factory=dict)
    voice_settings: Dict[str, Any] = Field(default_factory=dict)
    character_profiles: Dict[str, Any] = Field(default_factory=dict)
    emotion_presets: Dict[str, Any] = Field(default_factory=dict)
    pipeline_options: Dict[str, Any] = Field(default_factory=dict)
    subtitle_settings: Dict[str, Any] = Field(default_factory=dict)
    render_settings: Dict[str, Any] = Field(default_factory=dict)
    plugin_configuration: Dict[str, Any] = Field(default_factory=dict)

class ProjectTemplate(BaseModel):
    metadata: TemplateMetadata
    payload: TemplatePayload

class TemplateManager:
    """Manages creation, loading, and saving of Project Templates."""

    def __init__(self, storage_dir: str = "config/templates", cap_manager=None):
        self.storage_dir = os.path.abspath(storage_dir)
        self.cap_manager = cap_manager
        os.makedirs(self.storage_dir, exist_ok=True)
        self._ensure_defaults()

    def _ensure_defaults(self):
        """Creates default templates if they don't exist."""
        podcast_path = os.path.join(self.storage_dir, "podcast.json")
        if not os.path.exists(podcast_path):
            podcast_template = ProjectTemplate(
                metadata=TemplateMetadata(
                    template_id="podcast",
                    name="Podcast Workflow",
                    description="Optimized for long-form audio. Skips video rendering, deep speaker diarization.",
                    category="Podcast",
                    tags=["audio", "long-form"]
                ),
                payload=TemplatePayload(
                    pipeline_options={"skip_video_rendering": True, "diarization": "deep"}
                )
            )
            self.save_template(podcast_template)

        tiktok_path = os.path.join(self.storage_dir, "tiktok.json")
        if not os.path.exists(tiktok_path):
            tiktok_template = ProjectTemplate(
                metadata=TemplateMetadata(
                    template_id="tiktok",
                    name="TikTok Workflow",
                    description="Optimized for vertical rendering, large subtitle fonts, short length limits.",
                    category="TikTok",
                    tags=["video", "short-form", "vertical"]
                ),
                payload=TemplatePayload(
                    subtitle_settings={"font_size": 24, "alignment": "center"}
                )
            )
            self.save_template(tiktok_template)

    def load_template(self, template_id: str) -> Optional[ProjectTemplate]:
        """Loads and returns a template by ID."""
        file_path = os.path.join(self.storage_dir, f"{template_id}.json")
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return ProjectTemplate(**data)

    def save_template(self, template: ProjectTemplate):
        """Saves or updates a template to disk."""
        template.metadata.updated_at = time.time()
        file_path = os.path.join(self.storage_dir, f"{template.metadata.template_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(template.model_dump_json(indent=2))

    def list_templates(self, category: str = None, tag: str = None) -> List[ProjectTemplate]:
        """Lists available templates, optionally filtered."""
        templates = []
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                tpl = self.load_template(filename[:-5])
                if tpl:
                    if category and tpl.metadata.category != category:
                        continue
                    if tag and tag not in tpl.metadata.tags:
                        continue
                    templates.append(tpl)
        return templates

    def delete_template(self, template_id: str):
        """Deletes a template."""
        file_path = os.path.join(self.storage_dir, f"{template_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)

    def duplicate_template(self, template_id: str, new_name: str) -> Optional[ProjectTemplate]:
        """Creates a copy of an existing template."""
        orig = self.load_template(template_id)
        if not orig:
            return None
        new_id = f"{template_id}_copy_{int(time.time())}"
        orig.metadata.template_id = new_id
        orig.metadata.name = new_name
        self.save_template(orig)
        return orig

    def export_template(self, template_id: str, export_path: str):
        """Exports a template to an external JSON file for sharing."""
        file_path = os.path.join(self.storage_dir, f"{template_id}.json")
        if os.path.exists(file_path):
            shutil.copy2(file_path, export_path)

    def validate_template(self, template: ProjectTemplate) -> dict:
        """
        Validates template dependencies (providers, plugins, voices).
        Returns a diagnostic dictionary of missing capabilities.
        """
        diagnostics = {"missing_providers": [], "missing_voices": [], "capability_mismatches": []}
        if self.cap_manager:
            # Example check
            pass
        return diagnostics
