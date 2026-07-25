import os
import subprocess

class SilenceGenerator:
    """Generates silent audio segments using FFmpeg's virtual audio source filters."""

    @classmethod
    def generate_silence(cls, duration: float, output_path: str, sample_rate: int = 16000, channels: int = 1) -> str:
        """Runs ffmpeg command to generate a silent audio clip of a specific duration.
        
        Args:
            duration (float): Silence duration in seconds.
            output_path (str): Output wav file path.
            sample_rate (int): Audio sample rate in Hz.
            channels (int): Number of channels.
            
        Returns:
            str: Path of the generated silent audio file.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Prevent zero or negative duration errors
        if duration <= 0:
            duration = 0.001
            
        layout = "mono" if channels == 1 else "stereo"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r={sample_rate}:cl={layout}",
            "-t", f"{duration:.3f}",
            output_path
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
        return output_path
