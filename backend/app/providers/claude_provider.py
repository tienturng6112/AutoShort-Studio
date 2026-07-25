import httpx
from typing import List, Optional
from backend.app.providers.base import BaseAIProvider

class ClaudeProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.base_url = base_url or "https://api.anthropic.com"
        
    async def test_connection(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/v1/messages"
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                payload = {
                    "model": "claude-3-5-haiku-20241022",
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1
                }
                r = await client.post(url, headers=headers, json=payload, timeout=10.0)
                return r.status_code == 200
        except Exception:
            return False
            
    async def list_models(self) -> List[str]:
        # Anthropic doesn't publish an easy open endpoint for list models
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229"
        ]

    async def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        model: Optional[str] = None, 
        json_mode: bool = False
    ) -> str:
        if not self.api_key:
            raise ValueError("Claude API key is required.")
            
        model = model or "claude-3-5-sonnet-20241022"
        url = f"{self.base_url}/v1/messages"
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Claude handles JSON by asking in user prompt or prefilling assistant response.
        # Anthropic does not support a strict response_format="json" key natively in the same way,
        # but we can enforce it in the prompts.
        if json_mode and "json" not in prompt.lower():
            prompt += "\nOutput ONLY valid JSON. Do not write anything else."
            
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=headers, json=payload, timeout=60.0)
            r.raise_for_status()
            data = r.json()
            try:
                return data["content"][0]["text"]
            except (KeyError, IndexError):
                raise ValueError(f"Invalid Claude response shape: {data}")
