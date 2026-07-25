import os
import shutil
from backend.media.base_importer import BaseImporter

class LocalImporter(BaseImporter):
    """Imports media files from local file paths, copying them to target project directories."""

    async def import_media(self, source: str, destination_dir: str) -> str:
        if not os.path.exists(source):
            raise FileNotFoundError(f"Local importer error: Source file '{source}' not found on disk.")
            
        os.makedirs(destination_dir, exist_ok=True)
        filename = os.path.basename(source)
        dest_path = os.path.join(destination_dir, filename)
        
        # Performs copy keeping metadata tags
        shutil.copy2(source, dest_path)
        return os.path.abspath(dest_path)
