import json
import logging
import os
from typing import Optional
from backend.speech.models import Transcript
from backend.providers.translation.base_translation_provider import BaseTranslationProvider
from backend.translation.cache import TranslationCache
from backend.translation.glossary import GlossaryManager
from backend.translation.scene_builder import SceneBuilder
from backend.translation.conversation_analyzer import ConversationAnalyzerService

logger = logging.getLogger("ContextTranslationService")

class ContextTranslationService:
    """Translates segments scene-by-scene to provide conversational context to the LLM."""
    
    def __init__(
        self, 
        provider: BaseTranslationProvider, 
        cache: TranslationCache, 
        glossary_manager: GlossaryManager,
        scene_builder: SceneBuilder,
        analyzer: Optional[ConversationAnalyzerService] = None
    ) -> None:
        self._provider = provider
        self._cache = cache
        self._glossary_manager = glossary_manager
        self._scene_builder = scene_builder
        self._analyzer = analyzer

    async def translate_transcript(
        self, 
        transcript: Transcript, 
        target_lang: str, 
        state_file_path: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> Transcript:
        """Translates segments scene-by-scene and returns the modified transcript."""
        # Build scenes
        scenes = self._scene_builder.build_scenes(transcript.segments)
        glossary_instructions = self._glossary_manager.format_for_prompt()
        
        previous_scene_text = ""
        
        for idx, scene_segments in enumerate(scenes, start=1):
            if output_dir:
                scene_file = os.path.join(output_dir, f"scene_{idx:03d}.json")
                try:
                    with open(scene_file, "w", encoding="utf-8") as f:
                        json.dump([s.model_dump() for s in scene_segments], f, indent=2, ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"Could not save scene cache {scene_file}: {e}")

            # Check cache for all segments in this scene
            to_translate = []
            for seg in scene_segments:
                cached_text = self._cache.get(seg.text, target_lang)
                if not cached_text:
                    to_translate.append(seg)
                    
            if not to_translate:
                # All segments are already cached
                previous_scene_text = "\n".join([f"{seg.speaker_id or 'Unknown'}: {self._cache.get(seg.text, target_lang)}" for seg in scene_segments])
                continue
                
            payload = [{"id": seg.id, "text": seg.text} for seg in to_translate]
            
            scene_analysis = None
            if self._analyzer:
                scene_analysis = await self._analyzer.analyze_scene(scene_segments)
                if output_dir and scene_analysis:
                    analysis_file = os.path.join(output_dir, f"scene_analysis_{idx:03d}.json")
                    try:
                        with open(analysis_file, "w", encoding="utf-8") as f:
                            json.dump(scene_analysis, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        logger.warning(f"Could not save scene analysis {analysis_file}: {e}")
            
            # Build Context String
            context_string = ""
            if previous_scene_text:
                context_string += f"Previous Dialogue:\n{previous_scene_text}\n\n"
            
            speakers_in_scene = list(set([seg.speaker_id for seg in scene_segments if seg.speaker_id]))
            if speakers_in_scene:
                context_string += f"Speakers in this scene: {', '.join(speakers_in_scene)}\n"
                
            if scene_analysis:
                context_string += f"\nSemantic Scene Analysis:\n{json.dumps(scene_analysis, indent=2, ensure_ascii=False)}\n"
                
            retries = 3
            success = False
            last_err = None
            
            while retries > 0 and not success:
                try:
                    translated_payload = await self._provider.translate_segments(
                        segments=payload,
                        target_lang=target_lang,
                        glossary=glossary_instructions if glossary_instructions else None,
                        context=context_string if context_string else None
                    )
                    
                    translated_map = {item["id"]: item["text"] for item in translated_payload}
                    
                    # Update cache
                    for seg in to_translate:
                        trans_text = translated_map.get(seg.id, seg.text)
                        self._cache.set(seg.text, target_lang, trans_text)
                        
                    success = True
                except Exception as e:
                    retries -= 1
                    last_err = e
                    
            if not success:
                logger.error(f"Failed to translate scene {idx}: {last_err}")
                raise RuntimeError(f"Translation failed on scene {idx}: {last_err}")
                
            # Update previous scene text for the next iteration based on what we just translated
            current_translated = []
            for seg in scene_segments:
                txt = self._cache.get(seg.text, target_lang) or seg.text
                current_translated.append(f"{seg.speaker_id or 'Unknown'}: {txt}")
            previous_scene_text = "\n".join(current_translated)

        # Map translations back to the original transcript segments
        for seg in transcript.segments:
            cached_text = self._cache.get(seg.text, target_lang)
            if cached_text:
                seg.text = cached_text
                
        return transcript
