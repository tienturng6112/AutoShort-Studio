import os
import json
import httpx
from typing import Any, Dict, List, Tuple
from backend.providers.speech.base_speech_provider import BaseSpeechProvider

class KiraProvider(BaseSpeechProvider):
    """Voice synthesis adapter leveraging Kira AI's OpenAI-compatible speech endpoint."""
    
    def __init__(self, api_key: str, model: str = "kira-3.0-flash-tts", speed: float = 1.0, base_url: str = None) -> None:
        self._api_key = api_key
        self._model = model
        self._speed = speed
        self._base_url = base_url.rstrip("/") if base_url else "https://kiraai.vn/api/v1"

    async def list_models(self) -> List[str]:
        url = f"{self._base_url}/models"
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
            
        status_code = None
        raw_count = 0
        parsed_count = 0
        models = []
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10.0)
                status_code = resp.status_code
                if resp.status_code == 200:
                    data = resp.json()
                    raw_list = data.get("data", []) if isinstance(data, dict) else data
                    raw_count = len(raw_list)
                    models = [m.get("id") or m.get("name") for m in raw_list if isinstance(m, dict)]
                    parsed_count = len(models)
        except Exception:
            pass
            
        if not models:
            models = ["kira-3.0-flash-tts", "kira-3.0-pro-tts"]
            if self._model and self._model not in models:
                models.insert(0, self._model)
            parsed_count = len(models)
            
        print(f"\n[MODEL REFRESH AUDIT - KIRA]")
        print(f"  Provider:             Kira")
        print(f"  Endpoint:             {url}")
        print(f"  Status Code:          {status_code}")
        print(f"  Raw model count:      {raw_count}")
        print(f"  Parsed model count:   {parsed_count}")
        print(f"  Returned object type: {type(models).__name__}")
        print(f"  Example first model:  {models[0] if models else 'None'}")
        print(f"============================\n")
        
        return models

    async def list_voices(self) -> List[Dict[str, Any]]:
        print(f"\n[KIRA PROVIDER] list_voices called")
        print(f"[KIRA PROVIDER] API key empty? {not self._api_key}")
        print(f"[KIRA PROVIDER] base_url={self._base_url}")
        print(f"[KIRA PROVIDER] model={self._model}")
        
        if not self._api_key:
            print(f"[KIRA PROVIDER] API key is EMPTY -> return []")
            return []
            
        url = f"{self._base_url}/audio/voices"
        print(f"[KIRA PROVIDER] URL={url}")
        headers = {
            "Authorization": f"Bearer {self._api_key}"
        }
        status_code = None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10.0)
                status_code = resp.status_code
                print(f"[KIRA PROVIDER] HTTP status_code={status_code}")
                raw_body = resp.text
                print(f"[KIRA PROVIDER] Raw response body: {repr(raw_body)}")
                if resp.status_code == 200:
                    voices = resp.json()
                    print(f"[KIRA PROVIDER] Parsed response: {json.dumps(voices, ensure_ascii=True)}")
                    results = []
                    data_list = voices
                    if isinstance(voices, dict) and "data" in voices:
                        data_list = voices["data"]
                        
                    for v in data_list:
                        voice_id = v.get("id") or v.get("voice_id") or v.get("name")
                        voice_name = v.get("name") or voice_id
                        print(f"[KIRA PROVIDER] voice: display_name={repr(voice_name)}, voice_id={repr(voice_id)}")
                        results.append({
                            "voice_id": voice_id,
                            "display_name": voice_name,
                            "gender": v.get("gender", "Unknown"),
                            "language": v.get("language") or v.get("locale", "vi"),
                            "provider_id": "kira"
                        })
                    print(f"[KIRA PROVIDER] API success -> {len(results)} voices returned")
                    return results
        except Exception as e:
            print(f"[KIRA PROVIDER] Exception during API call: {repr(e)}")
            
        print(f"[KIRA PROVIDER] API failed (status={status_code}) -> returning empty list")
        return []

    def _translate_error(self, status_code: int) -> str:
        if status_code == 404:
            return "Model không tồn tại hoặc chưa được hỗ trợ."
        elif status_code == 401:
            return "API Key không hợp lệ."
        elif status_code == 429:
            return "Đã hết quota."
        elif status_code == 408:
            return "Không thể kết nối tới Kira."
        return "Lỗi không xác định."

    async def generate(self, text: str, voice_name: str, output_path: str, emotion_profile: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        if not self._api_key:
            raise ValueError("Kira API Key is missing.")
            
        url = f"{self._base_url}/audio/speech"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self._model,
            "input": text,
            "voice": voice_name,
            "speed": self._speed
        }
        
        import wave
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=30.0)
                if resp.status_code != 200:
                    logger.error(f"Raw Kira API Error ({resp.status_code}): {resp.text}")
                    friendly_msg = self._translate_error(resp.status_code)
                    raise RuntimeError(f"Lỗi TTS: {friendly_msg}")
                    
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with wave.open(output_path, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(24000)
                    wav_file.writeframes(resp.content)
                    
                return output_path, []
        except httpx.TimeoutException as e:
            logger.error(f"Raw Kira Timeout Error: {str(e)}")
            raise RuntimeError(f"Lỗi TTS: Không thể kết nối tới Kira.")
        except httpx.RequestError as e:
            logger.error(f"Raw Kira Network Error: {str(e)}")
            raise RuntimeError(f"Lỗi TTS: Không thể kết nối tới Kira.")

    async def preview(self, text: str, voice_name: str, **kwargs) -> bytes:
        if not self._api_key:
            raise ValueError("Kira API Key is missing.")
            
        url = f"{self._base_url}/audio/speech"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self._model,
            "input": text,
            "voice": voice_name,
            "speed": self._speed
        }
        
        import wave
        import io
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=20.0)
                if resp.status_code != 200:
                    logger.error(f"Raw Kira API Error (Preview) ({resp.status_code}): {resp.text}")
                    friendly_msg = self._translate_error(resp.status_code)
                    raise RuntimeError(f"Lỗi TTS: {friendly_msg}")
                
                wav_buf = io.BytesIO()
                with wave.open(wav_buf, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(24000)
                    wav_file.writeframes(resp.content)
                return wav_buf.getvalue()
        except httpx.TimeoutException as e:
            logger.error(f"Raw Kira Timeout Error (Preview): {str(e)}")
            raise RuntimeError(f"Lỗi TTS: Không thể kết nối tới Kira.")
        except httpx.RequestError as e:
            logger.error(f"Raw Kira Network Error (Preview): {str(e)}")
            raise RuntimeError(f"Lỗi TTS: Không thể kết nối tới Kira.")

    async def validate_voice(self, voice_name: str, language: str) -> None:
        is_vietnamese = "vi" in language.lower()
        if is_vietnamese:
            voices = await self.list_voices()
            matched = False
            for v in voices:
                name = v.get("name", "")
                display = v.get("display_name", "")
                if (voice_name.lower() == name.lower() or 
                    voice_name.lower() == display.lower() or 
                    voice_name.lower() in display.lower() or
                    name.lower() in voice_name.lower()):
                    matched = True
                    break
            if not matched:
                raise ValueError(
                    f"Selected voice error: Voice '{voice_name}' is not supported by KiraProvider for Vietnamese."
                )

    async def test_connection(self) -> Dict[str, Any]:
        if not self._api_key:
            return {"success": False, "message": "API Key is empty", "status_code": 401}
            
        url = f"{self._base_url}/audio/voices"
        headers = {
            "Authorization": f"Bearer {self._api_key}"
        }
        import time
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10.0)
                latency = int((time.perf_counter() - start) * 1000)
                if resp.status_code == 200:
                    return {
                        "success": True,
                        "message": "Connected",
                        "status_code": 200,
                        "latency_ms": latency,
                        "models": ["kira-3.0-flash-tts", "kira-3.0-pro-tts"]
                    }
                else:
                    return {"success": False, "message": f"API Error: {resp.text}", "status_code": resp.status_code, "latency_ms": latency}
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return {"success": False, "message": f"Connection Failed: {str(e)}", "latency_ms": latency}
