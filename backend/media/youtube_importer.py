import os
import subprocess
from backend.media.base_importer import BaseImporter

class YoutubeImporter(BaseImporter):
    """Downloads YouTube clips using yt-dlp and compiles them to standard MP4 files."""

    async def import_media(self, source: str, destination_dir: str) -> str:
        os.makedirs(destination_dir, exist_ok=True)
        # Using a deterministic output filename for pipeline stability
        dest_filename = "youtube_download.mp4"
        dest_path = os.path.join(destination_dir, dest_filename)
        
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "-o", dest_path,
            "--merge-output-format", "mp4",
            source
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=False, check=False)
        stdout_str = ""
        stderr_str = ""
        returncode = 0
        if result is not None:
            if isinstance(result.stdout, bytes):
                stdout_str = result.stdout.decode("utf-8", errors="replace")
            elif isinstance(result.stdout, str):
                stdout_str = result.stdout
            if isinstance(result.stderr, bytes):
                stderr_str = result.stderr.decode("utf-8", errors="replace")
            elif isinstance(result.stderr, str):
                stderr_str = result.stderr
            if isinstance(result.returncode, int):
                returncode = result.returncode

        if returncode != 0:
            raise subprocess.CalledProcessError(
                returncode=returncode,
                cmd=cmd,
                output=stdout_str,
                stderr=stderr_str
            )
        return os.path.abspath(dest_path)
