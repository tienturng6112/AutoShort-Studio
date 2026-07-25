from typing import Optional
from backend.app.providers.base import BaseAIProvider
from backend.app.providers.openai_provider import OpenAICompatibleProvider
from backend.app.providers.gemini_provider import GeminiProvider
from backend.app.providers.claude_provider import ClaudeProvider

class AIProviderFactory:
    @staticmethod
    def get_provider(
        name: str, 
        api_key: Optional[str] = None, 
        base_url: Optional[str] = None
    ) -> BaseAIProvider:
        name_lower = name.lower()
        if name_lower == "gemini":
            return GeminiProvider(api_key=api_key, base_url=base_url)
        elif name_lower in ["claude", "anthropic"]:
            return ClaudeProvider(api_key=api_key, base_url=base_url)
        else:
            # Handles chatanywhere, openai, groq, openrouter, ollama, lm_studio
            return OpenAICompatibleProvider(
                api_key=api_key, 
                base_url=base_url, 
                provider_name=name_lower
            )
