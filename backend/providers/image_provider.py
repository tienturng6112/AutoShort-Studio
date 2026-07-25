from abc import ABC, abstractmethod
from typing import List

class BaseImageProvider(ABC):
    """Port interface for stock image provider plugins."""
    
    @abstractmethod
    async def search_images(self, query: str, limit: int = 1) -> List[str]:
        """Queries stock image archives and returns image URLs."""
        pass
