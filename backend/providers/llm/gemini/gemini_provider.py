from typing import Generator, List, Optional, Dict, Any
from backend.providers.llm.base_llm_provider import BaseLLMProvider

class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self, name: str, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        super().__init__(name, api_key, base_url)
        self.model = model or "gemini-1.5-flash"
        
    async def test_connection(self) -> Dict[str, Any]:
        return {"success": True, "message": "Connected", "status_code": 200, "models": ["gemini-1.5-flash"], "latency_ms": 10}

    async def list_models(self) -> List[str]:
        return ["gemini-1.5-flash", "gemini-1.5-pro"]

    async def chat(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        model: Optional[str] = None, 
        json_mode: bool = False
    ) -> str:
        return "Gemini stub response"

    async def stream_chat(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        model: Optional[str] = None
    ):
        yield "Gemini stub response"
