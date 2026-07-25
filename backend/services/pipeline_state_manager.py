import os
import logging
from typing import Dict, Any, Optional
from backend.models.project_models import ProjectMetadata
from backend.services.project_repository import ProjectRepository

logger = logging.getLogger(__name__)

class PipelineStateManager:
    STAGE_MAP = {
        "stage_1": "stage_1_import",
        "stage_2": "stage_2_denoise",
        "stage_3": "stage_3_speech",
        "stage_4": "stage_4_translate",
        "stage_5": "stage_5_align",
        "stage_6": "stage_6_tts",
        "stage_7": "stage_7_export",
        "stage_8": "stage_8_render"
    }

    def __init__(self, project_id: str, repository: ProjectRepository = None):
        self.project_id = project_id
        self.repository = repository or ProjectRepository()
        self.project_metadata: ProjectMetadata = self.repository.load(self.project_id)
        
    def _map_stage(self, stage_name: str) -> str:
        return self.STAGE_MAP.get(stage_name, stage_name)

    def get_state(self, stage_name: str) -> bool:
        """Returns True if completed, False if pending/failed."""
        mapped_key = self._map_stage(stage_name)
        return self.project_metadata.pipeline_state.get(mapped_key, False)

    def is_completed(self, stage_name: str) -> bool:
        return self.get_state(stage_name)

    def mark_completed(self, stage_name: str):
        self._update_state(stage_name, True)

    def mark_failed(self, stage_name: str):
        # We model failure as 'not complete' plus an error state in ExecutionState
        self._update_state(stage_name, False)
        
    def mark_pending(self, stage_name: str):
        self._update_state(stage_name, False)

    def _update_state(self, stage_name: str, status: bool):
        mapped_key = self._map_stage(stage_name)
        self.project_metadata.pipeline_state[mapped_key] = status
        self.save()

    def update_execution_state(self, status: str, progress: int = None, current_stage: str = None, last_error: str = None):
        if status is not None:
            self.project_metadata.execution_state.status = status
        if progress is not None:
            self.project_metadata.execution_state.progress_percent = progress
        if current_stage is not None:
            self.project_metadata.execution_state.current_stage = current_stage
        if last_error is not None:
            self.project_metadata.execution_state.last_error = last_error
        self.save()

    def set_metadata(self, key: str, value: Any):
        self.project_metadata.extra_metadata[key] = value
        self.save()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self.project_metadata.extra_metadata.get(key, default)

    def save(self):
        self.repository.save(self.project_metadata)

    def check_integrity(self, expected_files: Dict[str, str]) -> bool:
        """
        Check if expected files exist for completed stages.
        If a file is missing, the stage is reverted to pending.
        """
        is_intact = True
        for stage, path in expected_files.items():
            if self.is_completed(stage) and not os.path.exists(path):
                logger.warning(f"Integrity check failed for {stage}: Missing {path}")
                self.mark_pending(stage)
                is_intact = False
        return is_intact
