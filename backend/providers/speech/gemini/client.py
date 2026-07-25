import httpx
import base64
import time
from typing import List, Dict, Any, Optional
from .models import GeminiModelInfo, GeminiVoiceInfo

class GeminiSpeechClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
    def _get_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint}?key={self.api_key}"
        
    async def list_models(self) -> List[GeminiModelInfo]:
        if not self.api_key:
            return []
            
        async with httpx.AsyncClient() as client:
            resp = await client.get(self._get_url("models"), timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            
            import logging
            logging.info("Gemini Raw Models JSON: %s", data)
            
            models = []
            for m in data.get("models", []):
                # Filter for models that support GENERATE_CONTENT
                methods = m.get("supportedGenerationMethods", [])
                name = m.get("name", "").replace("models/", "")
                display = m.get("displayName", name)
                
                logging.info("Evaluating Model: %s, Methods: %s", name, methods)
                
                if "generateContent" in methods:
                    caps = ["Chat", "Translation"]
                    
                    # Assume newer models support speech unless explicitly indicated otherwise.
                    # If we don't have a reliable field, we will just add Speech as a potential capability.
                    has_speech = True
                    if "vision" in name.lower():
                        has_speech = False
                    
                    if has_speech: caps.append("Speech (Unknown)")
                    else: caps.append("Speech (Unknown)") # Always append it, let the API decide at generation time
                    if "vision" in name.lower() or "1.5" in name or "2.0" in name: caps.append("Image")
                    if "streamGenerateContent" in methods: caps.append("Streaming")
                    if "thinking" in name.lower() or "pro" in name.lower(): caps.append("Thinking")
                        
                    models.append(GeminiModelInfo(
                        name=name,
                        display_name=display,
                        supports_audio=True, # We will default to True to allow the UI to list it
                        capabilities=caps
                    ))
                    logging.info("Accepted Model: %s, Capabilities: %s", name, caps)
                else:
                    logging.info("Rejected Model: %s (No generateContent method)", name)
            return models
            
    async def list_voices(self) -> List[GeminiVoiceInfo]:
        # Prebuilt voices for Gemini as of mid 2024
        voices = ["Puck", "Charon", "Kore", "Fenrir", "Aoede"]
        return [GeminiVoiceInfo(name=v) for v in voices]
        
    def _decode_error(self, resp: httpx.Response) -> str:
        try:
            return resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            return resp.text
            
    async def generate_speech(self, text: str, model: str, voice: str, language: str, speed: float, pitch: float) -> bytes:
        if not self.api_key:
            raise ValueError("API Key is required")
            
        url = self._get_url(f"models/{model}:generateContent")
        
        # Build prompt considering language, speed and pitch since they aren't explicit API parameters yet
        prompt = f"Please speak the following text in {language}. "
        if speed != 1.0:
            prompt += f"Speak {'faster' if speed > 1 else 'slower'} than normal. "
        if pitch != 0:
            prompt += f"Speak with a {'higher' if pitch > 0 else 'lower'} pitch. "
        prompt += f"Text to speak:\n\n{text}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": voice
                        }
                    }
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=60.0)
            
            if resp.status_code == 401:
                raise ValueError("Unauthorized: Invalid API Key")
            elif resp.status_code == 403:
                raise ValueError("Forbidden: Access Denied")
            elif resp.status_code == 429:
                raise ValueError("Quota Exceeded or Rate Limited")
            elif resp.status_code != 200:
                raise RuntimeError(f"API Error: {self._decode_error(resp)}")
                
            data = resp.json()
            try:
                candidates = data.get("candidates", [])
                if not candidates:
                    raise RuntimeError("No candidates returned from Gemini.")
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part and part["inlineData"]["mimeType"].startswith("audio/"):
                        return base64.b64decode(part["inlineData"]["data"])
                raise RuntimeError("No audio data found in response.")
            except Exception as e:
                if isinstance(e, RuntimeError):
                    raise
                raise RuntimeError(f"Failed to parse audio response: {str(e)}")
