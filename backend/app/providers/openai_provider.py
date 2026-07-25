import httpx
from typing import List, Optional
from openai import AsyncOpenAI
from backend.app.providers.base import BaseAIProvider

class OpenAICompatibleProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, provider_name: str = "openai"):
        self.api_key = api_key
        self.base_url = base_url
        self.provider_name = provider_name
        
        # Determine base URLs if not provided
        if not self.base_url:
            if provider_name == "chatanywhere":
                self.base_url = "https://api.chatanywhere.tech/v1"
            elif provider_name == "openai":
                self.base_url = "https://api.openai.com/v1"
            elif provider_name == "groq":
                self.base_url = "https://api.groq.com/openai/v1"
            elif provider_name == "openrouter":
                self.base_url = "https://openrouter.ai/api/v1"
            elif provider_name == "ollama":
                self.base_url = "http://localhost:11434/v1"
            elif provider_name == "lm_studio":
                self.base_url = "http://localhost:1234/v1"
                
        # Initialize client
        # Note: ChatAnywhere requires api_key. Ollama does not.
        self.client = AsyncOpenAI(
            api_key=self.api_key or "placeholder_key",
            base_url=self.base_url,
            timeout=30.0
        )
        
    async def test_connection(self) -> bool:
        try:
            # Lightweight check: list models
            await self.client.models.list()
            return True
        except Exception:
            # Fallback check: try a minimal prompt completion
            try:
                model_name = "gpt-3.5-turbo"
                if self.provider_name == "groq":
                    model_name = "llama3-8b-8192"
                elif self.provider_name == "openrouter":
                    model_name = "google/gemma-2-9b-it:free"
                elif self.provider_name == "ollama":
                    model_name = "llama3"
                elif self.provider_name == "lm_studio":
                    model_name = "local-model"
                    
                await self.client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=2
                )
                return True
            except Exception:
                return False
                
    async def list_models(self) -> List[str]:
        try:
            models_response = await self.client.models.list()
            return [model.id for model in models_response.data]
        except Exception:
            # Fallback static models if fetching fails
            if self.provider_name == "chatanywhere":
                return ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-mini"]
            elif self.provider_name == "openai":
                return ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-mini"]
            elif self.provider_name == "groq":
                return ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768", "gemma-7b-it"]
            elif self.provider_name == "openrouter":
                return ["meta-llama/llama-3-8b-instruct:free", "google/gemma-2-9b-it:free"]
            elif self.provider_name == "ollama":
                return ["llama3", "mistral", "phi3"]
            elif self.provider_name == "lm_studio":
                return ["local-model"]
            return []

    async def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        model: Optional[str] = None, 
        json_mode: bool = False
    ) -> str:
        if not model:
            models = await self.list_models()
            model = models[0] if models else "gpt-3.5-turbo"
            
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        extra_args = {}
        if json_mode:
            # Groq, OpenAI, and Ollama support response_format
            if self.provider_name in ["openai", "chatanywhere", "groq", "ollama"]:
                extra_args["response_format"] = {"type": "json_object"}
                # Ensure user prompt includes JSON instructions for OpenAI guidelines
                if "json" not in prompt.lower() and "json" not in (system_prompt or "").lower():
                    messages[-1]["content"] = prompt + "\nReturn response as valid JSON."
                    
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            **extra_args
        )
        return response.choices[0].message.content or ""
