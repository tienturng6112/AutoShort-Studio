import httpx
import time
from typing import Any, Dict, List, Optional
from backend.providers.translation.base_translation_provider import BaseTranslationProvider

class GoogleTranslationProvider(BaseTranslationProvider):
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key.strip()
        
    async def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "message": "API Key is required", "status_code": None, "models": None, "latency_ms": 0}
        
        url = f"https://translation.googleapis.com/language/translate/v2?key={self.api_key}"
        payload = {
            "q": ["Hello"],
            "target": "vi"
        }
        
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                latency = int((time.perf_counter() - start) * 1000)
                if resp.status_code == 200:
                    return {"success": True, "message": "Connected", "status_code": 200, "models": ["default"], "latency_ms": latency}
                else:
                    return {"success": False, "message": f"Google API returned status code {resp.status_code}", "status_code": resp.status_code, "models": None, "latency_ms": latency}
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return {"success": False, "message": str(e), "status_code": None, "models": None, "latency_ms": latency}

    async def list_models(self) -> List[str]:
        return ["default"]

    async def translate_segments(
        self, 
        segments: List[Dict[str, Any]], 
        target_lang: str, 
        glossary: Optional[Dict[str, str]] = None,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise ValueError("Google API key is missing.")
            
        texts = [seg["text"] for seg in segments]
        url = f"https://translation.googleapis.com/language/translate/v2?key={self.api_key}"
        payload = {
            "q": texts,
            "target": target_lang
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            translations = data.get("data", {}).get("translations", [])
            result = []
            for i, seg in enumerate(segments):
                translated_text = translations[i]["translatedText"] if i < len(translations) else seg["text"]
                result.append({
                    "id": seg["id"],
                    "text": translated_text
                })
            return result
