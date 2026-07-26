from typing import Optional
from backend.app.providers.base import BaseAIProvider
from backend.app.providers.openai_provider import OpenAICompatibleProvider

class AIProviderFactory:
    @staticmethod
    def get_provider(
        name: str, 
        api_key: Optional[str] = None, 
        base_url: Optional[str] = None
    ) -> BaseAIProvider:
        name_lower = name.lower()
        # Handles chatanywhere, groq, openrouter, ollama, lm_studio
        return OpenAICompatibleProvider(
            api_key=api_key, 
            base_url=base_url, 
            provider_name=name_lower
        )
