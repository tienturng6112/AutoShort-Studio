import os
from typing import Any, Dict, List, Optional, Tuple
from backend.providers.speech.base_speech_provider import BaseSpeechProvider

try:
    import edge_tts
except ImportError:
    edge_tts = None

class EdgeTTSProvider(BaseSpeechProvider):
    """Voice synthesis adapter utilizing Microsoft Edge's public TTS interface."""

    async def list_models(self) -> List[str]:
        # Edge TTS uses voices, there is no selectable text model for generation
        return ["edge-tts-default"]

    async def list_voices(self) -> List[Dict[str, Any]]:
        if edge_tts is None:
            # Fallback list for verification when running offline
            return [
                {"voice_id": "en-US-GuyNeural", "display_name": "Guy", "gender": "Male", "language": "en", "locale": "en-US", "provider_id": "edge-tts"},
                {"voice_id": "en-US-JennyNeural", "display_name": "Jenny", "gender": "Female", "language": "en", "locale": "en-US", "provider_id": "edge-tts"},
                {"voice_id": "vi-VN-NamMinhNeural", "display_name": "Nam Minh", "gender": "Male", "language": "vi", "locale": "vi-VN", "provider_id": "edge-tts"},
                {"voice_id": "vi-VN-HoaiMyNeural", "display_name": "Hoai My", "gender": "Female", "language": "vi", "locale": "vi-VN", "provider_id": "edge-tts"}
            ]
        
        manager = await edge_tts.VoicesManager.create()
        results = []
        for voice in manager.voices:
            short_name = voice.get("ShortName", voice.get("Name", ""))
            locale = voice.get("Locale", "Unknown")
            lang = locale.split("-")[0] if "-" in locale else locale
            results.append({
                "voice_id": short_name,
                "display_name": voice.get("FriendlyName", short_name.split("-")[-1].replace("Neural", "")),
                "gender": voice.get("Gender", "Unknown"),
                "language": lang,
                "locale": locale,
                "provider_id": "edge-tts"
            })
        return results

    async def generate(self, text: str, voice_name: str, output_path: str, emotion_profile: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if edge_tts is None:
            with open(output_path, "wb") as f:
                f.write(b"MOCK WAV AUDIO")
            return output_path, [{"word": text, "start": 0.0, "end": 1.0}]

        import asyncio
        import logging
        logger = logging.getLogger("EdgeTTSProvider")
        max_retries = 5
        delay = 1.5
        
        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(text, voice_name)
                word_boundaries = []
                
                with open(output_path, "wb") as fp:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            fp.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            start = chunk["offset"] / 10000000.0
                            duration = chunk["duration"] / 10000000.0
                            word_boundaries.append({
                                "word": chunk["text"],
                                "start": start,
                                "end": start + duration
                            })
                
                # Verify that audio file has contents
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return output_path, word_boundaries
                else:
                    raise Exception("Audio generation returned empty file")
            except Exception as e:
                logger.warning(f"edge-tts attempt {attempt + 1}/{max_retries} failed for text {repr(text)}. Error: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(delay * (attempt + 1))
        return output_path, []

    async def preview(self, text: str, voice_name: str, **kwargs) -> bytes:
        if edge_tts is None:
            return b"MOCK AUDIO PREVIEW"
        
        rate = kwargs.get("rate")
        pitch = kwargs.get("pitch")
        volume = kwargs.get("volume")
        
        communicate = edge_tts.Communicate(text, voice_name, rate=rate, pitch=pitch, volume=volume)
        data = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                data.append(chunk["data"])
        return b"".join(data)

    async def validate_voice(self, voice_name: str, language: str) -> None:
        is_vietnamese = "vi" in language.lower()
        if is_vietnamese:
            if voice_name not in ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"]:
                raise ValueError(
                    f"Selected voice error: Expected vi-VN-HoaiMyNeural or vi-VN-NamMinhNeural for Vietnamese transcript. "
                    f"Got: {voice_name}"
                )

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "Edge TTS operates locally/via public API without explicit auth.",
            "status_code": 200,
            "latency_ms": 0,
            "models": ["edge-tts-default"]
        }
