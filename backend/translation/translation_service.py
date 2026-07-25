import os
from typing import Any, Dict, List, Optional
from backend.speech.models import Segment, Transcript
from backend.providers.translation.base_translation_provider import BaseTranslationProvider
from backend.translation.cache import TranslationCache
from backend.translation.chunk_manager import ChunkManager
from backend.translation.glossary import GlossaryManager

class TranslationService:
    """Orchestrates structured text translations, executing retries and caching per segment."""

    def __init__(
        self, 
        provider: BaseTranslationProvider, 
        cache: TranslationCache, 
        glossary_manager: GlossaryManager
    ) -> None:
        self._provider = provider
        self._cache = cache
        self._glossary_manager = glossary_manager

    async def translate_transcript(
        self, 
        transcript: Transcript, 
        target_lang: str, 
        state_file_path: str,
        chunk_size: int = 10,
        max_retries: int = 3,
        output_dir: Optional[str] = None
    ) -> Transcript:
        """Translates all segments inside a Transcript while keeping alignment structures identical.
        
        Args:
            transcript (Transcript): Source transcript input containing segments.
            target_lang (str): Destination language code (e.g. 'vi').
            state_file_path (str): File path to store chunk checkpoint states.
            chunk_size (int): Segment count per chunk.
            max_retries (int): Maximum allowed attempts per failed chunk.
            output_dir (Optional[str]): Location directory to save exported translation formats.
            
        Returns:
            Transcript: The structured translated transcript.
        """
        # Initialize ChunkManager to track task resume state checkpoints
        chunk_manager = ChunkManager(state_file_path, chunk_size, max_retries)
        
        # 1. Parse segments and check cache registry
        input_segments = []
        for seg in transcript.segments:
            cached_text = self._cache.get(seg.text, target_lang)
            input_segments.append({
                "id": seg.id,
                "text": seg.text,
                "cached_translation": cached_text
            })

        chunks = chunk_manager.split_segments(input_segments)
        glossary_instructions = self._glossary_manager.format_for_prompt()
        
        for idx, chunk in enumerate(chunks):
            if output_dir:
                p_dir = os.path.dirname(os.path.abspath(output_dir))
                pause_flag = os.path.join(p_dir, "pause.flag")
                import asyncio
                while os.path.exists(pause_flag):
                    await asyncio.sleep(0.5)
            if chunk_manager.is_chunk_completed(idx):
                continue
                
            # Filter to only non-cached segments for translation
            to_translate = [item for item in chunk if item["cached_translation"] is None]
            translated_chunk_results = []
            
            if to_translate:
                retries = 0
                success = False
                last_err = None
                
                while retries < chunk_manager.max_retries and not success:
                    try:
                        payload = [{"id": item["id"], "text": item["text"]} for item in to_translate]
                        
                        translated_payload = await self._provider.translate_segments(
                            segments=payload,
                            target_lang=target_lang,
                            glossary=glossary_instructions if glossary_instructions else None
                        )
                        
                        translated_map = {item["id"]: item["text"] for item in translated_payload}
                        
                        for item in to_translate:
                            trans_text = translated_map.get(item["id"], item["text"])
                            # Save translation to cache
                            self._cache.set(item["text"], target_lang, trans_text)
                            translated_chunk_results.append({
                                "id": item["id"],
                                "text": trans_text
                            })
                        success = True
                    except Exception as e:
                        retries += 1
                        last_err = e
                        
                if not success:
                    raise RuntimeError(
                        f"Translation failed on chunk {idx} after {retries} retries. "
                        f"Underlying error: {str(last_err)}"
                    )
            
            # Combine cached and newly translated results
            combined_chunk_results = []
            newly_translated_map = {item["id"]: item["text"] for item in translated_chunk_results}
            
            for item in chunk:
                if item["cached_translation"] is not None:
                    combined_chunk_results.append({
                        "id": item["id"],
                        "text": item["cached_translation"]
                    })
                else:
                    combined_chunk_results.append({
                        "id": item["id"],
                        "text": newly_translated_map.get(item["id"], item["text"])
                    })
            
            # Save progress checkpoint
            chunk_manager.save_chunk_translations(idx, combined_chunk_results)

        # 2. Read checkpoints and merge segments back
        merged_translations = {}
        for idx in range(len(chunks)):
            for item in chunk_manager.get_chunk_translations(idx):
                merged_translations[item["id"]] = item["text"]

        translated_segments = []
        consolidated_texts = []
        
        for seg in transcript.segments:
            translated_text = merged_translations.get(seg.id, seg.text)
            
            # ConstructSegment keeping words alignment and duration fields exactly identical
            new_seg = Segment(
                id=seg.id,
                start=seg.start,
                end=seg.end,
                text=translated_text,
                words=seg.words,
                confidence=seg.confidence,
                speaker_id=seg.speaker_id,
                speaker_gender=seg.speaker_gender,
                voice=seg.voice,
                emotion=seg.emotion,
                metadata=seg.metadata.copy() if seg.metadata else {}
            )
            translated_segments.append(new_seg)
            consolidated_texts.append(translated_text)

        translated_transcript = Transcript(
            text=" ".join(consolidated_texts).strip(),
            language=target_lang,
            language_probability=1.0,
            duration=transcript.duration,
            segments=translated_segments
        )

        # 3. Export to files
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
            with open(os.path.join(output_dir, "translated_transcript.json"), "w", encoding="utf-8") as f:
                f.write(translated_transcript.to_json())
                
            with open(os.path.join(output_dir, "translated_transcript.txt"), "w", encoding="utf-8") as f:
                f.write(translated_transcript.to_txt())
                
            with open(os.path.join(output_dir, "translated_transcript.srt"), "w", encoding="utf-8") as f:
                f.write(translated_transcript.to_srt())

        return translated_transcript
