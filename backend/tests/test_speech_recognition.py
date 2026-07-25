import json
import os
import tempfile
from unittest.mock import MagicMock, patch
import pytest
from backend.speech.cancellation import CancellationToken
from backend.speech.faster_whisper_provider import FasterWhisperProvider
from backend.speech.model_manager import SpeechModelManager
from backend.speech.models import Transcript, Segment, Word
from backend.speech.speech_service import SpeechService

def test_transcript_exporters() -> None:
    # Setup mock transcript data
    words = [
        Word(word="Hello", start=0.0, end=0.5, probability=0.9),
        Word(word="world!", start=0.5, end=1.0, probability=0.95)
    ]
    seg1 = Segment(id=0, start=0.0, end=1.0, text="Hello world!", words=words, confidence=-0.1)
    transcript = Transcript(
        text="Hello world!",
        language="en",
        language_probability=0.99,
        duration=1.0,
        segments=[seg1]
    )

    # 1. JSON Export verification
    data = json.loads(transcript.to_json())
    assert data["text"] == "Hello world!"
    assert data["language"] == "en"

    # 2. TXT Export verification
    assert transcript.to_txt() == "Hello world!"

    # 3. SRT Export verification
    srt = transcript.to_srt()
    assert "1" in srt
    assert "00:00:00,000 --> 00:00:01,000" in srt
    assert "Hello world!" in srt


@patch("backend.speech.model_manager.download_model")
def test_speech_model_manager(mock_download: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        manager = SpeechModelManager(models_root=tmp_root)
        
        # Initial nonexistent check
        assert manager.is_model_downloaded("tiny") is False
        
        # Mock download behavior to generate weights payload file inside dir
        def fake_download(size: str, output_dir: str) -> None:
            with open(os.path.join(output_dir, "weights.bin"), "w", encoding="utf-8") as f:
                f.write("mock weights data")
        mock_download.side_effect = fake_download

        path = manager.get_model_path("tiny")
        assert "tiny" in path
        assert manager.is_model_downloaded("tiny") is True
        mock_download.assert_called_once_with("tiny", output_dir=path)

        # Unsupported model validation
        with pytest.raises(ValueError):
            manager.get_model_path("unsupported-size-name")


@pytest.mark.asyncio
@patch("backend.speech.faster_whisper_provider.WhisperModel")
async def test_faster_whisper_provider_transcribe(mock_whisper_class: MagicMock) -> None:
    mock_model = MagicMock()
    mock_whisper_class.return_value = mock_model

    # Setup segment timing structures mock
    mock_word = MagicMock()
    mock_word.word = "Hello"
    mock_word.start = 0.0
    mock_word.end = 0.5
    mock_word.probability = 0.9

    mock_seg = MagicMock()
    mock_seg.start = 0.0
    mock_seg.end = 1.0
    mock_seg.text = "Hello"
    mock_seg.avg_logprob = -0.15
    mock_seg.words = [mock_word]

    mock_info = MagicMock()
    mock_info.duration = 2.0
    mock_info.language = "en"
    mock_info.language_probability = 0.99

    # Set mock transcribe return to yield the segment list and details
    mock_model.transcribe.return_value = ([mock_seg], mock_info)

    provider = FasterWhisperProvider()
    progress_updates = []
    
    def progress_cb(val: float) -> None:
        progress_updates.append(val)

    transcript = await provider.transcribe(
        audio_path="fake_audio.wav",
        model_path="fake_model_dir",
        device="cpu",
        progress_callback=progress_cb
    )

    assert transcript.text == "Hello"
    assert transcript.language == "en"
    assert len(progress_updates) == 2  # seg progress (50.0%) + final trigger (100.0%)
    assert progress_updates[0] == pytest.approx(50.0)
    assert progress_updates[1] == pytest.approx(100.0)


@pytest.mark.asyncio
@patch("backend.speech.faster_whisper_provider.WhisperModel")
async def test_transcription_cancellation(mock_whisper_class: MagicMock) -> None:
    mock_model = MagicMock()
    mock_whisper_class.return_value = mock_model

    mock_seg = MagicMock()
    mock_seg.start = 0.0
    mock_seg.end = 1.0
    mock_seg.text = "Hello"
    mock_seg.avg_logprob = -0.1
    mock_seg.words = []

    mock_info = MagicMock()
    mock_info.duration = 2.0
    mock_info.language = "en"
    mock_info.language_probability = 0.95

    # Return multiple segments to check mid-run cancellation loops
    mock_model.transcribe.return_value = ([mock_seg, mock_seg], mock_info)

    provider = FasterWhisperProvider()
    token = CancellationToken()
    
    # Cancel token in advance
    token.cancel()
    
    with pytest.raises(RuntimeError) as exc:
        await provider.transcribe(
            audio_path="fake.wav",
            model_path="fake_dir",
            device="cpu",
            cancellation_token=token
        )
    assert "cancelled by the user" in str(exc.value)
