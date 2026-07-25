from abc import ABC, abstractmethod

class BaseImporter(ABC):
    """Port interface representing a general media importer (Local or YouTube)."""
    
    @abstractmethod
    async def import_media(self, source: str, destination_dir: str) -> str:
        """Imports or downloads media file into the destination folder.
        
        Args:
            source (str): File path or URL link.
            destination_dir (str): Folder path target.
            
        Returns:
            str: Absolute path of the imported media file.
        """
        pass
