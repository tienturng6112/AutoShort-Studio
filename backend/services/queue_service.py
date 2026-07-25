import os
import sys
import json
import time
import subprocess
import logging
from typing import List, Dict, Any
from PySide6.QtCore import QThread, Signal, QObject, QMutex, QMutexLocker
from backend.services.project_repository import ProjectRepository
from backend.models.project_models import ProjectMetadata

logger = logging.getLogger(__name__)

class QueueSignals(QObject):
    queue_updated = Signal()
    project_started = Signal(str) # project_id
    project_finished = Signal(str, int) # project_id, exit_code
    project_output = Signal(str, str) # project_id, text

class QueueService(QThread):
    def __init__(self, repository: ProjectRepository = None, parent=None):
        super().__init__(parent)
        self.repository = repository or ProjectRepository()
        self.signals = QueueSignals()
        
        self.queue: List[str] = []
        self.is_paused = False
        self._mutex = QMutex()
        self._running = True
        self._current_process = None
        self._current_project_id = None

    def enqueue(self, project_id: str):
        if hasattr(project_id, "project_id"):
            project_id = getattr(project_id, "project_id")
        project_id = str(project_id)
        with QMutexLocker(self._mutex):
            if project_id not in self.queue and project_id != self._current_project_id:
                self.queue.append(project_id)
                project = self.repository.load(project_id)
                project.execution_state.status = "Waiting"
                self.repository.save(project)
        self.signals.queue_updated.emit()

    def dequeue(self, project_id: str):
        if hasattr(project_id, "project_id"):
            project_id = getattr(project_id, "project_id")
        project_id = str(project_id)
        with QMutexLocker(self._mutex):
            if project_id in self.queue:
                self.queue.remove(project_id)
                project = self.repository.load(project_id)
                project.execution_state.status = "Paused"
                self.repository.save(project)
        self.signals.queue_updated.emit()

    def pause_queue(self):
        with QMutexLocker(self._mutex):
            self.is_paused = True
            if self._current_project_id:
                p_dir = os.path.join("projects", self._current_project_id)
                if os.path.exists(p_dir):
                    open(os.path.join(p_dir, "pause.flag"), "w").close()
        self.signals.queue_updated.emit()

    def resume_queue(self):
        with QMutexLocker(self._mutex):
            self.is_paused = False
            if self._current_project_id:
                p_dir = os.path.join("projects", self._current_project_id)
                flag_path = os.path.join(p_dir, "pause.flag")
                if os.path.exists(flag_path):
                    try:
                        os.remove(flag_path)
                    except Exception:
                        pass
        self.signals.queue_updated.emit()

    def stop(self):
        with QMutexLocker(self._mutex):
            self._running = False
        if self._current_process:
            try:
                self._current_process.terminate()
            except Exception:
                pass
        self.wait()

    def get_queue_status(self) -> List[str]:
        with QMutexLocker(self._mutex):
            return list(self.queue)

    def run(self):
        while self._running:
            project_to_run = None
            
            with QMutexLocker(self._mutex):
                if not self.is_paused and len(self.queue) > 0:
                    project_to_run = self.queue.pop(0)
                    self._current_project_id = project_to_run
            
            if project_to_run:
                self.signals.queue_updated.emit()
                self._process_project(project_to_run)
                
                with QMutexLocker(self._mutex):
                    self._current_project_id = None
                self.signals.queue_updated.emit()
            else:
                time.sleep(0.1) # Poll every 100ms if empty or paused

    def _process_project(self, project_id: str):
        if hasattr(project_id, "project_id"):
            project_id = getattr(project_id, "project_id")
        project_id = str(project_id)
        self.signals.project_started.emit(project_id)
        project = self.repository.load(project_id)
        project.execution_state.status = "Running"
        self.repository.save(project)
        
        # Determine python executable
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        python_exe = os.path.join(workspace_root, "backend", "venv", "Scripts", "python.exe")
        if not os.path.exists(python_exe):
            python_exe = os.path.join(workspace_root, "backend", "venv", "bin", "python")
        if not os.path.exists(python_exe):
            python_exe = sys.executable or "python"

        args = [
            python_exe, "-u", "-m", "backend.run_pipeline",
            "--project-id", project_id
        ]
        
        # Check settings for speech enhancement
        settings_path = os.path.join(workspace_root, "config", "settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings_data = json.load(f)
                    if settings_data.get("speech_enhancement") == "demucs":
                        args.append("--enhance-speech")
            except Exception:
                pass

        try:
            # We use Popen and read stdout line by line
            env = os.environ.copy()
            env["PYTHONPATH"] = workspace_root
            
            self._current_process = subprocess.Popen(
                args,
                cwd=workspace_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                bufsize=1
            )
            
            for line in self._current_process.stdout:
                if not self._running:
                    break
                line = line.strip()
                if line:
                    self.signals.project_output.emit(project_id, line)
                    
            self._current_process.wait()
            exit_code = self._current_process.returncode
            
            # Post-process status update
            project = self.repository.load(project_id)
            if exit_code == 0:
                all_stages = project.pipeline_state if isinstance(project.pipeline_state, dict) else {}
                stages_completed = bool(all_stages) and all(bool(v) for v in all_stages.values())
                if stages_completed:
                    project.execution_state.status = "Completed"
                    project.execution_state.progress_percent = 100
                else:
                    project.execution_state.status = "Failed"
                    project.execution_state.last_error = "Pipeline exited before completing all stages."
            else:
                project.execution_state.status = "Failed"
                if not project.execution_state.last_error:
                    project.execution_state.last_error = f"Pipeline exited with code {exit_code}"
            self.repository.save(project)
            
            self.signals.project_finished.emit(project_id, exit_code)
            
        except Exception as e:
            logger.error(f"Error executing pipeline for project {project_id}: {str(e)}")
            project = self.repository.load(project_id)
            project.execution_state.status = "Failed"
            project.execution_state.last_error = str(e)
            self.repository.save(project)
            self.signals.project_finished.emit(project_id, -1)
        finally:
            self._current_process = None
