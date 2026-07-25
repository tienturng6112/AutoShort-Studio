from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

class IPlugin(ABC):
    """Port interface for a sandboxed custom Plugin."""
    
    @property
    @abstractmethod
    def manifest(self) -> Dict[str, Any]:
        """Returns the parsed manifest dictionary of the plugin."""
        pass
        
    @abstractmethod
    def on_load(self) -> None:
        """Called when plugin container is dynamically loaded into memory."""
        pass
        
    @abstractmethod
    def on_unload(self) -> None:
        """Called when plugin container is disabled/unloaded."""
        pass


class IPluginSandbox(ABC):
    """Port interface for running plugins inside isolated execution environments."""
    
    @abstractmethod
    def run_safe(self, callback: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Executes a plugin callable inside the permission-restricted sandbox."""
        pass


class IPluginManager(ABC):
    """Port interface for discovering, loading, and routing event hooks to plugins."""
    
    @abstractmethod
    def scan_directory(self, path: str) -> None:
        """Discovers valid plugins containing manifest.json in the directory."""
        pass
        
    @abstractmethod
    def load_plugin(self, name: str) -> None:
        """Verifies permissions and initializes a plugin instance."""
        pass
        
    @abstractmethod
    def register_hook(self, hook_name: str, callback: Callable[..., Any]) -> None:
        """Registers a lifecycle hook event listener (e.g., pre_script_generation)."""
        pass
        
    @abstractmethod
    def trigger_hook(self, hook_name: str, data: Any) -> Any:
        """Fires a lifecycle hook event, passing it through sandboxed plugin hooks."""
        pass
