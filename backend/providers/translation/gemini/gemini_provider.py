import json
import httpx
import time
from typing import Any, Dict, List, Optional
from backend.providers.translation.base_translation_provider import BaseTranslationProvider

class GeminiTranslationProvider(BaseTranslationProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key.strip()
        self.model = model or "gemini-1.5-flash"
        
    async def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "message": "API Key is required", "status_code": None, "models": None, "latency_ms": 0}
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": "Hello, respond with OK"}]}]
        }
        
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                latency = int((time.perf_counter() - start) * 1000)
                if resp.status_code == 200:
                    return {"success": True, "message": "Connected", "status_code": 200, "models": [self.model], "latency_ms": latency}
                else:
                    return {"success": False, "message": f"Gemini API returned status code {resp.status_code}", "status_code": resp.status_code, "models": None, "latency_ms": latency}
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return {"success": False, "message": str(e), "status_code": None, "models": None, "latency_ms": latency}

    async def list_models(self) -> List[str]:
        return [self.model, "gemini-1.5-flash", "gemini-1.5-pro"]

    async def translate_segments(
        self, 
        segments: List[Dict[str, Any]], 
        target_lang: str, 
        glossary: Optional[Dict[str, str]] = None,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise ValueError("Gemini API key is missing.")
            
        system_instruction = f"Translate the following subtitle segments to {target_lang}."
        prompt_content = json.dumps(segments, ensure_ascii=False)
        
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_instruction}\n\nFormat response as a raw JSON list matching the input structure exactly (e.g. [{{'id': 0, 'text': '...'}}]). Text to translate:\n{prompt_content}"}]}
            ],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            text_resp = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text_resp)
