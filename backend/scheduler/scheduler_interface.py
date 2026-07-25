from abc import ABC, abstractmethod
from typing import Any, Callable

class IScheduler(ABC):
    """Port interface for core task scheduling and queue checks."""
    
    @abstractmethod
    def add_job(self, job_id: str, interval_seconds: int, callback: Callable[..., Any]) -> None:
        """Registers a recurring background task."""
        pass
        
    @abstractmethod
    def remove_job(self, job_id: str) -> None:
        """Cancels a scheduled task."""
        pass
        
    @abstractmethod
    def start(self) -> None:
        """Starts the task loop engine."""
        pass
        
    @abstractmethod
    def stop(self) -> None:
        """Tears down all tasks and stops loop thread pools."""
        pass
