from abc import abstractmethod
from typing import List
from backend.repositories.base_repository import IRepository
from backend.database.models import ProjectTable

class IProjectRepository(IRepository[ProjectTable]):
    """Port interface for Project entities persistence mapping."""
    
    @abstractmethod
    async def get_by_status(self, status: str) -> List[ProjectTable]:
        """Queries and retrieves all projects matching the target status.
        
        Args:
            status (str): The project execution status (e.g. queuing, completed).
            
        Returns:
            List[ProjectTable]: List of matching project data records.
        """
        pass
