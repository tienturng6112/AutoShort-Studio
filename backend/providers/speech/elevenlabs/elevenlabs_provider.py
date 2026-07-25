import os
import httpx
import time
from typing import Any, Dict, List, Tuple, Optional
from backend.providers.speech.base_speech_provider import BaseSpeechProvider

class ElevenLabsProvider(BaseSpeechProvider):
    """Voice synthesis adapter leveraging ElevenLabs API."""
    
    def __init__(self, api_key: str, model: str = "eleven_multilingual_v2", speed: float = 1.0) -> None:
        self._api_key = api_key
        self._model = model
        self._speed = speed
        self._base_url = "https://api.elevenlabs.io/v1"

    async def test_connection(self) -> Dict[str, Any]:
        if not self._api_key:
            return {"success": False, "message": "API Key is empty", "status_code": 401}
            
        url = f"{self._base_url}/user/subscription"
        headers = {
            "xi-api-key": self._api_key
        }
        
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10.0)
                latency = int((time.perf_counter() - start) * 1000)
                
                if resp.status_code == 200:
                    data = resp.json()
                    tier = data.get("tier", "Unknown")
                    char_count = data.get("character_count", 0)
                    char_limit = data.get("character_limit", 0)
                    
                    # Fetch voices count to return rich status
                    voices_resp = await client.get(f"{self._base_url}/voices", headers=headers, timeout=10.0)
                    voices_count = len(voices_resp.json().get("voices", [])) if voices_resp.status_code == 200 else 0
                    
                    return {
                        "success": True,
                        "message": "Connected",
                        "status_code": 200,
                        "latency_ms": latency,
                        "account_type": tier,
                        "quota_used": char_count,
                        "quota_limit": char_limit,
                        "voices_count": voices_count
                    }
                elif resp.status_code == 401:
                    return {"success": False, "message": "Invalid API Key", "status_code": 401, "latency_ms": latency}
                else:
                    return {"success": False, "message": f"API Error: {resp.text}", "status_code": resp.status_code, "latency_ms": latency}
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return {"success": False, "message": f"Connection Failed: {str(e)}", "latency_ms": latency}

    async def list_models(self) -> List[str]:
        return [
            "eleven_multilingual_v2",
            "eleven_monolingual_v1",
            "eleven_multilingual_v1",
            "eleven_turbo_v2",
            "eleven_turbo_v2_5"
        ]

    async def list_voices(self) -> List[Dict[str, Any]]:
        if not self._api_key:
            return []
            
        url = f"{self._base_url}/voices"
        headers = {
            "xi-api-key": self._api_key
        }
        status_code = None
        raw_count = 0
        parsed_count = 0
        first_id = "None"
        first_name = "None"
        results = []

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10.0)
                status_code = resp.status_code
                if resp.status_code == 200:
                    data = resp.json()
                    voices = data.get("voices", [])
                    raw_count = len(voices)
                    for v in voices:
                        vid = v.get("voice_id")
                        vname = v.get("name")
                        labels = v.get("labels", {})
                        gender = labels.get("gender", "Unknown").capitalize()
                        language = labels.get("language", "en-US")
                        results.append({
                            "voice_id": vid,
                            "name": vname,
                            "display_name": vname,
                            "gender": gender,
                            "language": language,
                            "category": v.get("category"),
                            "description": v.get("description"),
                            "labels": labels,
                            "preview_url": v.get("preview_url"),
                            "provider_id": "elevenlabs"
                        })
                    parsed_count = len(results)
                    if results:
                        first_id = results[0].get("voice_id", "None")
                        first_name = results[0].get("name", "None")
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to fetch ElevenLabs voices: {e}")



        return results

    async def _resolve_voice_id(self, voice_name: str) -> str:
        if not voice_name:
            raise ValueError("ElevenLabs requires a valid voice ID.")
            
        voices = await self.list_voices()
        
        # Check exact ID match first
        for v in voices:
            if v.get("voice_id") == voice_name:
                return voice_name
                
        # Check by name
        for v in voices:
            if v.get("name") == voice_name or v.get("display_name") == voice_name:
                return v.get("voice_id")
                
        raise ValueError(f"Invalid ElevenLabs voice: '{voice_name}'")

    async def generate(self, text: str, voice_name: str, output_path: str, emotion_profile: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        if not self._api_key:
            raise ValueError("ElevenLabs API Key is missing.")
            
        voice_id = await self._resolve_voice_id(voice_name)
        url = f"{self._base_url}/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {
            "model_id": self._model,
            "text": text,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=30.0)
                if resp.status_code != 200:
                    logger.error(f"Raw ElevenLabs API Error ({resp.status_code}): {resp.text}")
                    msg = "Invalid API Key" if resp.status_code == 401 else "Quota Exceeded" if resp.status_code == 429 else resp.text
                    raise RuntimeError(f"ElevenLabs TTS Error: {msg}")
                    
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                    
                return output_path, []
        except Exception as e:
            logger.error(f"ElevenLabs Error: {str(e)}")
            raise RuntimeError(f"ElevenLabs Error: {str(e)}")

    async def preview(self, text: str, voice_name: str, **kwargs) -> bytes:
        import httpx
        if not self._api_key:
            raise ValueError("ElevenLabs API Key is missing for preview.")
            
        try:
            voice_id = await self._resolve_voice_id(voice_name)
        except Exception:
            return b""
            
        url = f"{self._base_url}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {
            "model_id": self._model,
            "text": text,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=15.0)
                if resp.status_code == 200:
                    return resp.content
        except Exception:
            pass
        return b""

    async def validate_voice(self, voice_name: str, language: str) -> None:
        await self._resolve_voice_id(voice_name)
