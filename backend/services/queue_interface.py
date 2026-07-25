from abc import ABC, abstractmethod
from typing import Any, Dict

class IQueueManager(ABC):
    """Port interface for background execution queue orchestration."""
    
    @abstractmethod
    async def add_project(self, project_id: str) -> None:
        """Enqueues a project ID for sequential background timeline generation.
        
        Args:
            project_id (str): The project entity database key.
        """
        pass
        
    @abstractmethod
    def start(self) -> None:
        """Starts the background worker queue polling task loop."""
        pass
        
    @abstractmethod
    def stop(self) -> None:
        """Tears down background loops, cancelling any currently rendering process."""
        pass
        
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Queries and returns queue metadata statistics.
        
        Returns:
            Dict[str, Any]: Fields mapping queue_size, active_project_id, and worker states.
        """
        pass
