import asyncio
import logging
from typing import Dict, Any, List, Optional
from backend.app.core.database import AsyncSessionLocal
from backend.app.services.workflow_service import WorkflowService
from backend.app.services.prompt_service import PromptService
from backend.app.services.audio_service import AudioService
from backend.app.services.asset_service import AssetService
from backend.app.services.render_service import RenderService
from backend.app.repositories.repositories import ProjectRepository

logger = logging.getLogger("queue_manager")

class QueueManager:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._active_project_id: Optional[str] = None
        self._running = False
        self._loop_task: Optional[asyncio.Task] = None
        
    async def add_project(self, project_id: str):
        """Adds a project to the rendering queue."""
        await self._queue.put(project_id)
        logger.info(f"Project {project_id} queued.")
        
    def start(self):
        """Starts the background worker loop."""
        if not self._running:
            self._running = True
            self._loop_task = asyncio.create_task(self._loop())
            logger.info("Rendering queue worker started.")
            
    def stop(self):
        """Stops the background worker loop."""
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
            
    async def _loop(self):
        while self._running:
            try:
                # Wait for next project item
                project_id = await self._queue.get()
                self._active_project_id = project_id
                logger.info(f"Starting pipeline execution for project: {project_id}")
                
                # Create scoped session for workflow run
                async with AsyncSessionLocal() as db:
                    # Resolve services
                    prompt_svc = PromptService()
                    audio_svc = AudioService()
                    asset_svc = AssetService()
                    render_svc = RenderService()
                    
                    workflow_svc = WorkflowService(
                        db=db,
                        prompt_service=prompt_svc,
                        audio_service=audio_svc,
                        asset_service=asset_svc,
                        render_service=render_svc
                    )
                    
                    # Update status to queuing first if not already rendering
                    project_repo = ProjectRepository(db)
                    proj = await project_repo.get(project_id)
                    if proj and proj.status == "draft":
                        proj.status = "queuing"
                        await db.commit()
                        
                    try:
                        await workflow_svc.run_workflow(project_id)
                    except Exception as e:
                        logger.error(f"Error processing project {project_id} in queue: {e}")
                        
                self._queue.task_done()
                self._active_project_id = None
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Exception in rendering queue worker: {e}")
                await asyncio.sleep(2.0)
                
    def get_status(self) -> Dict[str, Any]:
        """Returns the current state of the queue worker."""
        return {
            "active_project_id": self._active_project_id,
            "queue_size": self._queue.qsize(),
            "is_running": self._running
        }

queue_manager = QueueManager()
