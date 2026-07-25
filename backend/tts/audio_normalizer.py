import os
import subprocess

class AudioNormalizer:
    """Applies volume normalization, resampling, and channel downmixing using FFmpeg filters."""

    @classmethod
    def normalize_audio(
        cls, 
        input_path: str, 
        output_path: str, 
        sample_rate: int = 16000, 
        channels: int = 1,
        target_loudness_lufs: float = -16.0
    ) -> str:
        """Resamples, downmixes, and normalizes audio files (e.g. to WAV or MP3).
        
        Args:
            input_path (str): Input audio file path.
            output_path (str): Normalized output path.
            sample_rate (int): Target sample rate in Hz.
            channels (int): Target number of channels.
            target_loudness_lufs (float): Target loudness level in LUFS.
            
        Returns:
            str: Path of the normalized audio file.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Use EBU R128 loudness normalization filter
        filter_str = f"loudnorm=I={target_loudness_lufs}:TP=-1.5:LRA=11"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-filter:a", filter_str,
            "-ar", str(sample_rate),
            "-ac", str(channels),
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
