import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import OpenAI

from backend.core.exceptions import AIProviderException
from backend.providers.llm.base_llm_provider import BaseLLMProvider


class OpenAICompatibleLLMProvider(BaseLLMProvider):
    """LLM adapter for endpoints implementing the OpenAI API contract."""

    def __init__(self, name: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        super().__init__(name, api_key, base_url)
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise AIProviderException("LLM API connection error: API Key must be set.")
            if not self.base_url:
                raise AIProviderException("LLM API connection error: Base URL must be set.")
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    async def test_connection(self) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            models = [model.id for model in self._get_client().models.list().data]
            return {
                "success": True,
                "message": "Connected",
                "status_code": 200,
                "models": models,
                "latency_ms": int((time.perf_counter() - start) * 1000),
            }
        except Exception as exc:
            return {
                "success": False,
                "message": str(exc),
                "status_code": getattr(exc, "status_code", None),
                "models": None,
                "latency_ms": int((time.perf_counter() - start) * 1000),
            }

    async def list_models(self) -> List[str]:
        return [model.id for model in self._get_client().models.list().data]

    async def chat(self, prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None, json_mode: bool = False) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = self._get_client().chat.completions.create(
            model=model or "gpt-3.5-turbo",
            messages=messages,
            response_format={"type": "json_object"} if json_mode else None,
        )
        return response.choices[0].message.content or ""

    async def stream_chat(self, prompt: str, system_prompt: Optional[str] = None, model: Optional[str] = None) -> AsyncGenerator[str, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        stream = self._get_client().chat.completions.create(
            model=model or "gpt-3.5-turbo", messages=messages, stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content