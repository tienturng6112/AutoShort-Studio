from typing import Dict, List, Optional, Any
from backend.providers.llm.base_llm_provider import BaseLLMProvider

class LLMProviderManager:
    """Independent manager and factory for LLM Providers."""
    
    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        
    def register(self, provider_id: str, provider: BaseLLMProvider) -> None:
        self._providers[provider_id.lower()] = provider
        
    def remove(self, provider_id: str) -> None:
        self._providers.pop(provider_id.lower(), None)
        
    def get(self, provider_id: str, create_lazy: bool = True) -> Optional[BaseLLMProvider]:
        provider_id = provider_id.lower()
        if provider_id not in self._providers and create_lazy:
            try:
                import json
                import os
                settings_path = os.path.join("config", "settings.json")
                settings = {}
                if os.path.exists(settings_path):
                    with open(settings_path, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                self.create_provider(provider_id, settings)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Lazy creation of LLM provider {provider_id} failed: {e}")
        return self._providers.get(provider_id)
        
    def list(self) -> List[str]:
        return list(self._providers.keys())
        
    async def test_connection(self, provider_id: str) -> Dict[str, Any]:
        provider = self.get(provider_id)
        if not provider:
            return {"success": False, "error": "Provider not registered."}
        try:
            return await provider.test_connection()
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    async def refresh(self, provider_id: str) -> List[str]:
        provider = self.get(provider_id)
        if not provider:
            return []
        return await provider.list_models()

    def create_provider(self, provider_id: str, settings: dict) -> BaseLLMProvider:
        """Factory: creates, registers, and returns an LLM provider instance.
        
        Args:
            provider_id: Provider identifier (e.g., "llm", "openai_compatible").
            settings: Application settings dict (typically loaded from settings.json).
            
        Returns:
            BaseLLMProvider: The created and registered provider instance.
        """
        provider_id = provider_id.lower()

        # Support "llm" as the primary LLM provider key.
        # Reads config from settings under "llm" key with fallback to "providers.llm".
        if provider_id == "llm":
            from backend.providers.llm.chatanywhere.chatanywhere_provider import LLMAPIProvider
            config = settings.get("llm", settings.get("providers", {}).get("llm", {}))
            provider = LLMAPIProvider(
                name=provider_id,
                api_key=config.get("api_key", ""),
                base_url=config.get("base_url", config.get("api_base", ""))
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider_id}")

        import inspect
        if inspect.isabstract(provider.__class__):
            raise ValueError(f"Provider class {provider.__class__.__name__} for '{provider_id}' is abstract. Missing methods.")

        self.register(provider_id, provider)
        return provider