from abc import ABC, abstractmethod
from typing import BinaryIO

class IStorage(ABC):
    """Generic storage interface port supporting Local, AWS S3, Cloudflare R2, and Google Drive adapters."""
    
    @abstractmethod
    async def upload_file(self, file_obj: BinaryIO, destination_path: str) -> str:
        """Uploads a file stream binary payload to target storage paths.
        
        Args:
            file_obj (BinaryIO): Python file-like binary stream.
            destination_path (str): Target key or filename path.
            
        Returns:
            str: Public URI or system file reference path.
        """
        pass
        
    @abstractmethod
    async def download_file(self, source_path: str, local_destination: str) -> None:
        """Downloads a target asset from remote storage and writes to local disk.
        
        Args:
            source_path (str): Remote URI or source path key.
            local_destination (str): Absolute local target output write path.
        """
        pass
        
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Deletes an asset from the storage directory.
        
        Args:
            file_path (str): Target file reference path to purge.
            
        Returns:
            bool: True if purged successfully, False otherwise.
        """
        pass

    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Checks if the target path key contains an existing asset.
        
        Args:
            file_path (str): target file reference path.
            
        Returns:
            bool: True if file exists, False otherwise.
        """
        pass
