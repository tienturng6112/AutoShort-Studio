import json
import logging
from typing import Any, Dict, List
from backend.services.conversation import Conversation
from backend.services.llm_service import ILLMService
from backend.speech.models import Segment

logger = logging.getLogger("ConversationAnalyzerService")

class ConversationAnalyzerService:
    """Performs semantic analysis on a group of scene segments using an LLM."""
    
    def __init__(self, llm_service: ILLMService, model: str = "gpt-4o-mini", llm_provider_id: str = "llm") -> None:
        self._llm = llm_service
        self._model = model
        self._llm_provider_id = llm_provider_id
        
    async def analyze_scene(self, segments: List[Segment]) -> Dict[str, Any]:
        """Analyzes a scene and returns structural/emotional context."""
        if not segments:
            return {}
            
        system_instruction = (
            "You are a Conversation Analyzer for video subtitles. "
            "Your job is to read the provided scene transcript and analyze its context. "
            "DO NOT TRANSLATE. DO NOT output conversational text. ONLY output raw valid JSON.\n\n"
            "Return JSON matching exactly this schema:\n"
            "{\n"
            '  "scene_type": "string (e.g. Argument, Casual, Professional, Romantic)",\n'
            '  "participants": ["string list of speaker IDs"],\n'
            '  "speaker_roles": {"SpeakerID": "Inferred role, e.g. Boss, Friend, Customer"},\n'
            '  "relationship_graph": "string describing power dynamics or relationships",\n'
            '  "estimated_emotional_tone": "string",\n'
            '  "confidence_score": 0.95\n'
            "}"
        )
        
        dialogue = []
        for seg in segments:
            spk = seg.speaker_id or "Unknown"
            dialogue.append(f"[{spk}]: {seg.text}")
            
        prompt_content = "\n".join(dialogue)
        
        conv = Conversation(system_message=system_instruction)
        conv.add_user_message(f"Analyze this scene:\n\n{prompt_content}")
        
        try:
            response_text = await self._llm.chat(conv, model=self._model, json_mode=False, provider_id=self._llm_provider_id)
            
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```"):
                lines = cleaned_text.splitlines()
                if lines[0].strip().startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                cleaned_text = "\n".join(lines).strip()
                
            data = json.loads(cleaned_text)
            return data
        except Exception as e:
            logger.warning(f"Conversation analysis failed: {str(e)}")
            return {}
