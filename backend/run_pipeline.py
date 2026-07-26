import sys
print("RUN_PIPELINE =", __file__)
print(sys.executable)
print(sys.path)
import argparse
import asyncio
import json
import logging
import os
import shutil
import time
from typing import Any, Dict, Optional
from backend.alignment.alignment_service import TimelineAlignmentService
from backend.media.audio_extractor import AudioExtractor
from backend.media.local_importer import LocalImporter
from backend.media.metadata_extractor import MetadataExtractor


from backend.services.llm_service import LLMService
from backend.services.project_service import ProjectService
from backend.speech.models import Transcript, Segment
from backend.speech.speech_service import SpeechBenchmark
from backend.speech.faster_whisper_provider import FasterWhisperProvider
from backend.speech.model_manager import SpeechModelManager
from backend.speech.speech_service import SpeechService
from backend.providers.translation.base_translation_provider import BaseTranslationProvider
from backend.translation.cache import TranslationCache
from backend.providers.translation.chatanywhere.chatanywhere_provider import ChatAnywhereTranslationProvider
from backend.translation.glossary import GlossaryManager
from backend.translation.translation_service import TranslationService
from backend.providers.speech.edge.edge_tts_provider import EdgeTTSProvider
from backend.tts.voice_cache import VoiceCache
from backend.tts.voice_service import VoiceService
from backend.core.exceptions import TimelineSynchronizationError


class MockTranslationProvider(BaseTranslationProvider):
    """Offline translation provider for robust E2E verification without API keys."""

    async def list_models(self) -> list[str]:
        return ["mock-model"]

    async def translate_segments(self, segments: list, target_lang: str,
                                 glossary=None, context: Optional[str] = None) -> list:
        results = []
        for seg in segments:
            results.append({
                "id": seg["id"],
                "text": f"{seg['text']} [Translated to {target_lang}]"
            })
        return results


def initialize_capability_manager(project_dir):
    from backend.providers.provider_registry import ProviderRegistry
    from backend.providers.provider_capability_manager import ProviderCapabilityManager
    import os

    registry = ProviderRegistry()
    registry.inject_legacy_providers()
    registry.discover_providers(
        os.path.join(
            "backend",
            "plugins",
            "providers"))

    cap_mgr = ProviderCapabilityManager(
        registry, config_dir=os.path.join(
            project_dir, "config"))
    cap_mgr.refresh()
    return cap_mgr


def get_provider_config(settings: dict, provider_key: str) -> dict:
    if not settings:
        return {}
    prov_cfg = settings.get(provider_key)
    if isinstance(prov_cfg, dict) and prov_cfg:
        return prov_cfg
    prov_nested = settings.get("providers", {}).get(provider_key)
    if isinstance(prov_nested, dict):
        return prov_nested
    return {}


