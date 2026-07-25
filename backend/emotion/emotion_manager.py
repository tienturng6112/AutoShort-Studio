import logging
from typing import Optional
from backend.emotion.metadata import EmotionProfile
from backend.speech.models import Transcript

logger = logging.getLogger("EmotionManager")

class EmotionManager:
    """Manages emotional metadata for timeline segments."""
    
    def __init__(self, capability_manager=None, llm_service=None, use_llm: bool = False):
        self.capability_manager = capability_manager
        self.llm_service = llm_service
        self.use_llm = use_llm
        
        # Simple heuristic keywords mapping
        self.heuristic_map = {
            "sad": "Sad",
            "cry": "Sad",
            "angry": "Angry",
            "mad": "Angry",
            "happy": "Happy",
            "glad": "Happy",
            "excited": "Excited",
            "wow": "Excited",
            "!": "Excited"
        }

    async def detect(self, text: str, character_profile=None) -> EmotionProfile:
        """
        Analyzes the text (via heuristics or LLM) to predict an emotion.
        """
        text_lower = text.lower()
        
        if self.use_llm and self.llm_service:
            # Future expansion: LLM semantic detection
            pass
            
        # Fast heuristic
        for keyword, emotion in self.heuristic_map.items():
            if keyword in text_lower:
                intensity = 1.0 if "!" in text or text.isupper() else 0.7
                return EmotionProfile(emotion_id=emotion, intensity=intensity, confidence=80.0)
                
        # Default to character preference if available, else Neutral
        if character_profile and character_profile.emotion_profile and character_profile.emotion_profile != "Neutral":
            return EmotionProfile(emotion_id=character_profile.emotion_profile, intensity=0.5, confidence=100.0)
            
        return EmotionProfile(emotion_id="Neutral", intensity=1.0, confidence=100.0)

    async def apply(self, transcript: Transcript, character_manager=None):
        """
        Batch applies emotion detection across an entire transcript.
        """
        for seg in transcript.segments:
            if not getattr(seg, "emotion", None) or not seg.emotion.get("user_override"):
                char_profile = None
                if character_manager and seg.speaker_id:
                    char_profile = character_manager.resolve_speaker(seg.speaker_id)
                    
                profile = await self.detect(seg.text, character_profile=char_profile)
                # Store as dict in the segment
                seg.emotion = profile.model_dump()

    def validate(self, provider_id: str, emotion_profile: EmotionProfile) -> EmotionProfile:
        """
        Checks if the chosen TTS provider supports the requested emotion.
        """
        if not self.capability_manager:
            return emotion_profile
            
        try:
            # If the provider specifically supports "emotion" capability
            self.capability_manager.require(provider_id, "tts", "emotion")
            emotion_profile.provider_supported = True
        except Exception:
            emotion_profile.provider_supported = False
            logger.debug(f"Provider {provider_id} does not support emotions. Falling back to Neutral.")
            
        return emotion_profile
