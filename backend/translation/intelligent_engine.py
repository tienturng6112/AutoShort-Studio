import json
import logging
import os
from typing import Optional, List
from backend.speech.models import Transcript
from backend.translation.cache import TranslationCache
from backend.translation.glossary import GlossaryManager
from backend.translation.scene_builder import SceneBuilder
from backend.translation.context_builder import TranslationContextBuilder
from backend.translation.post_optimizer import PostTranslationOptimizer
from backend.translation.translation_memory import TranslationMemory
from backend.providers.translation.base_translation_provider import BaseTranslationProvider

logger = logging.getLogger("IntelligentTranslationEngine")

class IntelligentTranslationEngine:
    """New translation orchestrator supporting Context, Memory, Optimizer, and Quality Scores."""
    
    def __init__(
        self,
        provider: BaseTranslationProvider,
        cache: TranslationCache,
        glossary_manager: GlossaryManager,
        context_builder: TranslationContextBuilder,
        translation_memory: TranslationMemory,
        character_manager=None
    ):
        self._provider = provider
        self._cache = cache
        self._glossary_manager = glossary_manager
        self._context_builder = context_builder
        self._memory = translation_memory
        self._character_manager = character_manager
        
        self.average_quality_score = 0.0

    async def translate_transcript(
        self,
        transcript: Transcript,
        target_lang: str,
        quality_setting: str = "Balanced",
        state_file_path: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> Transcript:
        scenes = self._context_builder.scene_builder.build_scenes(transcript.segments)
        glossary_instructions = self._glossary_manager.format_for_prompt()
        
        previous_scene_text = ""
        total_confidence = 0
        total_segments = 0
        
        for idx, scene_segments in enumerate(scenes, start=1):
            if output_dir:
                p_dir = os.path.dirname(os.path.abspath(output_dir))
                pause_flag = os.path.join(p_dir, "pause.flag")
                import asyncio
                while os.path.exists(pause_flag):
                    await asyncio.sleep(0.5)
                scene_file = os.path.join(output_dir, f"scene_{idx:03d}.json")
                try:
                    with open(scene_file, "w", encoding="utf-8") as f:
                        json.dump([s.model_dump() for s in scene_segments], f, indent=2, ensure_ascii=False)
                except Exception as e:
                    logger.warning(f"Could not save scene cache {scene_file}: {e}")

            to_translate = []
            for seg in scene_segments:
                cached_text = self._cache.get(seg.text, target_lang)
                if not cached_text:
                    to_translate.append(seg)
                    
            if not to_translate:
                # All cached
                previous_scene_text = "\n".join([f"{seg.speaker_id or 'Unknown'}: {self._cache.get(seg.text, target_lang)}" for seg in scene_segments])
                continue
                
            payload = [{"id": seg.id, "text": seg.text} for seg in to_translate]
            
            # Build intelligent context
            context_string = await self._context_builder.build_context_for_scene(
                scene_segments, previous_scene_text, self._memory
            )
            
            # Inject Character Context
            if self._character_manager:
                char_context = []
                for seg in to_translate:
                    if seg.speaker_id:
                        profile = self._character_manager.resolve_speaker(seg.speaker_id)
                        if profile and (profile.gender != "Unknown" or profile.estimated_age or profile.emotion_profile != "Neutral"):
                            info = f"{seg.speaker_id} is {profile.display_name} ("
                            traits = []
                            if profile.gender != "Unknown": traits.append(profile.gender)
                            if profile.estimated_age: traits.append(f"{profile.estimated_age}yo")
                            if profile.emotion_profile != "Neutral": traits.append(profile.emotion_profile)
                            info += ", ".join(traits) + ")"
                            if info not in char_context:
                                char_context.append(info)
                if char_context:
                    if context_string:
                        context_string += "\n\nSpeaker Context:\n- " + "\n- ".join(char_context)
                    else:
                        context_string = "Speaker Context:\n- " + "\n- ".join(char_context)
                        
            # Inject Segment Emotion Context
            emotion_context = []
            for seg in to_translate:
                if hasattr(seg, "emotion") and seg.emotion and seg.emotion.get("emotion_id") != "Neutral":
                    emotion_id = seg.emotion.get("emotion_id")
                    intensity = seg.emotion.get("intensity", 1.0)
                    desc = "strong" if intensity > 0.8 else "mild"
                    emotion_context.append(f"Segment '{seg.text}' is spoken with {desc} {emotion_id} emotion.")
                    
            if emotion_context:
                if context_string:
                    context_string += "\n\nEmotion Context:\n- " + "\n- ".join(emotion_context)
                else:
                    context_string = "Emotion Context:\n- " + "\n- ".join(emotion_context)
            
            retries = 3
            success = False
            last_err = None
            
            while retries > 0 and not success:
                try:
                    # Pass the extended quality config to the provider if supported
                    if hasattr(self._provider, "set_quality"):
                        self._provider.set_quality(quality_setting)
                        
                    translated_payload = await self._provider.translate_segments(
                        segments=payload,
                        target_lang=target_lang,
                        glossary=glossary_instructions if glossary_instructions else None,
                        context=context_string if context_string else None
                    )
                    
                    # Post-optimize and capture confidence
                    translated_map = {}
                    for item in translated_payload:
                        item = PostTranslationOptimizer.optimize(item)
                        translated_map[item["id"]] = item["text"]
                        
                        conf = item.get("confidence", 90) # default to 90 if provider didn't return
                        total_confidence += conf
                        total_segments += 1
                        
                        # Optionally intercept new TM terms here (skipped for simplicity unless schema explicitly returned them)
                        
                    # Update cache
                    for seg in to_translate:
                        trans_text = translated_map.get(seg.id, seg.text)
                        self._cache.set(seg.text, target_lang, trans_text)
                        
                    success = True
                except Exception as e:
                    retries -= 1
                    last_err = e
                    logger.warning(f"Scene {idx} translation failed, retrying... {e}")
                    
            if not success:
                logger.error(f"Failed to translate scene {idx}: {last_err}")
                raise RuntimeError(f"Translation failed on scene {idx}: {last_err}")
                
            # Update previous scene text
            current_translated = []
            for seg in scene_segments:
                txt = self._cache.get(seg.text, target_lang) or seg.text
                current_translated.append(f"{seg.speaker_id or 'Unknown'}: {txt}")
            previous_scene_text = "\n".join(current_translated)

        # Map back to original
        for seg in transcript.segments:
            cached_text = self._cache.get(seg.text, target_lang)
            if cached_text:
                seg.text = cached_text
        
        # Rebuild top-level text from translated segments and update language
        transcript.text = " ".join(seg.text.strip() for seg in transcript.segments).strip()
        transcript.language = target_lang
                
        # Calculate score
        if total_segments > 0:
            self.average_quality_score = total_confidence / total_segments
        else:
            self.average_quality_score = 100.0
            
        logger.info(f"Intelligent Translation Complete. Average Confidence: {self.average_quality_score:.1f}%")
        # Save memory state
        self._memory.save()
        
        return transcript
