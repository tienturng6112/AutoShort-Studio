from abc import ABC, abstractmethod
from typing import List

class BaseVideoProvider(ABC):
    """Port interface for stock video provider plugins."""
    
    @abstractmethod
    async def search_videos(self, query: str, limit: int = 1) -> List[str]:
        """Queries stock video archives and returns video download URLs."""
        pass
