from typing import Generator, List, Optional, Dict, Any
from backend.providers.llm.base_llm_provider import BaseLLMProvider

class ClaudeLLMProvider(BaseLLMProvider):
    def __init__(self, name: str, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        super().__init__(name, api_key, base_url)
        self.model = model or "claude-3-haiku-20240307"
        
    async def test_connection(self) -> Dict[str, Any]:
        return {"success": True, "message": "Connected", "status_code": 200, "models": ["claude-3-haiku-20240307"], "latency_ms": 10}

    async def list_models(self) -> List[str]:
        return ["claude-3-haiku-20240307", "claude-3-5-sonnet-20240620"]

    async def chat(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        model: Optional[str] = None, 
        json_mode: bool = False
    ) -> str:
        return "Claude stub response"

    async def stream_chat(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        model: Optional[str] = None
    ):
        yield "Claude stub response"
