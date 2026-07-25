from typing import Dict, List, Optional, Any
from backend.providers.translation.base_translation_provider import BaseTranslationProvider

class ProviderRegistrationError(ValueError):
    """Raised when registering or instantiating an invalid/abstract provider."""
    pass


class TranslationProviderManager:
    """Independent manager and factory for Translation Providers."""
    
    def __init__(self):
        self._providers: Dict[str, BaseTranslationProvider] = {}
        self.pre_register_providers()
        
    def pre_register_providers(self):
        print("\n=== TRANSLATION PROVIDER STARTUP REPORT ===")
        for pid in ["chatanywhere", "deepl", "google", "gemini", "openai"]:
            registered = "NO"
            concrete_class = "None"
            creatable = "NO"
            try:
                # Pre-register unconditionally using a dummy initialization key
                provider = self.create_provider(pid, {pid: {"api_key": "dummy_init_key"}})
                if provider:
                    registered = "YES"
                    concrete_class = provider.__class__.__name__
                    creatable = "YES"
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to pre-register translation provider '{pid}': {e}")
            print(f"  Provider ID:    {pid}")
            print(f"  Registered:     {registered}")
            print(f"  Concrete Class: {concrete_class}")
            print(f"  Creatable:      {creatable}")
            print("  ----------------")
        print("===========================================\n")
        assert self.get("chatanywhere", create_lazy=False) is not None, "Startup validation failed: ChatAnywhere provider not registered."
        
    def register(self, provider_id: str, provider: BaseTranslationProvider) -> None:
        import inspect
        if inspect.isabstract(provider.__class__):
            raise ProviderRegistrationError(f"Cannot register abstract provider: {provider.__class__.__name__}")
        self._providers[provider_id.lower()] = provider
        
    def remove(self, provider_id: str) -> None:
        self._providers.pop(provider_id.lower(), None)
        
    def get(self, provider_id: str, llm_service=None, create_lazy: bool = True) -> Optional[BaseTranslationProvider]:
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
                if provider_id in ("chatanywhere", "openai") and llm_service is None:
                    from backend.services.llm_service import LLMService
                    llm_service = LLMService()
                self.create_provider(provider_id, settings, llm_service)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Lazy creation of translation provider {provider_id} failed: {e}")
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

    def create_provider(self, provider_id: str, settings: dict, llm_service=None) -> BaseTranslationProvider:
        """Factory: creates, registers, and returns a translation provider instance.
        
        Args:
            provider_id: Provider identifier (chatanywhere, deepl, gemini, google, openai).
            settings: Application settings dict (typically loaded from settings.json).
            llm_service: Optional LLMService instance needed by ChatAnywhere translation provider.
            
        Returns:
            BaseTranslationProvider: The created and registered provider instance.
        """
        provider_id = provider_id.lower()

        # Config Flow Audit Logs
        config = settings.get(provider_id, settings.get("providers", {}).get(provider_id, {}))
        api_key = config.get("api_key", "")
        print(f"\n[CONFIG FLOW AUDIT]")
        print(f"  Requested provider:           {provider_id}")
        print(f"  Received config:              { {k: v for k, v in config.items() if k != 'api_key'} }")
        print(f"  API key length:               {len(api_key)}")

        if provider_id == "deepl":
            from backend.providers.translation.deepl.deepl_provider import DeepLTranslationProvider
            provider = DeepLTranslationProvider(
                api_key=config.get("api_key", "")
            )
        elif provider_id == "chatanywhere":
            from backend.providers.translation.chatanywhere.chatanywhere_provider import ChatAnywhereTranslationProvider
            
            # Print audit checks
            api_key = config.get("api_key", "")
            print(f"[CONFIG FLOW AUDIT - MANAGER]")
            print(f"  api_key exists:               {bool(api_key)}")
            print(f"  api_key length:               {len(api_key)}")
            print(f"  config keys:                  {list(config.keys())}")
            
            if llm_service is not None and hasattr(llm_service, "create_provider"):
                llm_service.create_provider("chatanywhere", {"chatanywhere": config})
                
            provider = ChatAnywhereTranslationProvider(
                api_key=api_key,
                base_url=config.get("base_url"),
                model=config.get("model", "gpt-4o-mini")
            )
        elif provider_id == "gemini":
            from backend.providers.translation.gemini.gemini_provider import GeminiTranslationProvider
            provider = GeminiTranslationProvider(
                api_key=config.get("api_key", ""),
                model=config.get("model", "gemini-1.5-flash")
            )
        elif provider_id == "google":
            from backend.providers.translation.google.google_provider import GoogleTranslationProvider
            provider = GoogleTranslationProvider(
                api_key=config.get("api_key", "")
            )
        elif provider_id == "openai":
            from backend.providers.translation.chatanywhere.chatanywhere_provider import ChatAnywhereTranslationProvider
            
            # Print audit checks
            api_key = config.get("api_key", "")
            print(f"[CONFIG FLOW AUDIT - MANAGER]")
            print(f"  api_key exists:               {bool(api_key)}")
            print(f"  api_key length:               {len(api_key)}")
            print(f"  config keys:                  {list(config.keys())}")
            
            if llm_service is not None and hasattr(llm_service, "create_provider"):
                llm_service.create_provider("openai", {"openai": config})
                
            provider = ChatAnywhereTranslationProvider(
                api_key=api_key,
                base_url=config.get("base_url"),
                model=config.get("model", "gpt-4o-mini")
            )
        else:
            raise ValueError(f"Unknown translation provider: {provider_id}")

        import inspect
        if inspect.isabstract(provider.__class__):
            raise ProviderRegistrationError(f"Provider class {provider.__class__.__name__} for '{provider_id}' is abstract. Missing methods.")

        self.register(provider_id, provider)
        return provider

