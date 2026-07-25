import httpx
from typing import List, Optional
from backend.app.providers.base import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.base_url = base_url or "https://generativelanguage.googleapis.com"
        
    async def test_connection(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/v1beta/models?key={self.api_key}"
                r = await client.get(url, timeout=10.0)
                return r.status_code == 200
        except Exception:
            return False
            
    async def list_models(self) -> List[str]:
        if not self.api_key:
            return ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/v1beta/models?key={self.api_key}"
                r = await client.get(url, timeout=10.0)
                if r.status_code == 200:
                    data = r.json()
                    models = []
                    for m in data.get("models", []):
                        name = m.get("name", "")
                        methods = m.get("supportedGenerationMethods", [])
                        if "generateContent" in methods:
                            models.append(name.split("/")[-1])
                    return models
        except Exception:
            pass
        return ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]

    async def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        model: Optional[str] = None, 
        json_mode: bool = False
    ) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key is required.")
            
        model = model or "gemini-1.5-flash"
        model_name = model if model.startswith("models/") else f"models/{model}"
        url = f"{self.base_url}/v1beta/{model_name}:generateContent?key={self.api_key}"
        
        contents = [{"parts": [{"text": prompt}]}]
        
        payload = {
            "contents": contents
        }
        
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }
            
        if json_mode:
            payload["generationConfig"] = {
                "responseMimeType": "application/json"
            }
            
        async with httpx.AsyncClient() as client:
            r = await client.post(
                url, 
                json=payload, 
                headers={"Content-Type": "application/json"},
                timeout=60.0
            )
            r.raise_for_status()
            data = r.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                raise ValueError(f"Invalid Gemini response shape: {data}")
