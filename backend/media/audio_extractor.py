import os
import subprocess

class AudioExtractor:
    """Extracts audio channels from media containers using FFmpeg demuxing commands."""

    @classmethod
    def extract_audio(cls, video_path: str, output_wav_path: str) -> str:
        """Runs ffmpeg command to extract audio tracks as PCM 16kHz Mono WAV.
        
        Args:
            video_path (str): Input video path reference.
            output_wav_path (str): Output wav filepath destination.
            
        Returns:
            str: Output wav filepath.
        """
        os.makedirs(os.path.dirname(output_wav_path), exist_ok=True)
        
        # -y: overwrite output file
        # -vn: disable video stream mapping
        # -acodec pcm_s16le: 16-bit signed little-endian PCM
        # -ar 16000: Resample to 16,000 Hz
        # -ac 1: Convert to single (mono) channel
        cmd = [
            "ffmpeg", "-y", 
            "-i", video_path,
            "-vn", 
            "-acodec", "pcm_s16le", 
            "-ar", "16000", 
            "-ac", "1",
            output_wav_path
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
        return output_wav_path
