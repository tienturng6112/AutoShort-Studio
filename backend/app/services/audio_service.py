import os
import uuid
import httpx
from pathlib import Path
import edge_tts
from typing import Optional, List, Dict, Any
from backend.app.core.config import settings

class AudioService:
    def __init__(self, voices_dir: str = "voices"):
        self.voices_dir = Path(voices_dir).resolve()
        if not self.voices_dir.exists():
            self.voices_dir = Path("../voices").resolve()
        self.voices_dir.mkdir(parents=True, exist_ok=True)

    async def list_voices(self, voice_type: str = "edge") -> List[Dict[str, Any]]:
        """List available voices for the given provider."""
        if voice_type == "edge":
            try:
                voices = await edge_tts.list_voices()
                return [
                    {
                        "id": v["ShortName"],
                        "name": v["FriendlyName"],
                        "gender": v["Gender"],
                        "language": v["Locale"]
                    }
                    for v in voices
                ]
            except Exception as e:
                print(f"Error fetching edge-tts voices: {e}")
                return [
                    {"id": "vi-VN-HoaiMyNeural", "name": "Hoai My (Vietnamese)", "gender": "Female", "language": "vi-VN"},
                    {"id": "vi-VN-NamMinhNeural", "name": "Nam Minh (Vietnamese)", "gender": "Male", "language": "vi-VN"},
                    {"id": "en-US-EmmaNeural", "name": "Emma (English)", "gender": "Female", "language": "en-US"},
                    {"id": "en-US-BrianNeural", "name": "Brian (English)", "gender": "Male", "language": "en-US"}
                ]
        elif voice_type == "openai":
            return [
                {"id": "alloy", "name": "Alloy", "gender": "Neutral", "language": "en-US"},
                {"id": "echo", "name": "Echo", "gender": "Male", "language": "en-US"},
                {"id": "fable", "name": "Fable", "gender": "Neutral", "language": "en-US"},
                {"id": "onyx", "name": "Onyx", "gender": "Male", "language": "en-US"},
                {"id": "nova", "name": "Nova", "gender": "Female", "language": "en-US"},
                {"id": "shimmer", "name": "Shimmer", "gender": "Female", "language": "en-US"}
            ]
        elif voice_type == "elevenlabs":
            return [
                {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "Female", "language": "en-US"},
                {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "Female", "language": "en-US"},
                {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "Female", "language": "en-US"},
                {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "Male", "language": "en-US"}
            ]
        return []

    async def generate_tts(
        self,
        text: str,
        voice_type: str = "edge",
        voice_name: str = "vi-VN-HoaiMyNeural",
        api_key: Optional[str] = None,
        output_name: Optional[str] = None
    ) -> tuple[str, list[dict[str, Any]]]:
        """Generates TTS audio file and returns its path and word boundaries."""
        if not output_name:
            output_name = f"tts_{uuid.uuid4().hex}.mp3"
            
        output_path = self.voices_dir / output_name
        word_boundaries = []
        
        if voice_type == "edge":
            communicate = edge_tts.Communicate(text, voice_name)
            with open(output_path, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        # Convert ticks (100ns units) to seconds
                        word_boundaries.append({
                            "text": chunk["text"],
                            "start": chunk["offset"] / 10000000.0,
                            "end": (chunk["offset"] + chunk["duration"]) / 10000000.0
                        })
            
        elif voice_type == "openai":
            if not api_key:
                raise ValueError("OpenAI API Key is required for OpenAI TTS")
            
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            response = await client.audio.speech.create(
                model="tts-1",
                voice=voice_name,
                input=text
            )
            content = await response.aread()
            with open(output_path, "wb") as f:
                f.write(content)
                
        elif voice_type == "elevenlabs":
            if not api_key:
                raise ValueError("ElevenLabs API Key is required")
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_name}"
            headers = {
                "xi-api-key": api_key,
                "accept": "audio/mpeg",
                "content-type": "application/json"
            }
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1"
            }
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json=payload, headers=headers, timeout=60.0)
                r.raise_for_status()
                with open(output_path, "wb") as f:
                    f.write(r.content)
        else:
            raise ValueError(f"Unsupported voice type: {voice_type}")
            
        return str(output_path.resolve()), word_boundaries
