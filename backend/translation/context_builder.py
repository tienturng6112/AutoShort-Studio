import json
from typing import List, Dict, Any, Optional
from backend.speech.models import Segment
from backend.translation.scene_builder import SceneBuilder
from backend.translation.conversation_analyzer import ConversationAnalyzerService
from backend.translation.translation_memory import TranslationMemory

class TranslationContextBuilder:
    """Consolidates Scene summaries, speakers, relationships, dialogue history, and Translation Memory."""
    
    def __init__(self, scene_builder: SceneBuilder, analyzer: Optional[ConversationAnalyzerService]):
        self.scene_builder = scene_builder
        self.analyzer = analyzer

    async def build_context_for_scene(
        self,
        scene_segments: List[Segment],
        previous_scene_text: str,
        memory: TranslationMemory
    ) -> str:
        """Constructs the comprehensive context string for the LLM."""
        context_string = ""
        
        # 1. Inject Translation Memory
        tm_string = memory.get_context_string()
        if tm_string:
            context_string += f"--- Project Translation Memory ---\n{tm_string}\n\n"
            
        # 2. Previous Dialogue
        if previous_scene_text:
            context_string += f"--- Previous Dialogue (Context) ---\n{previous_scene_text}\n\n"
            
        # 3. Scene Participants
        speakers_in_scene = list(set([seg.speaker_id for seg in scene_segments if seg.speaker_id]))
        if speakers_in_scene:
            context_string += f"Speakers in this scene: {', '.join(speakers_in_scene)}\n"
            
        # 4. Semantic Scene Analysis (Conversation Analyzer)
        if self.analyzer:
            scene_analysis = await self.analyzer.analyze_scene(scene_segments)
            if scene_analysis:
                context_string += f"\n--- Semantic Scene Analysis ---\n{json.dumps(scene_analysis, indent=2, ensure_ascii=False)}\n"
                
        return context_string
