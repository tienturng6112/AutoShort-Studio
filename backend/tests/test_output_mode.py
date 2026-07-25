import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import shutil
from backend.speech.models import Transcript, Segment
from backend.speech.speech_service import SpeechBenchmark

class MockTTSBenchmark:
    def __init__(self):
        self.provider = "edge-tts"
        self.voice = "alloy"
        self.synthesis_time_seconds = 1.5
        self.realtime_factor = 0.5

@pytest.mark.asyncio
@patch("backend.run_pipeline.argparse.ArgumentParser.parse_args")
@patch("backend.run_pipeline.LocalImporter")
@patch("backend.run_pipeline.MetadataExtractor")
@patch("backend.run_pipeline.AudioExtractor")
@patch("backend.run_pipeline.SpeechService")
@patch("backend.run_pipeline.TimelineAlignmentService")
@patch("backend.run_pipeline.VoiceService")
@patch("subprocess.run")
@patch("shutil.copy2")
@patch("os.path.exists")
@patch("wave.open")
async def test_output_mode_subtitle_only(
    mock_wave_open,
    mock_exists,
    mock_copy2,
    mock_subprocess_run,
    mock_voice_service,
    mock_alignment_service,
    mock_speech_service,
    mock_audio_extractor,
    mock_metadata_extractor,
    mock_local_importer,
    mock_parse_args
) -> None:
    # Setup CLI arguments
    mock_args = MagicMock()
    mock_args.input = "input.mp4"
    mock_args.source_language = "en"
    mock_args.target_language = "es"
    mock_args.enhance_speech = False
    mock_args.output_mode = "Subtitle Only"
    mock_parse_args.return_value = mock_args

    # Mock settings.json loading
    mock_exists.return_value = True

    # Setup core service returns
    mock_local_importer.return_value.import_media = AsyncMock(return_value="video.mp4")
    mock_metadata_extractor.extract_metadata = MagicMock(return_value={"duration": 10.0, "fps": 30.0})
    mock_audio_extractor.extract_audio = MagicMock()
    
    mock_subprocess_result = MagicMock()
    mock_subprocess_result.returncode = 0
    mock_subprocess_result.stdout = b""
    mock_subprocess_result.stderr = b""
    mock_subprocess_run.return_value = mock_subprocess_result
    
    dummy_transcript = Transcript(text="hello", language="en", language_probability=1.0, duration=10.0, segments=[])
    dummy_bench = SpeechBenchmark(
        model="small",
        device="cpu",
        execution_time_seconds=1.2,
        realtime_factor=0.12,
        memory_usage_mb=100.0
    )
    
    mock_speech_service.return_value.transcribe_audio = AsyncMock(return_value=(dummy_transcript, dummy_bench))
    mock_alignment_service.return_value.align_transcript = AsyncMock(return_value=dummy_transcript)

    # Mock faster_whisper in sys.modules to simulate presence
    with patch.dict("sys.modules", {"faster_whisper": MagicMock()}):
        # Run main pipeline
        from backend.run_pipeline import main
        with patch("backend.run_pipeline.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "{}"
            await main()

    # 1. Voice Synthesis (Stage 6) must NOT be instantiated or called
    mock_voice_service.assert_not_called()

    # 2. FFmpeg Video composition (Stage 8 subprocess.run) MUST be called (burn subtitles)
    mock_subprocess_run.assert_called_once()


@pytest.mark.asyncio
@patch("backend.run_pipeline.argparse.ArgumentParser.parse_args")
@patch("backend.run_pipeline.LocalImporter")
@patch("backend.run_pipeline.MetadataExtractor")
@patch("backend.run_pipeline.AudioExtractor")
@patch("backend.run_pipeline.SpeechService")
@patch("backend.run_pipeline.TimelineAlignmentService")
@patch("backend.run_pipeline.VoiceService")
@patch("subprocess.run")
@patch("shutil.copy2")
@patch("os.path.exists")
@patch("wave.open")
async def test_output_mode_voice_only(
    mock_wave_open,
    mock_exists,
    mock_copy2,
    mock_subprocess_run,
    mock_voice_service,
    mock_alignment_service,
    mock_speech_service,
    mock_audio_extractor,
    mock_metadata_extractor,
    mock_local_importer,
    mock_parse_args
) -> None:
    # Setup CLI arguments
    mock_args = MagicMock()
    mock_args.input = "input.mp4"
    mock_args.source_language = "en"
    mock_args.target_language = "es"
    mock_args.enhance_speech = False
    mock_args.output_mode = "Voice Only"
    mock_parse_args.return_value = mock_args

    # Mock settings.json loading
    mock_exists.return_value = True

    # Setup core service returns
    mock_local_importer.return_value.import_media = AsyncMock(return_value="video.mp4")
    mock_metadata_extractor.extract_metadata = MagicMock(return_value={"duration": 10.0, "fps": 30.0})
    mock_audio_extractor.extract_audio = MagicMock()
    
    dummy_transcript = Transcript(text="hello", language="en", language_probability=1.0, duration=10.0, segments=[])
    dummy_bench = SpeechBenchmark(
        model="small",
        device="cpu",
        execution_time_seconds=1.2,
        realtime_factor=0.12,
        memory_usage_mb=100.0
    )
    
    mock_speech_service.return_value.transcribe_audio = AsyncMock(return_value=(dummy_transcript, dummy_bench))
    mock_alignment_service.return_value.align_transcript = AsyncMock(return_value=dummy_transcript)

    # Setup Voice service synthesis output
    mock_vs = MagicMock()
    mock_vs.synthesize_transcript = AsyncMock(return_value=("final.wav", "final.mp3", MockTTSBenchmark()))
    mock_voice_service.return_value = mock_vs

    # Mock wave reading for validation
    mock_wave_file = MagicMock()
    mock_wave_file.getnframes.return_value = 240000
    mock_wave_file.getframerate.return_value = 24000
    mock_wave_open.return_value.__enter__.return_value = mock_wave_file

    # Mock faster_whisper in sys.modules to simulate presence
    with patch.dict("sys.modules", {"faster_whisper": MagicMock()}):
        # Run main pipeline
        from backend.run_pipeline import main
        with patch("backend.run_pipeline.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "{}"
            await main()

    # 1. Voice Synthesis (Stage 6) MUST be called
    mock_vs.synthesize_transcript.assert_called_once()

    # 2. FFmpeg Video composition (Stage 8 subprocess.run) must NOT be called
    mock_subprocess_run.assert_not_called()

@pytest.mark.asyncio
@patch("backend.run_pipeline.argparse.ArgumentParser.parse_args")
@patch("backend.run_pipeline.LocalImporter")
@patch("backend.run_pipeline.MetadataExtractor")
@patch("backend.run_pipeline.AudioExtractor")
@patch("backend.run_pipeline.SpeechService")
@patch("backend.run_pipeline.TimelineAlignmentService")
@patch("backend.run_pipeline.VoiceService")
@patch("subprocess.run")
@patch("shutil.copy2")
@patch("os.path.exists")
@patch("wave.open")
async def test_output_mode_subtitle_audio_files(
    mock_wave_open,
    mock_exists,
    mock_copy2,
    mock_subprocess_run,
    mock_voice_service,
    mock_alignment_service,
    mock_speech_service,
    mock_audio_extractor,
    mock_metadata_extractor,
    mock_local_importer,
    mock_parse_args
) -> None:
    mock_args = MagicMock()
    mock_args.input = "input.mp4"
    mock_args.source_language = "en"
    mock_args.target_language = "es"
    mock_args.enhance_speech = False
    mock_args.output_mode = "Subtitle + Audio Files"
    mock_parse_args.return_value = mock_args

    mock_exists.return_value = True

    mock_local_importer.return_value.import_media = AsyncMock(return_value="video.mp4")
    mock_metadata_extractor.extract_metadata = MagicMock(return_value={"duration": 10.0, "fps": 30.0})
    mock_audio_extractor.extract_audio = MagicMock()
    
    dummy_transcript = Transcript(text="hello", language="en", language_probability=1.0, duration=10.0, segments=[])
    dummy_bench = SpeechBenchmark(
        model="small",
        device="cpu",
        execution_time_seconds=1.2,
        realtime_factor=0.12,
        memory_usage_mb=100.0
    )
    
    mock_speech_service.return_value.transcribe_audio = AsyncMock(return_value=(dummy_transcript, dummy_bench))
    mock_alignment_service.return_value.align_transcript = AsyncMock(return_value=dummy_transcript)

    mock_vs = MagicMock()
    mock_vs.synthesize_transcript = AsyncMock(return_value=("final.wav", "final.mp3", MockTTSBenchmark()))
    mock_voice_service.return_value = mock_vs

    mock_wave_file = MagicMock()
    mock_wave_file.getnframes.return_value = 240000
    mock_wave_file.getframerate.return_value = 24000
    mock_wave_open.return_value.__enter__.return_value = mock_wave_file

    with patch.dict("sys.modules", {"faster_whisper": MagicMock()}):
        from backend.run_pipeline import main
        with patch("backend.run_pipeline.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "{}"
            await main()

    # Assertions
    # 1. Voice Synthesis (Stage 6) MUST be called
    mock_vs.synthesize_transcript.assert_called_once()
    # 2. FFmpeg Video composition MUST NOT be called
    mock_subprocess_run.assert_not_called()

@pytest.mark.asyncio
@patch("backend.run_pipeline.argparse.ArgumentParser.parse_args")
@patch("backend.run_pipeline.LocalImporter")
@patch("backend.run_pipeline.MetadataExtractor")
@patch("backend.run_pipeline.AudioExtractor")
@patch("backend.run_pipeline.SpeechService")
@patch("backend.run_pipeline.TimelineAlignmentService")
@patch("backend.run_pipeline.VoiceService")
@patch("subprocess.run")
@patch("shutil.copy2")
@patch("os.path.exists")
@patch("wave.open")
async def test_output_mode_subtitle_voice(
    mock_wave_open,
    mock_exists,
    mock_copy2,
    mock_subprocess_run,
    mock_voice_service,
    mock_alignment_service,
    mock_speech_service,
    mock_audio_extractor,
    mock_metadata_extractor,
    mock_local_importer,
    mock_parse_args
) -> None:
    mock_args = MagicMock()
    mock_args.input = "input.mp4"
    mock_args.source_language = "en"
    mock_args.target_language = "es"
    mock_args.enhance_speech = False
    mock_args.output_mode = "Subtitle + Voice"
    mock_parse_args.return_value = mock_args

    mock_exists.return_value = True

    mock_local_importer.return_value.import_media = AsyncMock(return_value="video.mp4")
    mock_metadata_extractor.extract_metadata = MagicMock(return_value={"duration": 10.0, "fps": 30.0})
    mock_audio_extractor.extract_audio = MagicMock()
    
    mock_subprocess_result = MagicMock()
    mock_subprocess_result.returncode = 0
    mock_subprocess_result.stdout = b""
    mock_subprocess_result.stderr = b""
    mock_subprocess_run.return_value = mock_subprocess_result
    
    dummy_transcript = Transcript(text="hello", language="en", language_probability=1.0, duration=10.0, segments=[])
    dummy_bench = SpeechBenchmark(
        model="small",
        device="cpu",
        execution_time_seconds=1.2,
        realtime_factor=0.12,
        memory_usage_mb=100.0
    )
    
    mock_speech_service.return_value.transcribe_audio = AsyncMock(return_value=(dummy_transcript, dummy_bench))
    mock_alignment_service.return_value.align_transcript = AsyncMock(return_value=dummy_transcript)

    mock_vs = MagicMock()
    mock_vs.synthesize_transcript = AsyncMock(return_value=("final.wav", "final.mp3", MockTTSBenchmark()))
    mock_voice_service.return_value = mock_vs

    mock_wave_file = MagicMock()
    mock_wave_file.getnframes.return_value = 240000
    mock_wave_file.getframerate.return_value = 24000
    mock_wave_open.return_value.__enter__.return_value = mock_wave_file

    with patch.dict("sys.modules", {"faster_whisper": MagicMock()}):
        from backend.run_pipeline import main
        with patch("backend.run_pipeline.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "{}"
            await main()

    # Assertions
    # 1. Voice Synthesis (Stage 6) MUST be called
    mock_vs.synthesize_transcript.assert_called_once()
    # 2. FFmpeg Video composition MUST be called
    mock_subprocess_run.assert_called_once()

