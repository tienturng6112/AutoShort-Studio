import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from backend.speech.models import Segment, Transcript
from backend.tts.audio_merger import AudioMerger
from backend.tts.audio_normalizer import AudioNormalizer
from backend.tts.edge_tts_provider import EdgeTTSProvider
from backend.tts.silence_generator import SilenceGenerator
from backend.tts.tts_provider import BaseTTSProvider
from backend.tts.voice_cache import VoiceCache
from backend.tts.voice_manager import VoiceManager
from backend.tts.voice_service import VoiceService

@pytest.mark.asyncio
@patch("backend.tts.edge_tts_provider.edge_tts")
async def test_edge_tts_provider_voices_and_generate(mock_edge: MagicMock) -> None:
    # Setup EdgeTTS mock managers
    mock_manager = AsyncMock()
    mock_edge.VoicesManager.create = AsyncMock(return_value=mock_manager)
    mock_manager.voices = [
        {"Name": "en-US-GuyNeural", "Gender": "Male", "Locale": "en-US"},
        {"Name": "vi-VN-HoaiMyNeural", "Gender": "Female", "Locale": "vi-VN"}
    ]

    provider = EdgeTTSProvider()
    voices = await provider.list_voices()
    assert len(voices) == 2
    assert voices[0]["name"] == "en-US-GuyNeural"
    assert voices[0]["gender"] == "Male"

    # Mock streaming chunk generator
    mock_comm = MagicMock()
    mock_edge.Communicate.return_value = mock_comm
    
    async def fake_stream():
        yield {"type": "audio", "data": b"wav bytes data"}
        # WordBoundary chunk offset and duration (in 100ns units -> 1.0s, 0.5s duration)
        yield {"type": "WordBoundary", "text": "Hello", "offset": 10000000, "duration": 5000000}
    
    mock_comm.stream = fake_stream

    with tempfile.TemporaryDirectory() as tmp_root:
        out_path = os.path.join(tmp_root, "output.wav")
        path, word_bounds = await provider.generate("Hello", "en-US-GuyNeural", out_path)
        
        assert path == out_path
        assert os.path.exists(out_path)
        assert len(word_bounds) == 1
        assert word_bounds[0]["word"] == "Hello"
        assert word_bounds[0]["start"] == pytest.approx(1.0)
        assert word_bounds[0]["end"] == pytest.approx(1.5)


@pytest.mark.asyncio
async def test_voice_manager() -> None:
    mock_prov_1 = MagicMock(spec=BaseTTSProvider)
    mock_prov_1.list_voices = AsyncMock(return_value=[{"name": "en-Guy", "gender": "Male", "language": "en-US"}])
    mock_prov_2 = MagicMock(spec=BaseTTSProvider)
    mock_prov_2.list_voices = AsyncMock(return_value=[{"name": "vi-HoaiMy", "gender": "Female", "language": "vi-VN"}])

    mgr = VoiceManager()
    mgr.register_provider("prov1", mock_prov_1)
    mgr.register_provider("prov2", mock_prov_2)

    res_en = await mgr.list_voices(language="en")
    assert len(res_en) == 1
    assert res_en[0]["name"] == "en-Guy"

    res_fem = await mgr.list_voices(gender="Female")
    assert len(res_fem) == 1
    assert res_fem[0]["name"] == "vi-HoaiMy"


def test_voice_cache() -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        cache = VoiceCache(cache_dir=tmp_root)
        
        assert cache.get("Hello", "en-Guy") is None
        
        src_file = os.path.join(tmp_root, "source.wav")
        with open(src_file, "w", encoding="utf-8") as f:
            f.write("source audio")
            
        cached_file = cache.set("Hello", "en-Guy", src_file)
        assert os.path.exists(cached_file)
        assert cache.get("Hello", "en-Guy") == cached_file
        
        cache.clear()
        assert cache.get("Hello", "en-Guy") is None


