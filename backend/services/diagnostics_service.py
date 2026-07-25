import os
from typing import List, Dict, Any

class DiagnosticsService:
    """Service responsible for loading provider registries and extracting diagnostics reports."""
    
    @staticmethod
    def get_diagnostics() -> List[Dict[str, Any]]:
        from backend.providers.provider_registry import ProviderRegistry
        from backend.providers.provider_capability_manager import ProviderCapabilityManager
        
        registry = ProviderRegistry()
        registry.inject_legacy_providers()
        registry.discover_providers(os.path.join("backend", "plugins", "providers"))
        cap_mgr = ProviderCapabilityManager(registry, config_dir="config")
        cap_mgr.refresh()
        return cap_mgr.get_provider_diagnostics()
