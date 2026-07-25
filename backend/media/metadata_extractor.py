import json
import subprocess
import shutil
import logging
from typing import Any, Dict

logger = logging.getLogger("MetadataExtractor")

class MetadataExtractor:
    """Extracts media container structural parameters using FFprobe audits."""

    @classmethod
    def extract_metadata(cls, filepath: str) -> Dict[str, Any]:
        """Runs ffprobe subprocess checks on media file to fetch formats and stream keys.
        
        Args:
            filepath (str): Target media file path.
            
        Returns:
            Dict[str, Any]: Compiled video/audio streams parameters metadata.
        """
        # Detect if ffprobe is missing on system path
        ffprobe_path = shutil.which("ffprobe")
        if ffprobe_path is None:
            msg = "FFmpeg / ffprobe is not installed or not found."
            logger.error(msg)
            raise RuntimeError(msg)
        
        logger.info(f"Using ffprobe executable: {ffprobe_path}")

        cmd = [
            ffprobe_path, 
            "-v", "error", 
            "-show_format", 
            "-show_streams", 
            "-of", "json", 
            filepath
        ]
        
        logger.info(f"The full ffprobe executable path: {ffprobe_path}")
        logger.info(f"The exact command arguments: {cmd}")

        # Execute subprocess
        try:
            # We omit text=True to get raw bytes and prevent system encoding issues
            result = subprocess.run(cmd, capture_output=True, check=False)
        except FileNotFoundError:
            msg = "FFmpeg / ffprobe is not installed or not found."
            logger.error(msg)
            raise RuntimeError(msg)
        except Exception as e:
            msg = f"Failed to execute ffprobe: {str(e)}"
            logger.error(msg)
            raise RuntimeError(msg)

        # Safely decode raw streams to string to prevent UnicodeDecodeErrors
        stdout_raw = result.stdout
        stderr_raw = result.stderr
        
        if isinstance(stdout_raw, bytes):
            stdout_str = stdout_raw.decode("utf-8", errors="ignore")
        elif isinstance(stdout_raw, str):
            stdout_str = stdout_raw
        else:
            stdout_str = ""

        if isinstance(stderr_raw, bytes):
            stderr_str = stderr_raw.decode("utf-8", errors="ignore")
        elif isinstance(stderr_raw, str):
            stderr_str = stderr_raw
        else:
            stderr_str = ""

        logger.info(f"subprocess.returncode: {result.returncode}")
        logger.info(f"subprocess.stdout (raw): {repr(stdout_str)}")
        logger.info(f"subprocess.stderr (raw): {repr(stderr_str)}")

        # Check return code
        returncode = result.returncode if isinstance(result.returncode, int) else 0
        if returncode != 0:
            msg = f"ffprobe execution failure (exit code {returncode}). stderr: {stderr_str or 'none'}"
            logger.error(msg)
            raise RuntimeError(msg)

        # Detect empty stdout
        if not stdout_str or not stdout_str.strip():
            msg = "ffprobe output is empty."
            logger.error(msg)
            raise RuntimeError(msg)

        # Never call json.loads(None) or empty/invalid strings
        try:
            data = json.loads(stdout_str)
        except json.JSONDecodeError as je:
            msg = f"Failed to parse ffprobe JSON output: {str(je)}. Output: {stdout_str}"
            logger.error(msg)
            raise RuntimeError(msg)
        
        format_info = data.get("format", {})
        streams = data.get("streams", [])

        
        # Extract stream types
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
        subtitle_streams = [s for s in streams if s.get("codec_type") == "subtitle"]
        
        # Parse FPS frame rate representation (e.g. "30/1" or "24000/1001")
        fps = 0.0
        fps_str = video_stream.get("r_frame_rate", "0/0")
        if "/" in fps_str:
            try:
                num, den = fps_str.split("/")
                if float(den) > 0:
                    fps = float(num) / float(den)
            except (ValueError, ZeroDivisionError):
                pass
        else:
            try:
                fps = float(fps_str)
            except ValueError:
                pass

        # Bitrate check (falls back to formats bitrate check)
        bitrate_str = format_info.get("bit_rate") or video_stream.get("bit_rate")
        bitrate = int(bitrate_str) if bitrate_str and bitrate_str.isdigit() else 0
        
        # Duration extraction
        try:
            duration = float(format_info.get("duration", 0.0))
        except ValueError:
            duration = 0.0

        return {
            "duration": duration,
            "fps": fps,
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "codec": video_stream.get("codec_name", "unknown"),
            "bitrate": bitrate,
            "audio_streams": [
                {
                    "index": s.get("index"), 
                    "codec": s.get("codec_name", "unknown"), 
                    "channels": s.get("channels", 0)
                } for s in audio_streams
            ],
            "subtitle_streams": [
                {
                    "index": s.get("index"), 
                    "codec": s.get("codec_name", "unknown"), 
                    "language": s.get("tags", {}).get("language", "unknown")
                } for s in subtitle_streams
            ]
        }