def check_pause_sync(project_dir):
    if not project_dir:
        return
    pause_flag = os.path.join(project_dir, "pause.flag")
    if os.path.exists(pause_flag):
        logging.getLogger("PipelineRunner").info("[Pause] Execution paused by user...")
    while os.path.exists(pause_flag):
        time.sleep(0.5)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="AutoShort Studio Alpha 0.1A E2E Pipeline Driver CLI")
    parser.add_argument(
        "--input",
        help="Path to input video file (required for new projects)")
    parser.add_argument(
        "--project-id",
        help="Project ID to resume an existing project")
    parser.add_argument(
        "--source-language",
        default="en",
        help="Speech recognition source language")
    parser.add_argument(
        "--target-language",
        default="es",
        help="Target translation language")
    parser.add_argument(
        "--enhance-speech",
        action="store_true",
        help="Enable AI speech enhancement (Demucs separation)")
    parser.add_argument(
        "--diarize",
        action="store_true",
        help="Enable voice diarization")
    parser.add_argument("--output-mode", help="Output mode selection")
    parser.add_argument(
        "--force-render",
        action="store_true",
        help="Force render all segments and bypass translation review pause")
    args = parser.parse_args()

    if not args.input and not args.project_id:
        parser.error("Either --input or --project-id must be provided.")

    # Load settings to resolve output mode
    settings_path = os.path.join("config", "settings.json")
    settings = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            pass

    output_mode = args.output_mode or settings.get(
        "output_mode", "Subtitle + Voice")
    skip_tts = output_mode == "Subtitle Only"
    skip_video = output_mode in ["Voice Only", "Subtitle + Audio Files"]

    from backend.services.project_repository import ProjectRepository
    from backend.models.project_models import ProjectMetadata, ProjectSnapshot, ExecutionState
    from backend.services.pipeline_state_manager import PipelineStateManager

    project_repo = ProjectRepository()

    if args.project_id:
        project_id = args.project_id
        try:
            project_data = project_repo.load(project_id)
        except FileNotFoundError as err:
            raise FileNotFoundError(f"Error: Project {project_id} not found in repository.") from err

        project_name = project_data.project_name
        project_dir = project_repo.get_project_dir(project_id)
        if project_data.settings_snapshot and project_data.settings_snapshot.output_mode:
            output_mode = project_data.settings_snapshot.output_mode
        skip_tts = output_mode in ["Subtitle Only", "Video có phụ đề", "Sub Only"]
        skip_video = output_mode in ["Voice Only", "Subtitle + Audio Files", "Sub + Audio"]
        args.source_language = project_data.languages.get(
            "source", args.source_language)
        args.target_language = project_data.languages.get(
            "target", args.target_language)
    else:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        project_id = f"project_{timestamp}"
        project_name = f"Project {timestamp}"
        project_dir = project_repo.get_project_dir(project_id)

        snapshot = ProjectSnapshot(output_mode=output_mode)
        exec_state = ExecutionState(status="Running")
        project_data = ProjectMetadata(
            project_id=project_id,
            project_name=project_name,
            created_at=time.time(),
            modified_at=time.time(),
            settings_snapshot=snapshot,
            languages={
                "source": args.source_language,
                "target": args.target_language},
            execution_state=exec_state
        )
        project_repo.save(project_data)

    state_manager = PipelineStateManager(project_id, repository=project_repo)
    state_manager.update_execution_state("Running")

    # Configure simultaneous console and file logging directly inside the
    # project folder
    log_format = "%(asctime)s [%(levelname)s] (%(name)s) %(message)s"
    log_file_path = os.path.join(project_dir, "execution.log")
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
        ]
    )
    logger = logging.getLogger("PipelineRunner")

    # Initialize capability manager
    cap_mgr = initialize_capability_manager(project_dir)

    logger.info("Initializing Alpha 0.1A E2E Pipeline Driver CLI...")
    logger.info(f"Output Mode: {output_mode}")
    start_time = time.perf_counter()

    try:
        # 1. Video Import
        check_pause_sync(project_dir)
        logger.info("Stage 1: Video Import started.")
        video_dir = os.path.join(project_dir, "video")

        if not state_manager.is_completed("stage_1"):
            input_source = args.input or project_data.input_video
            if not input_source:
                raise ValueError(
                    "No input video source specified in arguments or project metadata.")

            is_youtube = input_source.startswith(("http://", "https://"))
            if is_youtube:
                if shutil.which("yt-dlp") is None:
                    raise RuntimeError(
                        "yt-dlp is required to process YouTube URLs.")
                logger.info("Downloading YouTube video...")
                from backend.media.youtube_importer import YoutubeImporter
                importer = YoutubeImporter()
            else:
                logger.info("Importing local video...")
                if not os.path.exists(input_source):
                    raise FileNotFoundError(
                        f"Local input video file not found: {input_source}")
                importer = LocalImporter()

            video_path = await importer.import_media(input_source, video_dir)
            logger.info(f"Imported video saved to: {video_path}")
            state_manager.set_metadata("video_path", video_path)
            state_manager.mark_completed("stage_1")
        else:
            logger.info("Stage 1: Skipped (Already completed).")
            video_path = state_manager.get_metadata("video_path")

        # 2. Audio Extraction
        check_pause_sync(project_dir)
        logger.info("Stage 2: Audio Extraction started.")
        state_manager.update_execution_state(
            "Running", progress=25, current_stage="Stage 2: Audio Extraction")
        audio_dir = os.path.join(project_dir, "audio")
        audio_path = os.path.join(audio_dir, "audio.wav")

        if not state_manager.is_completed("stage_2"):
            metadata = MetadataExtractor.extract_metadata(video_path)
            video_duration = metadata.get("duration", 5.0)
            state_manager.set_metadata("video_duration", video_duration)
            logger.info(
                f"Container metadata resolved: duration={video_duration}s, FPS={metadata.get('fps')}")

            AudioExtractor.extract_audio(video_path, audio_path)
            logger.info(f"Extracted WAV audio saved to: {audio_path}")

            speech_audio_path = audio_path
            if args.enhance_speech:
                logger.info(
                    "Stage 2.5: AI Speech Enhancement (Demucs) started.")
                try:
                    from backend.audio.speech_enhancer import SpeechEnhancer
                    enhancer = SpeechEnhancer()
                    vocals_path, background_path = enhancer.enhance_speech(
                        audio_path=audio_path,
                        output_dir=audio_dir
                    )
                    speech_audio_path = vocals_path
                    logger.info(
                        f"AI Speech Enhancement complete. Vocals track: {vocals_path}, Background track: {background_path}")
                except Exception as e:
                    logger.error(
                        f"Speech enhancement failed, falling back to original audio: {str(e)}")
            state_manager.set_metadata("speech_audio_path", speech_audio_path)
            state_manager.mark_completed("stage_2")
        else:
            logger.info("Stage 2: Skipped (Already completed).")
            speech_audio_path = state_manager.get_metadata(
                "speech_audio_path", audio_path)
            video_duration = state_manager.get_metadata("video_duration", 5.0)

        # 3. Speech Recognition
        check_pause_sync(project_dir)
        logger.info("Stage 3: Speech Recognition started.")
        state_manager.update_execution_state(
            "Running", progress=37, current_stage="Stage 3: Speech Recognition")
        sub_dir = os.path.join(project_dir, "subtitle")
        os.makedirs(sub_dir, exist_ok=True)

        if not state_manager.is_completed("stage_3"):
            # Detect faster-whisper package presence
            try:
                from faster_whisper import WhisperModel
                has_whisper = True
            except ImportError:
                has_whisper = False

            if not has_whisper:
                logger.info(
                    "faster-whisper package not installed. Using local MockSpeechProvider.")
                mock_text = "这是一个关于Alpha 0.1A端到端管道测试的视频。" if args.source_language == "zh" else "This is a test speech verification run for Alpha 0.1A pipeline."
                transcript = Transcript(
                    text=mock_text,
                    language=args.source_language,
                    language_probability=1.0,
                    duration=video_duration,
                    segments=[
                        Segment(
                            id=0,
                            start=0.5,
                            end=max(0.6, video_duration - 0.5),
                            text=mock_text,
                            words=[],
                            confidence=1.0
                        )
                    ]
                )
                with open(os.path.join(sub_dir, "transcript.json"), "w", encoding="utf-8") as f:
                    f.write(transcript.to_json())
                with open(os.path.join(sub_dir, "transcript.srt"), "w", encoding="utf-8") as f:
                    f.write(transcript.to_srt())

                speech_bench = SpeechBenchmark(
                    model="tiny", device="cpu", execution_time_seconds=0.1, realtime_factor=0.02, memory_usage_mb=10.0
                )
            else:
                speech_provider = FasterWhisperProvider()
                speech_model_manager = SpeechModelManager(
                    models_root=os.path.abspath("cache/whisper"))
                speech_service = SpeechService(
                    speech_provider, speech_model_manager)

                transcript, speech_bench = await speech_service.transcribe_audio(
                    audio_path=speech_audio_path,
                    model_size="small",
                    output_dir=sub_dir
                )

            logger.info(
                f"Transcription complete. Segments count: {len(transcript.segments)}")

            # 3.5: Speaker Diarization
            logger.info("Stage 3.5: Speaker Diarization started.")
            from backend.speech.diarization import DiarizationService, PyannoteDiarizationProvider, MockDiarizationProvider

            hf_token = settings.get("hf_token") or os.environ.get("HF_TOKEN")
            diarize_provider = None
            try:
                import pyannote.audio
                if hf_token:
                    diarize_provider = PyannoteDiarizationProvider(
                        hf_token=hf_token)
                else:
                    logger.warning(
                        "HF_TOKEN not found in settings or environment. Falling back to MockDiarizationProvider.")
            except ImportError:
                logger.warning(
                    "pyannote.audio is not installed. Falling back to MockDiarizationProvider.")

            if diarize_provider is None:
                diarize_provider = MockDiarizationProvider()

            diarization_service = DiarizationService(diarize_provider)
            try:
                speaker_map = diarization_service.diarize_transcript(
                    transcript, speech_audio_path)
                speaker_map_path = os.path.join(
                    project_dir, "speaker_map.json")
                with open(speaker_map_path, "w", encoding="utf-8") as f:
                    json.dump(speaker_map, f, indent=4)

                state_manager.set_metadata("speaker_map", speaker_map)
                with open("speaker_map.json", "w", encoding="utf-8") as f:
                    json.dump(speaker_map, f, indent=4)

                with open(os.path.join(sub_dir, "transcript.json"), "w", encoding="utf-8") as f:
                    f.write(transcript.to_json())
                with open(os.path.join(sub_dir, "transcript.srt"), "w", encoding="utf-8") as f:
                    f.write(transcript.to_srt())

                logger.info(
                    f"Speaker diarization complete. Mapped {len(speaker_map)} speaker(s).")
            except Exception as e:
                logger.error(
                    f"Speaker diarization failed: {str(e)}. Continuing without speaker metadata.")

            state_manager.mark_completed("stage_3")
        else:
            logger.info("Stage 3: Skipped (Already completed).")
            with open(os.path.join(sub_dir, "transcript.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
                transcript = Transcript(**data)

            speaker_map = state_manager.get_metadata("speaker_map", {})

        # 3.5: Emotion Analysis
        logger.info("Stage 3.5: Emotion Analysis started.")
        state_manager.update_execution_state(
            "Running", progress=45, current_stage="Stage 3.5: Emotion Analysis")
        from backend.emotion.emotion_manager import EmotionManager
        from backend.character.character_manager import CharacterManager

        emotion_manager = EmotionManager()
        char_mgr = CharacterManager(
            storage_path=os.path.join(
                project_dir, "data/characters.json"))

        await emotion_manager.apply(
            transcript,
            character_manager=char_mgr)

        # Save transcript with emotion metadata
        with open(os.path.join(sub_dir, "transcript.json"), "w", encoding="utf-8") as f:
            f.write(transcript.to_json())

        # 4. Translation
        check_pause_sync(project_dir)
        logger.info("Stage 4: Translation started.")
        state_manager.update_execution_state(
            "Running", progress=50, current_stage="Stage 4: Translation")
        trans_dir = os.path.join(project_dir, "translation")
        os.makedirs(trans_dir, exist_ok=True)

        if not state_manager.is_completed("stage_4"):
            settings_path = os.path.join("config", "settings.json")
            settings = {}
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not load settings.json: {str(e)}")

            from backend.character.character_manager import CharacterManager
            char_mgr = CharacterManager(
                storage_path=os.path.join(
                    project_dir, "data/characters.json"))
            if "speaker_voices" in settings:
                char_mgr.lazy_migrate_settings(settings["speaker_voices"])

            # --- NEW PROVIDER ARCHITECTURE ---
            # 1. Initialize Managers
            from backend.providers.llm.manager import LLMProviderManager
            from backend.providers.translation.manager import TranslationProviderManager
            from backend.providers.speech.manager import SpeechProviderManager

            llm_manager = LLMProviderManager()
            trans_manager = TranslationProviderManager()
            speech_manager = SpeechProviderManager()

            # 2. Init LLM Provider
            llm_type = settings.get("llm_provider", "chatanywhere").lower()
            if llm_type == "chatanywhere":
                from backend.providers.llm.chatanywhere.chatanywhere_provider import ChatAnywhereProvider
                config = settings.get("providers", {}).get("chatanywhere", {})
                llm_prov = ChatAnywhereProvider(
                    "chatanywhere", config.get("api_key"), config.get("base_url"))
                llm_manager.register("chatanywhere", llm_prov)

            # Wrap LLM provider in LLMService
            from backend.services.llm_service import LLMService
            # We must create a mock manager for LLMService to stay compatible with existing code,
            # or just pass the provider. LLMService expects a manager with
            # get_active_provider().

            class LegacyLLMManagerAdapter:
                def __init__(self, p): self.p = p
                def get_active_provider(self): return self.p
            llm_service = LLMService(
                LegacyLLMManagerAdapter(
                    llm_manager.get(llm_type)))

            # 3. Init Translation Provider
            trans_type = settings.get("translation_provider", "deepl").lower()
            translation_provider = None
            if trans_type == "deepl":
                from backend.providers.translation.deepl.deepl_provider import DeepLTranslationProvider
                config = settings.get("providers", {}).get("deepl", {})
                translation_provider = DeepLTranslationProvider(
                    api_key=config.get("api_key"), context=transcript.text if transcript else None)
                trans_manager.register("deepl", translation_provider)
            elif trans_type == "chatanywhere":
                from backend.providers.translation.chatanywhere.chatanywhere_provider import ChatAnywhereTranslationProvider
                config = get_provider_config(settings, "chatanywhere")
                translation_provider = ChatAnywhereTranslationProvider(
                    api_key=config.get("api_key"),
                    base_url=config.get("base_url"),
                    model=config.get("model", "gpt-4o-mini")
                )
                trans_manager.register("chatanywhere", translation_provider)

            if translation_provider is None:
                raise RuntimeError("No Translation provider configured.")

            provider_type = trans_type.capitalize()
            trans_cache = TranslationCache(
                cache_file_path=os.path.join(
                    project_dir, "cache", "translation_cache.json"))
            glossary = GlossaryManager()
            state_file_path = os.path.join(
                project_dir, "cache", "translation_state.json")

            for seg in transcript.segments:
                cached_text = trans_cache.get(seg.text, args.target_language)
                if cached_text is not None:
                    logger.info(
                        f"[DeepLTelemetry] provider={provider_type} latency=0.000s characters={len(seg.text)} retry_count=0 cache_hit_miss=hit")

            use_context_translation = settings.get(
                "use_context_translation", True)

            def build_conversation_analyzer(translation_prov):
                use_analyzer = settings.get("use_conversation_analyzer", True)
                if not use_analyzer:
                    return None
                from backend.translation.conversation_analyzer import ConversationAnalyzerService
                if llm_manager.get(llm_type):
                    return ConversationAnalyzerService(llm_service, model=settings.get(
                        "providers", {}).get(llm_type, {}).get("model", "gpt-4o-mini"))
                return None

            def build_translation_service(provider):
                if use_context_translation:
                    from backend.translation.scene_builder import SceneBuilder
                    from backend.translation.context_builder import TranslationContextBuilder
                    from backend.translation.translation_memory import TranslationMemory
                    from backend.translation.intelligent_engine import IntelligentTranslationEngine

                    analyzer = build_conversation_analyzer(provider)
                    context_builder = TranslationContextBuilder(
                        SceneBuilder(), analyzer)
                    memory = TranslationMemory(project_id=args.project_id)
                    return IntelligentTranslationEngine(
                        provider=provider,
                        cache=trans_cache,
                        glossary_manager=glossary,
                        context_builder=context_builder,
                        translation_memory=memory,
                        character_manager=char_mgr
                    )
                else:
                    return TranslationService(provider, trans_cache, glossary)

            translation_service = build_translation_service(
                translation_provider)
            quality_setting = settings.get("translation_quality", "Balanced")

            translated_transcript = None
            try:
                # Duck typing for the new engine vs old service
                if hasattr(translation_service, "average_quality_score"):
                    translated_transcript = await translation_service.translate_transcript(
                        transcript=transcript, target_lang=args.target_language,
                        quality_setting=quality_setting,
                        state_file_path=state_file_path, output_dir=trans_dir
                    )
                    score = translation_service.average_quality_score
                    print(
                        f"[Translation Quality Score] {score:.1f}%",
                        flush=True)
                else:
                    translated_transcript = await translation_service.translate_transcript(
                        transcript=transcript, target_lang=args.target_language,
                        state_file_path=state_file_path, output_dir=trans_dir
                    )
            except Exception as e:
                if provider_type == "DeepL":
                    deepl_config = settings.get("deepl", {})
                    disable_fallback = deepl_config.get(
                        "disable_fallback", False)
                    if not disable_fallback:
                        logger.warning(
                            f"DeepL translation execution failed ({str(e)}). Falling back to ChatAnywhere...")
                        try:
                            ca_provider = build_chatanywhere()
                            if ca_provider:
                                translation_service = build_translation_service(
                                    ca_provider)
                                if hasattr(translation_service,
                                           "average_quality_score"):
                                    translated_transcript = await translation_service.translate_transcript(
                                        transcript=transcript, target_lang=args.target_language,
                                        quality_setting=quality_setting,
                                        state_file_path=state_file_path, output_dir=trans_dir
                                    )
                                    score = translation_service.average_quality_score
                                    print(
                                        f"[Translation Quality Score] {score:.1f}%",
                                        flush=True)
                                else:
                                    translated_transcript = await translation_service.translate_transcript(
                                        transcript=transcript, target_lang=args.target_language,
                                        state_file_path=state_file_path, output_dir=trans_dir
                                    )
                                logger.info(
                                    "Fallback ChatAnywhere translation complete.")
                        except Exception as fallback_err:
                            logger.error(
                                f"Fallback to ChatAnywhere also failed: {str(fallback_err)}")

                if translated_transcript is None:
                    error_str = str(e).lower()
                    friendly_msg = "Lỗi không xác định từ nhà cung cấp dịch thuật."

                    if "429" in error_str or "too many requests" in error_str or "quota" in error_str:
                        friendly_msg = "Giới hạn quota API hàng ngày đã hết hoặc bạn đang bị chặn do vượt quá số lần yêu cầu."
                    elif "401" in error_str or "invalid api key" in error_str or "unauthorized" in error_str:
                        friendly_msg = "API Key không hợp lệ. Vui lòng kiểm tra lại cấu hình."
                    elif "404" in error_str or "model not found" in error_str:
                        friendly_msg = "Model dịch thuật không tồn tại hoặc bạn không có quyền truy cập."
                    elif "408" in error_str or "timeout" in error_str:
                        friendly_msg = "Quá thời gian kết nối (Timeout). Vui lòng thử lại sau."
                    elif "network" in error_str or "connection" in error_str:
                        friendly_msg = "Lỗi kết nối mạng. Không thể kết nối tới nhà cung cấp."

                    logger.error(
                        f"Translation stage encountered critical failure: {str(e)}. Message: {friendly_msg}")
                    raise RuntimeError(
                        f"Lỗi Dịch Thuật: {friendly_msg} ({str(e)})")
                    raise RuntimeError(
                        f"Lỗi Dịch Thuật: {friendly_msg} ({str(e)})")

            logger.info("Translation complete.")

            # Initialize Review Manager and merge translations
            from backend.translation.review_manager import ReviewManager, ReviewSegment
            from backend.translation.translation_memory import TranslationMemory
            review_mgr = ReviewManager(project_id=project_id)
            memory = TranslationMemory(project_id=project_id)

            for orig_seg, trans_seg in zip(
                    transcript.segments, translated_transcript.segments):
                existing = review_mgr.get_segment(str(orig_seg.id))

                if existing and existing.is_frozen:
                    # Freeze rule: never overwrite
                    trans_seg.text = existing.translated
                    continue

                # Priority: Glossary > User TM > Auto TM > LLM
                # (Assuming Glossary was handled by LLM/Optimizer for now, but we check TM here)
                tm_trans = memory.segments.get(orig_seg.text)
                final_trans = trans_seg.text
                status = "AI Generated"

                if tm_trans:
                    if tm_trans.source == "User Edited":
                        final_trans = tm_trans.translation
                        status = "Reviewed"
                    elif tm_trans.source == "Glossary" or tm_trans.locked:
                        final_trans = tm_trans.translation
                        status = "Locked"
                    else:
                        # Auto TM
                        pass

                trans_seg.text = final_trans

                # Update Review segment
                if existing:
                    existing.translated = final_trans
                    existing.status = status if existing.status == "AI Generated" else existing.status
                    review_mgr.update_segment(existing)
                else:
                    new_seg = ReviewSegment(
                        segment_id=str(orig_seg.id),
                        start_time=orig_seg.start,
                        end_time=orig_seg.end,
                        speaker=orig_seg.speaker_id or "",
                        original=orig_seg.text,
                        translated=final_trans,
                        optimized="",
                        confidence=trans_seg.confidence,
                        status=status
                    )
                    review_mgr.update_segment(new_seg)

            # Re-save translated transcript with any TM overrides
            with open(os.path.join(trans_dir, "translated_transcript.json"), "w", encoding="utf-8") as f:
                f.write(translated_transcript.to_json())

            state_manager.mark_completed("stage_4")
        else:
            logger.info("Stage 4: Skipped (Already completed).")
            with open(os.path.join(trans_dir, "translated_transcript.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
                translated_transcript = Transcript(**data)

        enable_review = settings.get("enable_translation_review", False)
        if enable_review and not args.force_render:
            logger.info(
                "Pipeline Paused: Pending Translation Review. Use 'Render All' in UI to continue.")
            state_manager.update_execution_state(
                "Pending Review", progress=50, current_stage="Translation Review")
            return

        # 5. Timeline Alignment
        check_pause_sync(project_dir)
        logger.info("Stage 5: Timeline Alignment started.")
        state_manager.update_execution_state(
            "Running", progress=62, current_stage="Stage 5: Timeline Alignment")
        if not state_manager.is_completed("stage_5"):
            alignment_service = TimelineAlignmentService()
            aligned_transcript = await alignment_service.align_transcript(
                transcript=translated_transcript,
                output_dir=sub_dir,
                video_duration=video_duration
            )
            logger.info("Timeline alignment complete.")
            state_manager.mark_completed("stage_5")
        else:
            logger.info("Stage 5: Skipped (Already completed).")
            with open(os.path.join(sub_dir, "aligned_transcript.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
                aligned_transcript = Transcript(**data)

        # 6. Voice Synthesis
        tts_bench = None
        if not skip_tts:
            check_pause_sync(project_dir)
            logger.info("Stage 6: Voice Synthesis started.")
            state_manager.update_execution_state("Running", progress=75, current_stage="Stage 6: Voice Synthesis")

            render_dir = os.path.join(project_dir, "render")
            tts_dir = os.path.join(project_dir, "tts")
            os.makedirs(render_dir, exist_ok=True)
            os.makedirs(tts_dir, exist_ok=True)

            if not state_manager.is_completed("stage_6"):
                if "settings" not in locals() or not settings:
                    settings_path = os.path.join("config", "settings.json")
                    settings = {}
                    if os.path.exists(settings_path):
                        try:
                            with open(settings_path, "r", encoding="utf-8") as f:
                                settings = json.load(f)
                        except Exception as e:
                            logger.warning(f"Could not load settings.json in Stage 6: {str(e)}")
                            
                tts_type = settings.get("speech_provider", "edge").lower()
                config = get_provider_config(settings, tts_type)
                if tts_type == "elevenlabs":
                    from backend.providers.speech.elevenlabs.elevenlabs_provider import ElevenLabsProvider
                    tts_provider = ElevenLabsProvider(api_key=config.get("api_key"), model=config.get("model", "eleven_multilingual_v2"))
                else:
                    from backend.providers.speech.edge.edge_tts_provider import EdgeTTSProvider
                    tts_provider = EdgeTTSProvider()

                speech_manager.register(tts_type, tts_provider)

                voice_cache = VoiceCache(cache_dir=os.path.join(project_dir, "cache", "voice_cache"))
                voice_service = VoiceService(tts_provider, voice_cache, temp_dir=os.path.join(project_dir, "cache"))

                # Use VoiceManager to get voices
                from backend.voice.voice_manager import VoiceManager
                voice_manager = VoiceManager(cap_mgr, os.path.join(project_dir, "config", "voice_cache.json"))

                # We need to run refresh in the current event loop since run_pipeline is async
                await voice_manager.refresh(tts_type)

                target_lang = aligned_transcript.language.lower() if aligned_transcript.language else args.target_language.lower()
                
                # === SINGLE SOURCE OF TRUTH: settings.json (do UI ghi) ===
                # Nguồn duy nhất cho voice configuration — KHÔNG dùng settings_snapshot
                selected_voice = settings.get("global_voice", "") or None
                voice_mode = settings.get("voice_mode", "SINGLE")
                speaker_voices = settings.get("speaker_voices", {})
                
                if tts_type == "edge":
                    voice_name = selected_voice if selected_voice else "en-US-GuyNeural"
                else:
                    voice_name = selected_voice
                    # Fallback nếu UI chưa chọn
                    if not voice_name:
                        try:
                            voices = voice_manager.list_voices(provider_id=tts_type)
                            lang_prefix = target_lang.split("-")[0] if target_lang else "en"
                            target_voices = [v for v in voices if lang_prefix in v.language]
                            if target_voices:
                                voice_name = target_voices[0].voice_id
                            elif voices:
                                voice_name = voices[0].voice_id
                        except Exception as e:
                            logger.warning(f"Failed to fetch fallback voices: {e}")


                gen_wav_path, gen_mp3_path, _ = await voice_service.synthesize_transcript(
                    transcript=aligned_transcript,
                    voice_name=voice_name,
                    output_dir=tts_dir,
                    tts_dir=tts_dir,
                    provider_name=tts_type,
                    speaker_voices=speaker_voices if voice_mode == "MULTI" else None
                )

                state_manager.set_metadata("gen_wav_path", gen_wav_path)
                state_manager.set_metadata("gen_mp3_path", gen_mp3_path)

                # Diarization
                if args.diarize:
                    logger.info("Stage 6.5: Voice Diarization.")
                    aligned_transcript = await diarization_service.diarize(
                        aligned_transcript, gen_wav_path, tts_dir)

                logger.info("Voice synthesis completed")
                state_manager.mark_completed("stage_6")
            else:
                logger.info("Stage 6: Skipped (Already completed).")
                with open(os.path.join(tts_dir, "aligned_transcript.json"), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    aligned_transcript = Transcript(**data)
                gen_wav_path = state_manager.get_metadata("gen_wav_path")
                gen_mp3_path = state_manager.get_metadata("gen_mp3_path")
        else:
            logger.info("Stage 6: Voice Synthesis skipped (Subtitle Only mode).")
            gen_wav_path = None
            gen_mp3_path = None

# 7. Export Outputs
        check_pause_sync(project_dir)
        logger.info("Stage 7: Exporting results.")
        state_manager.update_execution_state("Running", progress=87, current_stage="Stage 7: Export")
        voice_wav_dest = None
        voice_mp3_dest = None
        video_dur = state_manager.get_metadata("video_duration", 5.0)
        narr_dur = 0.0
        
        if not state_manager.is_completed("stage_7"):
            if not skip_tts:
                voice_wav_dest = os.path.join(project_dir, "voice.wav")
                voice_mp3_dest = os.path.join(project_dir, "voice.mp3")
                if gen_wav_path and os.path.exists(gen_wav_path):
                    shutil.copy2(gen_wav_path, voice_wav_dest)
                if gen_mp3_path and os.path.exists(gen_mp3_path):
                    shutil.copy2(gen_mp3_path, voice_mp3_dest)
                logger.info(f"Saved voice.wav and voice.mp3 to: {project_dir}")

                try:
                    import wave
                    if voice_wav_dest and os.path.exists(voice_wav_dest):
                        with wave.open(voice_wav_dest, "rb") as wfile:
                            narr_dur = wfile.getnframes() / float(wfile.getframerate())
                except Exception as e:
                    raise RuntimeError(f"Could not verify voice.wav duration: {str(e)}")

                if abs(narr_dur - video_dur) > 0.100:
                    logger.warning(
                        f"Timeline verification mismatch: Narration duration {narr_dur:.3f}s "
                        f"differs from video duration {video_dur:.3f}s by more than 100 ms."
                    )
                logger.info(f"Verification SUCCESS: voice.wav duration ({narr_dur:.3f}s) matches video duration ({video_dur:.3f}s) within 100 ms.")
            else:
                logger.info("Skipping voice file export and duration verification (Subtitle Only mode).")

            # Export subtitle.srt if available
            subtitle_srt_src = os.path.join(project_dir, "subtitle", "aligned_transcript.srt")
            subtitle_srt_dest = os.path.join(project_dir, "subtitle.srt")
            has_subtitles = False
            if os.path.exists(subtitle_srt_src):
                try:
                    shutil.copy2(subtitle_srt_src, subtitle_srt_dest)
                    logger.info(f"Saved subtitle.srt to: {project_dir}")
                    has_subtitles = True
                except Exception as e:
                    logger.warning(f"Could not copy subtitle.srt to project dir: {str(e)}")
            
            state_manager.set_metadata("voice_wav_dest", voice_wav_dest)
            state_manager.set_metadata("voice_mp3_dest", voice_mp3_dest)
            state_manager.set_metadata("narr_dur", narr_dur)
            state_manager.set_metadata("has_subtitles", has_subtitles)
            state_manager.set_metadata("subtitle_srt_dest", subtitle_srt_dest)
            state_manager.mark_completed("stage_7")
        else:
            logger.info("Stage 7: Skipped (Already completed).")
            voice_wav_dest = state_manager.get_metadata("voice_wav_dest")
            voice_mp3_dest = state_manager.get_metadata("voice_mp3_dest")
            narr_dur = state_manager.get_metadata("narr_dur", 0.0)
            has_subtitles = state_manager.get_metadata("has_subtitles", False)
            subtitle_srt_dest = state_manager.get_metadata("subtitle_srt_dest")

        # 8. Video and Audio Composition (Stitch Video)
        final_mp4_dest = os.path.join(project_dir, "final.mp4")
        if not skip_video:
            check_pause_sync(project_dir)
            logger.info("Stage 8: Video and Audio Composition started.")
            state_manager.update_execution_state("Running", progress=95, current_stage="Stage 8: Video rendering")
            if not state_manager.is_completed("stage_8"):
                stitched = False
                import subprocess

                if has_subtitles and subtitle_srt_dest:
                    try:
                        # Fix Windows subtitle path escaping (escape colon for FFmpeg filter)
                        sub_path_fw = subtitle_srt_dest.replace("\\", "/").replace(":", "\\:")
                        if skip_tts:
                            logger.info("Attempting to assemble final.mp4 with burned subtitles (original audio).")
                            cmd = [
                                "ffmpeg", "-y",
                                "-i", video_path,
                                "-c:v", "libx264",
                                "-c:a", "aac",
                                "-vf", f"subtitles='{sub_path_fw}'",
                                final_mp4_dest
                            ]
                        else:
                            logger.info("Attempting to assemble final.mp4 with audio replacement and burned subtitles.")
                            cmd = [
                                "ffmpeg", "-y",
                                "-i", video_path,
                                "-i", voice_wav_dest,
                                "-map", "0:v",
                                "-map", "1:a",
                                "-c:v", "libx264",
                                "-c:a", "aac",
                                "-vf", f"subtitles='{sub_path_fw}'",
                                final_mp4_dest
                            ]
                        result = subprocess.run(cmd, capture_output=True, text=False, check=False)
                        stdout_str = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
                        stderr_str = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
                        if result.returncode != 0:
                            raise subprocess.CalledProcessError(
                                returncode=result.returncode,
                                cmd=cmd,
                                output=stdout_str,
                                stderr=stderr_str
                            )
                        logger.info("Successfully generated final.mp4 with burned subtitles.")
                        stitched = True
                    except Exception as e:
                        logger.warning(f"Failed to generate final.mp4 with burned subtitles: {str(e)}.")
                        if not skip_tts:
                            logger.info("Falling back to audio-only replacement.")
                        else:
                            logger.error("No valid fallback available (Subtitle Only mode).")
                            raise e

                if not stitched and not skip_tts:
                    logger.info("Assembling final.mp4 with audio replacement only (no burned subtitles).")
                    cmd = [
                        "ffmpeg", "-y",
                        "-i", video_path,
                        "-i", voice_wav_dest,
                        "-map", "0:v",
                        "-map", "1:a",
                        "-c:v", "copy",
                        "-c:a", "aac",
                        final_mp4_dest
                    ]
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=False, check=False)
                        stdout_str = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
                        stderr_str = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
                        if result.returncode != 0:
                            raise subprocess.CalledProcessError(
                                returncode=result.returncode,
                                cmd=cmd,
                                output=stdout_str,
                                stderr=stderr_str
                            )
                        logger.info("Successfully generated final.mp4 with audio replacement only.")
                        stitched = True
                    except Exception as e:
                        logger.error(f"Failed to generate final.mp4 during audio-only fallback: {str(e)}")
                        raise e
                
                # Verification step
                if not os.path.exists(final_mp4_dest):
                    raise RuntimeError(f"Expected output video file not found at: {final_mp4_dest}")
                
                state_manager.mark_completed("stage_8")
            else:
                logger.info("Stage 8: Skipped (Already completed).")
        else:
            logger.info("Stage 8: Video and Audio Composition skipped (requested output mode does not compile a final video).")

        # Generate sync_report.json
        sub_dur = aligned_transcript.duration if aligned_transcript and aligned_transcript.segments else 0.0
        diff_ms = abs(video_dur - narr_dur) * 1000.0 if not skip_tts else 0.0
        sync_report = {
            "video_duration": video_dur,
            "narration_duration": narr_dur,
            "subtitle_duration": sub_dur,
            "difference_ms": diff_ms
        }
        try:
            with open(os.path.join(project_dir, "sync_report.json"), "w", encoding="utf-8") as f:
                json.dump(sync_report, f, indent=4)
        except Exception as e:
            logger.warning(f"Failed to save sync_report.json: {str(e)}")

        logger.info("Pipeline execution completed successfully.")
        print("\n=== Pipeline Execution Complete ===")

        end_time = time.perf_counter()
        elapsed = end_time - start_time
        print(f"Total pipeline time: {elapsed:.2f}s")
        print(f"Output directory: {project_dir}")
        print(f"Video: {final_mp4_dest if not skip_video else 'N/A'}")
        print(f"Voice: {voice_wav_dest if not skip_tts else 'N/A'}")
        print(f"Subtitle: {subtitle_srt_dest if has_subtitles else 'N/A'}")
        state_manager.update_execution_state("Completed", progress=100, current_stage="Completed")
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        state_manager.update_execution_state("Failed", progress=0, current_stage=f"Failed: {str(e)[:100]}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
