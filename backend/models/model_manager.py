import os
import json
import logging
import asyncio
from typing import Dict, List, Optional

logger = logging.getLogger("ModelManager")

class ModelManager:
    """Manages local AI models (OmniVoice, etc.) including downloading, verification, and deletion."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = os.path.abspath(models_dir)
        os.makedirs(self.models_dir, exist_ok=True)
        self.active_models: Dict[str, str] = {}
        
    def detect_installed_models(self) -> List[Dict[str, str]]:
        """Scans the models directory for installed models."""
        installed = []
        for root, dirs, files in os.walk(self.models_dir):
            if "model.json" in files:
                try:
                    with open(os.path.join(root, "model.json"), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data["location"] = root
                        
                        # Calculate size
                        total_size = 0
                        for f_name in files:
                            fp = os.path.join(root, f_name)
                            total_size += os.path.getsize(fp)
                        data["size_bytes"] = total_size
                        
                        installed.append(data)
                except Exception as e:
                    logger.warning(f"Error reading model config in {root}: {e}")
        return installed

    def switch_model(self, engine: str, model_id: str):
        """Switches the active model for a specific engine (e.g. omnivoice)."""
        self.active_models[engine] = model_id
        logger.info(f"Switched {engine} to model {model_id}")
        
    def get_active_model(self, engine: str) -> Optional[str]:
        return self.active_models.get(engine)

    async def download_model(self, model_id: str, download_url: str) -> bool:
        """Mock download for a local model."""
        logger.info(f"Downloading model {model_id} from {download_url}...")
        model_path = os.path.join(self.models_dir, "omnivoice", model_id)
        os.makedirs(model_path, exist_ok=True)
        
        # Simulate network download delay
        await asyncio.sleep(2)
        
        # Write dummy model metadata
        meta = {
            "id": model_id,
            "name": f"OmniVoice {model_id.capitalize()}",
            "version": "1.0.0",
            "checksum": "sha256-dummy",
            "engine": "omnivoice"
        }
        with open(os.path.join(model_path, "model.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4)
            
        with open(os.path.join(model_path, "weights.bin"), "wb") as f:
            f.write(os.urandom(1024 * 1024 * 5)) # 5MB dummy weights
            
        logger.info(f"Downloaded model {model_id} successfully.")
        return True

    def delete_model(self, model_id: str) -> bool:
        import shutil
        target = None
        for root, dirs, files in os.walk(self.models_dir):
            if "model.json" in files:
                try:
                    with open(os.path.join(root, "model.json"), "r") as f:
                        if json.load(f).get("id") == model_id:
                            target = root
                            break
                except Exception:
                    pass
        if target:
            shutil.rmtree(target)
            return True
        return False
        
    def verify_checksum(self, model_id: str) -> bool:
        """Verifies integrity of local model."""
        return True # Mock implementation

    def get_system_hardware(self) -> Dict[str, Any]:
        """Detects available hardware for inference."""
        import platform
        hardware = {
            "os": platform.system(),
            "cpu": platform.processor(),
            "ram_gb": 0,
            "gpu": "None detected",
            "vram_gb": 0,
            "inference_mode": "CPU"
        }
        
        try:
            import psutil
            hardware["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
        except ImportError:
            pass
            
        try:
            # Check for CUDA via torch if available without crashing if not
            import torch
            if torch.cuda.is_available():
                hardware["gpu"] = torch.cuda.get_device_name(0)
                hardware["vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1)
                hardware["inference_mode"] = "CUDA"
            else:
                try:
                    # Check for DirectML
                    import torch_directml
                    if torch_directml.is_available():
                        hardware["gpu"] = torch_directml.device_name(0)
                        hardware["inference_mode"] = "DirectML"
                except ImportError:
                    pass
        except ImportError:
            pass
            
        return hardware
