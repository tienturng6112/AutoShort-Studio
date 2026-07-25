import os
from typing import Set

try:
    from faster_whisper import download_model
except ImportError:
    download_model = None

class SpeechModelManager:
    """Manages local Whisper model configurations and dynamic weights downloads."""
    
    SUPPORTED_MODELS: Set[str] = {"tiny", "base", "small", "medium", "large-v3"}

    def __init__(self, models_root: str = "models/whisper") -> None:
        self._root = models_root

    def get_model_path(self, model_size: str) -> str:
        """Resolves the local folder path containing the model weights, downloading them if missing.
        
        Args:
            model_size (str): Whisper model identifier (e.g. tiny, base).
            
        Returns:
            str: Directory path containing the model weights.
            
        Raises:
            ValueError: If the requested model size is not supported.
            ImportError: If faster_whisper is not installed.
        """
        if model_size not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model size '{model_size}'. Supported choices are: {self.SUPPORTED_MODELS}"
            )
            
        model_dir = os.path.join(self._root, model_size)
        
        # Download files if the directory is missing or empty
        if not os.path.exists(model_dir) or not os.listdir(model_dir):
            if download_model is None:
                raise ImportError(
                    "Speech model download error: The 'faster_whisper' package is not installed. "
                    "Cannot download model weights."
                )
            os.makedirs(model_dir, exist_ok=True)
            # Calls faster-whisper downloader
            download_model(model_size, output_dir=model_dir)
            
        return os.path.abspath(model_dir)

    def is_model_downloaded(self, model_size: str) -> bool:
        """Checks if the target model weights are already downloaded and cached locally.
        
        Args:
            model_size (str): Target model size.
            
        Returns:
            bool: True if model is cached, False otherwise.
        """
        model_dir = os.path.join(self._root, model_size)
        return os.path.exists(model_dir) and len(os.listdir(model_dir)) > 0
