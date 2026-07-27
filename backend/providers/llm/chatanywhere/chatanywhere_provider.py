import time
from typing import Any, AsyncGenerator, Dict, List, Optional
from openai import OpenAI
from backend.providers.llm.base_llm_provider import BaseLLMProvider
from backend.core.exceptions import AIProviderException

class LLMAPIProvider(BaseLLMProvider):
    """Provider adapter for any endpoint compatible with the OpenAI API."""

    def __init__(self, name: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        super().__init__(name, api_key, base_url)
        self._effective_url: str = base_url or ""
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        """Resolves and returns the OpenAI client instance."""
        if self._client is None:
            if not self.api_key:
                raise AIProviderException("LLM API connection error: API Key must be set.")
            if not self._effective_url:
                raise AIProviderException("LLM API connection error: Base URL must be set.")
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self._effective_url
            )
        return self._client

    async def test_connection(self) -> Dict[str, Any]:
        """Tests the connection and returns a standardized dictionary."""
        start = time.perf_counter()
        try:
            client = self._get_client()
            models_list = client.models.list()
            models = [m.id for m in models_list.data]
            latency = int((time.perf_counter() - start) * 1000)
            return {
                "success": True,
                "message": "Connected",
                "status_code": 200,
                "models": models,
                "latency_ms": latency
            }
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            error_msg = str(e)
            status_code = getattr(e, "status_code", None)
            
            if "401" in error_msg or getattr(e, "status_code", 0) == 401:
                error_msg = "Invalid API Key or Unauthorized"
            elif "timeout" in error_msg.lower():
                error_msg = "Timeout"
            
            return {
                "success": False,
                "message": error_msg,
                "status_code": status_code,
                "models": None,
                "latency_ms": latency
            }

    async def list_models(self) -> List[str]:
        """Queries and returns list of available models using client.models.list().
        
        Returns:
            List[str]: List of model names.
        """
        status_code = None
        raw_count = 0
        parsed_count = 0
        models = []
        raw_response_preview = []
        url = f"{self._effective_url}/models"
        try:
            client = self._get_client()
            models_list = client.models.list()
            raw_response_preview = [m.id for m in models_list.data]
            models = list(raw_response_preview)
            raw_count = len(models_list.data)
            parsed_count = len(models)
            status_code = 200
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to query LLM API models: {e}")

        print(f"\n[LLM API MODEL LISTING AUDIT]")
        print(f"  Provider:             OpenAI-compatible LLM API")
        print(f"  Endpoint:             {url}")
        print(f"  Status Code:          {status_code}")
        print(f"  Raw API count:        {raw_count}")
        print(f"  Raw model IDs:        {raw_response_preview}")
        print(f"  Returned model IDs:   {models}")
        print(f"=======================================\n")
        
        return models

    async def chat(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        model: Optional[str] = None, 
        json_mode: bool = False
    ) -> str:
        try:
            client = self._get_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            model_name = model or "gpt-3.5-turbo"
            response_format = {"type": "json_object"} if json_mode else None

            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                response_format=response_format
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise AIProviderException(f"LLM API chat execution failed: {str(e)}")

    async def stream_chat(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        try:
            client = self._get_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            model_name = model or "gpt-3.5-turbo"
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise AIProviderException(f"LLM API stream execution failed: {str(e)}")

    async def embeddings(self, text: str) -> List[float]:
        try:
            client = self._get_client()
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise AIProviderException(f"LLM API embeddings execution failed: {str(e)}")
