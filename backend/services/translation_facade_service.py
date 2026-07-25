from typing import Optional, Any

class TranslationFacadeService:
    """UI-facing service wrapping TranslationProviderManager.
    
    This facade ensures the UI layer never instantiates or imports providers directly.
    """
    
    def __init__(self, manager: Optional[Any] = None):
        if manager is None:
            from backend.providers.translation.manager import TranslationProviderManager
            manager = TranslationProviderManager()
        self._manager = manager
    
    async def test_connection(self, provider_id: str) -> dict:
        try:
            return await self._manager.test_connection(provider_id)
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def refresh_models(self, provider_id: str) -> list:
        try:
            return await self._manager.refresh(provider_id)
        except Exception:
            return []
    
    def create_provider(self, provider_id: str, settings: dict, llm_service=None):
        try:
            return self._manager.create_provider(provider_id, settings, llm_service)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": provider_id
            }
    
    def list_providers(self) -> list:
        return self._manager.list()
    
    def get(self, provider_id: str):
        return self._manager.get(provider_id)
