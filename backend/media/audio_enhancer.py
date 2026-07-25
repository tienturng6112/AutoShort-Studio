import os
import subprocess
import shutil

class DemucsSpeechEnhancer:
    """Uses Meta's Demucs to separate speech vocals from background music/noise."""
    
    @classmethod
    def separate_audio(cls, input_audio_path: str, output_dir: str) -> tuple[str, str]:
        """Separates vocals and background tracks from input wav.
        
        Args:
            input_audio_path (str): Path to input mono/stereo audio.wav.
            output_dir (str): Directory where vocals.wav and background.wav will be saved.
            
        Returns:
            tuple[str, str]: Path to vocals.wav, path to background.wav.
        """
        os.makedirs(output_dir, exist_ok=True)
        vocals_dest = os.path.join(output_dir, "vocals.wav")
        background_dest = os.path.join(output_dir, "background.wav")
        
        # Check if already cached/computed
        if os.path.exists(vocals_dest) and os.path.exists(background_dest):
            return vocals_dest, background_dest
            
        # Determine demucs executable path in venv
        demucs_exe = os.path.abspath("backend/venv/Scripts/demucs.exe")
        if not os.path.exists(demucs_exe):
            # Fallback to PATH search
            demucs_exe = "demucs"
            
        # Run demucs command
        # --two-stems vocals: outputs vocals and no_vocals
        # -o temp_out: temporary output folder
        temp_out = os.path.abspath(os.path.join(os.path.dirname(output_dir), "temp_demucs"))
        os.makedirs(temp_out, exist_ok=True)
        
        cmd = [
            demucs_exe,
            "--two-stems", "vocals",
            "-o", temp_out,
            os.path.abspath(input_audio_path)
        ]
        
        # Run process
        result = subprocess.run(cmd, capture_output=True, text=False, check=False)
        if result.returncode != 0:
            stderr_msg = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
            raise RuntimeError(f"Demucs audio separation failed with code {result.returncode}. Stderr: {stderr_msg}")
            
        # Locate generated outputs
        # Demucs output structure: temp_out/htdemucs/<filename_without_ext>/vocals.wav (and no_vocals.wav)
        filename = os.path.splitext(os.path.basename(input_audio_path))[0]
        vocals_src = os.path.join(temp_out, "htdemucs", filename, "vocals.wav")
        background_src = os.path.join(temp_out, "htdemucs", filename, "no_vocals.wav")
        
        if not os.path.exists(vocals_src) or not os.path.exists(background_src):
            raise FileNotFoundError("Demucs finished but could not locate vocals.wav or no_vocals.wav.")
            
        # Copy to destination paths
        shutil.copy2(vocals_src, vocals_dest)
        shutil.copy2(background_src, background_dest)
        
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_out)
        except Exception:
            pass
            
        return vocals_dest, background_dest