@patch("backend.tts.silence_generator.subprocess.run")
def test_silence_generator(mock_run: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        out = os.path.join(tmp_root, "silence.wav")
        
        def fake_run(cmd: list, **kwargs: dict) -> None:
            with open(out, "w", encoding="utf-8") as f:
                f.write("silence")
        mock_run.side_effect = fake_run
        
        res = SilenceGenerator.generate_silence(0.5, out)
        assert res == out
        assert os.path.exists(out)
        mock_run.assert_called_once()


@patch("backend.tts.audio_merger.subprocess.run")
def test_audio_merger(mock_run: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        out = os.path.join(tmp_root, "merged.wav")
        
        def fake_run(cmd: list, **kwargs: dict) -> None:
            with open(out, "w", encoding="utf-8") as f:
                f.write("merged")
        mock_run.side_effect = fake_run

        in1 = os.path.join(tmp_root, "in1.wav")
        with open(in1, "w", encoding="utf-8") as f:
            f.write("1")
            
        res = AudioMerger.merge_audio_files([in1], out)
        assert res == out
        assert os.path.exists(out)
        mock_run.assert_called_once()


@patch("backend.tts.audio_normalizer.subprocess.run")
def test_audio_normalizer(mock_run: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        out = os.path.join(tmp_root, "normalized.wav")
        
        def fake_run(cmd: list, **kwargs: dict) -> None:
            with open(out, "w", encoding="utf-8") as f:
                f.write("normalized")
        mock_run.side_effect = fake_run
        
        res = AudioNormalizer.normalize_audio("src.wav", out)
        assert res == out
        assert os.path.exists(out)
        mock_run.assert_called_once()


@pytest.mark.asyncio
@patch("backend.tts.silence_generator.subprocess.run")
@patch("backend.tts.audio_merger.subprocess.run")
@patch("backend.tts.audio_normalizer.subprocess.run")
@patch("backend.tts.voice_service.subprocess.run")
async def test_voice_service_pipeline(
    mock_silence: MagicMock,
    mock_merge: MagicMock,
    mock_norm: MagicMock,
    mock_voice_run: MagicMock
) -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        temp_dir = os.path.join(tmp_root, "temp")
        out_dir = os.path.join(tmp_root, "output")
        cache_dir = os.path.join(tmp_root, "cache")
        
        # Set fake run writes to resolve existence assertions
        def fake_silence(cmd: list, **kwargs: dict) -> None:
            out_file = cmd[-1]
            with open(out_file, "w", encoding="utf-8") as f:
                f.write("silence")
        mock_silence.side_effect = fake_silence

        def fake_merge(cmd: list, **kwargs: dict) -> None:
            out_file = cmd[-1]
            with open(out_file, "w", encoding="utf-8") as f:
                f.write("merged")
        mock_merge.side_effect = fake_merge

        def fake_norm(cmd: list, **kwargs: dict) -> None:
            out_file = cmd[-1]
            with open(out_file, "w", encoding="utf-8") as f:
                f.write("normalized")
        mock_norm.side_effect = fake_norm

        def fake_voice_run(cmd: list, **kwargs: dict) -> MagicMock:
            out_file = cmd[-1]
            # Write a dummy WAV file: 44-byte header + some PCM data
            with open(out_file, "wb") as f:
                f.write(b"RIFF" + b"\x00" * 36 + b"data" + b"\x00" * 100)
            res = MagicMock()
            res.returncode = 0
            return res
        mock_voice_run.side_effect = fake_voice_run

        # Mock active speech provider
        mock_provider = MagicMock(spec=BaseTTSProvider)
        async def fake_gen(text: str, voice: str, out_path: str) -> tuple:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("speech")
            return out_path, []
        mock_provider.generate = fake_gen
        mock_provider.validate_voice = AsyncMock()

        cache = VoiceCache(cache_dir=cache_dir)
        service = VoiceService(mock_provider, cache, temp_dir=temp_dir)

        # Setup transcript (Initial gap 0.2s, segment interval gap of 0.5s)
        seg1 = Segment(id=0, start=0.2, end=1.0, text="First segment", words=[], confidence=0.9)
        seg2 = Segment(id=1, start=1.5, end=2.0, text="Second segment", words=[], confidence=0.9)
        transcript = Transcript(text="", language="en", language_probability=0.9, duration=2.0, segments=[seg1, seg2])

        wav_path, mp3_path, benchmark = await service.synthesize_transcript(
            transcript=transcript,
            voice_name="en-US-GuyNeural",
            output_dir=out_dir
        )

        assert os.path.exists(wav_path)
        assert os.path.exists(mp3_path)
        assert benchmark.provider == "edge-tts"
        assert benchmark.voice == "en-US-GuyNeural"
        assert benchmark.synthesis_time_seconds > 0


@pytest.mark.asyncio
@patch("backend.tts.kira_provider.httpx.AsyncClient")
async def test_kira_provider_and_factory(mock_async_client: MagicMock) -> None:
    # Setup HTTP response mock
    mock_client = MagicMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client
    
    # 1. Mock list_voices response
    mock_list_resp = MagicMock()
    mock_list_resp.status_code = 200
    mock_list_resp.json.return_value = [
        {"id": "aoede", "name": "Aoede (Nova - Female)", "gender": "Female", "language": "vi"}
    ]
    
    # 2. Mock generate POST response (returns raw audio bytes)
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post_resp.content = b"kira mp3 bytes output"
    
    # Set side effects for request calls
    async def fake_get(url, *args, **kwargs):
        if "/voices" in url:
            return mock_list_resp
        return MagicMock(status_code=404)
        
    async def fake_post(url, *args, **kwargs):
        if "/speech" in url:
            return mock_post_resp
        return MagicMock(status_code=404)
        
    mock_client.get = fake_get
    mock_client.post = fake_post
    
    # Instantiate via TTSProviderFactory
    settings = {
        "tts_provider": "Kira",
        "kira": {
            "api_key": "test-key-123",
            "model": "kira-3.0-flash-tts",
            "speed": "1.1"
        }
    }
    from backend.tts.tts_provider import TTSProviderFactory
    provider = TTSProviderFactory.create("Kira", settings)
    
    assert provider._api_key == "test-key-123"
    assert provider._model == "kira-3.0-flash-tts"
    assert provider._speed == 1.1
    
    # Test list_voices
    voices = await provider.list_voices()
    assert len(voices) == 1
    assert voices[0]["name"] == "aoede"
    assert voices[0]["display_name"] == "Aoede (Nova - Female)"
    
    # Test generate
    with tempfile.TemporaryDirectory() as tmp_root:
        out_path = os.path.join(tmp_root, "speech.mp3")
        path, word_bounds = await provider.generate("Xin chao", "aoede", out_path)
        assert path == out_path
        assert os.path.exists(out_path)
        import wave
        with wave.open(out_path, "rb") as w:
            assert w.getnchannels() == 1
            assert w.getsampwidth() == 2
            assert w.getframerate() == 24000
            assert w.readframes(w.getnframes()) == b"kira mp3 bytes outpu"
            
    # Test preview
    preview_bytes = await provider.preview("Xin chao", "aoede")
    import io
    with wave.open(io.BytesIO(preview_bytes), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == 24000
        assert w.readframes(w.getnframes()) == b"kira mp3 bytes outpu"


@pytest.mark.asyncio
async def test_edge_tts_provider_voice_validation() -> None:
    provider = EdgeTTSProvider()
    # Should pass
    await provider.validate_voice("vi-VN-HoaiMyNeural", "vi")
    await provider.validate_voice("vi-VN-NamMinhNeural", "vi-VN")
    # Should bypass if not Vietnamese
    await provider.validate_voice("invalid-voice", "en")
    
    # Should fail if Vietnamese and not in list
    with pytest.raises(ValueError, match="Selected voice error: Expected vi-VN-HoaiMyNeural"):
        await provider.validate_voice("invalid-voice", "vi")


@pytest.mark.asyncio
@patch("backend.tts.kira_provider.httpx.AsyncClient")
async def test_kira_provider_voice_validation(mock_async_client: MagicMock) -> None:
    # Setup HTTP response mock for list_voices
    mock_client = MagicMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client
    
    mock_list_resp = MagicMock()
    mock_list_resp.status_code = 200
    mock_list_resp.json.return_value = [
        {"id": "alloy", "name": "Alloy", "gender": "Female", "language": "vi"}
    ]
    mock_client.get = AsyncMock(return_value=mock_list_resp)
    
    from backend.tts.kira_provider import KiraProvider
    provider = KiraProvider(api_key="test-key")
    # Should pass because it is in list_voices
    await provider.validate_voice("alloy", "vi")
    
    # Should fail if not in list_voices
    with pytest.raises(ValueError, match="Voice 'invalid-voice' is not supported"):
        await provider.validate_voice("invalid-voice", "vi")


@pytest.mark.asyncio
@patch("backend.tts.silence_generator.subprocess.run")
@patch("backend.tts.audio_merger.subprocess.run")
@patch("backend.tts.audio_normalizer.subprocess.run")
@patch("backend.tts.voice_service.subprocess.run")
async def test_voice_service_speaker_id_validation(
    mock_silence: MagicMock,
    mock_merge: MagicMock,
    mock_norm: MagicMock,
    mock_voice_run: MagicMock
) -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        temp_dir = os.path.join(tmp_root, "temp")
        out_dir = os.path.join(tmp_root, "output")
        cache_dir = os.path.join(tmp_root, "cache")
        
        # Set fake run writes to resolve existence assertions
        def fake_write(cmd: list, **kwargs: dict) -> None:
            out_file = cmd[-1]
            with open(out_file, "w", encoding="utf-8") as f:
                f.write("dummy")
        mock_silence.side_effect = fake_write
        mock_merge.side_effect = fake_write
        mock_norm.side_effect = fake_write
        
        def fake_voice_run(cmd: list, **kwargs: dict) -> MagicMock:
            out_file = cmd[-1]
            with open(out_file, "wb") as f:
                f.write(b"RIFF" + b"\x00" * 36 + b"data" + b"\x00" * 100)
            res = MagicMock()
            res.returncode = 0
            return res
        mock_voice_run.side_effect = fake_voice_run
        
        mock_provider = MagicMock(spec=BaseTTSProvider)
        async def fake_gen(text: str, voice: str, out_path: str) -> tuple:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("speech")
            return out_path, []
        mock_provider.generate = fake_gen
        mock_provider.validate_voice = AsyncMock()
        
        cache = VoiceCache(cache_dir=cache_dir)
        service = VoiceService(mock_provider, cache, temp_dir=temp_dir)
        
        # 1. Segment speaker_id is missing (None) when speaker_voices is configured -> should fail
        seg_no_spk = Segment(id=0, start=0.0, end=1.0, text="No speaker ID segment", words=[], confidence=0.9, speaker_id=None)
        tx_no_spk = Transcript(text="", language="en", language_probability=0.9, duration=1.0, segments=[seg_no_spk])
        
        with pytest.raises(ValueError, match="is missing a speaker_id assignment"):
            await service.synthesize_transcript(
                transcript=tx_no_spk,
                voice_name="en-US-GuyNeural",
                output_dir=out_dir,
                speaker_voices={"Speaker_A": "alloy"}
            )
            
        # 2. Segment speaker_id is unmapped in speaker_voices configuration -> should fail
        seg_bad_spk = Segment(id=0, start=0.0, end=1.0, text="Bad speaker ID segment", words=[], confidence=0.9, speaker_id="Speaker_B")
        tx_bad_spk = Transcript(text="", language="en", language_probability=0.9, duration=1.0, segments=[seg_bad_spk])
        
        with pytest.raises(KeyError, match="is not configured in speaker_voices mapping"):
            await service.synthesize_transcript(
                transcript=tx_bad_spk,
                voice_name="en-US-GuyNeural",
                output_dir=out_dir,
                speaker_voices={"Speaker_A": "alloy"}
            )
            
        # 3. Segment speaker_id is correct and mapped -> should pass
        seg_ok = Segment(id=0, start=0.0, end=1.0, text="OK segment", words=[], confidence=0.9, speaker_id="Speaker_A")
        tx_ok = Transcript(text="", language="en", language_probability=0.9, duration=1.0, segments=[seg_ok])
        
        wav_path, mp3_path, benchmark = await service.synthesize_transcript(
            transcript=tx_ok,
            voice_name="en-US-GuyNeural",
            output_dir=out_dir,
            speaker_voices={"Speaker_A": "alloy"}
        )
        assert os.path.exists(wav_path)
        assert os.path.exists(mp3_path)
