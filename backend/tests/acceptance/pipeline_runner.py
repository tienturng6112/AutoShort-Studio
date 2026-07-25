import os
from typing import Any, Dict
from backend.alignment.alignment_service import TimelineAlignmentService
from backend.media.audio_extractor import AudioExtractor
from backend.media.local_importer import LocalImporter
from backend.media.metadata_extractor import MetadataExtractor
from backend.media.youtube_importer import YoutubeImporter
from backend.services.llm_service import ILLMService
from backend.services.project_service import ProjectService
from backend.speech.faster_whisper_provider import FasterWhisperProvider
from backend.speech.model_manager import SpeechModelManager
from backend.speech.speech_service import SpeechService
from backend.translation.cache import TranslationCache
from backend.providers.translation.chatanywhere.chatanywhere_provider import ChatAnywhereTranslationProvider
from backend.translation.glossary import GlossaryManager
from backend.translation.translation_service import TranslationService
from backend.tts.edge_tts_provider import EdgeTTSProvider
from backend.tts.voice_cache import VoiceCache
from backend.tts.voice_service import VoiceService

class PipelineRunner:
    """Runs the media generation pipeline step-by-step for verification."""

    def __init__(self, projects_root: str, llm_service: ILLMService) -> None:
        self.project_service = ProjectService(projects_root=projects_root)
        self.local_importer = LocalImporter()
        self.youtube_importer = YoutubeImporter()
        self.llm_service = llm_service

    async def run_pipeline(
        self,
        project_id: str,
        project_name: str,
        media_source: str,
        is_youtube: bool = False,
        whisper_model: str = "tiny",
        target_lang: str = "es",
        voice_name: str = "en-US-GuyNeural"
    ) -> Dict[str, Any]:
        """Runs the entire pipeline sequentially and returns execution metadata paths.
        
        Returns:
            Dict[str, Any]: File path results and performance benchmarks.
        """
        # 1. Scaffold project folders
        project_data = self.project_service.create_project(project_id, project_name)
        project_dir = self.project_service.get_project_dir(project_id)
        
        video_dir = os.path.join(project_dir, "video")
        audio_dir = os.path.join(project_dir, "audio")
        sub_dir = os.path.join(project_dir, "subtitle")
        trans_dir = os.path.join(project_dir, "translation")
        render_dir = os.path.join(project_dir, "render")
        cache_dir = os.path.join(project_dir, "cache")
        
        # 2. Import raw video source
        importer = self.youtube_importer if is_youtube else self.local_importer
        video_path = await importer.import_media(media_source, video_dir)
        
        # 3. Query container metadata
        metadata = MetadataExtractor.extract_metadata(video_path)
        
        # 4. Demux mono WAV audio track
        audio_path = os.path.join(audio_dir, "audio.wav")
        AudioExtractor.extract_audio(video_path, audio_path)
        
        # 5. Speech transcription
        speech_provider = FasterWhisperProvider()
        speech_model_manager = SpeechModelManager(models_root=os.path.join(cache_dir, "whisper"))
        speech_service = SpeechService(speech_provider, speech_model_manager)
        transcript, speech_bench = await speech_service.transcribe_audio(
            audio_path=audio_path,
            model_size=whisper_model,
            output_dir=sub_dir
        )
        
        # 6. Segment translation
        trans_provider = ChatAnywhereTranslationProvider(self.llm_service)
        trans_cache = TranslationCache(cache_file_path=os.path.join(cache_dir, "translation_cache.json"))
        glossary = GlossaryManager()
        translation_service = TranslationService(trans_provider, trans_cache, glossary)
        
        state_file_path = os.path.join(cache_dir, "translation_state.json")
        translated_transcript = await translation_service.translate_transcript(
            transcript=transcript,
            target_lang=target_lang,
            state_file_path=state_file_path,
            output_dir=trans_dir
        )
        
        # 7. Timeline alignment
        alignment_service = TimelineAlignmentService()
        aligned_transcript = await alignment_service.align_transcript(
            transcript=translated_transcript,
            output_dir=sub_dir
        )
        
        # 8. Voice Synthesis
        tts_provider = EdgeTTSProvider()
        voice_cache = VoiceCache(cache_dir=os.path.join(cache_dir, "voice_cache"))
        voice_service = VoiceService(tts_provider, voice_cache, temp_dir=cache_dir)
        
        final_wav, final_mp3, tts_bench = await voice_service.synthesize_transcript(
            transcript=aligned_transcript,
            voice_name=voice_name,
            output_dir=render_dir
        )
        
        return {
            "project_dir": project_dir,
            "video_path": video_path,
            "audio_path": audio_path,
            "metadata": metadata,
            "transcript_path": os.path.join(sub_dir, "transcript.json"),
            "translated_path": os.path.join(trans_dir, "translated_transcript.json"),
            "aligned_path": os.path.join(sub_dir, "aligned_transcript.json"),
            "final_wav": final_wav,
            "final_mp3": final_mp3,
            "speech_benchmark": speech_bench,
            "tts_benchmark": tts_bench
        }
