import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock
import pytest
from backend.speech.models import Segment, Transcript, Word
from backend.providers.translation.chatanywhere.chatanywhere_provider import ChatAnywhereTranslationProvider
from backend.translation.glossary import GlossaryManager
from backend.translation.cache import TranslationCache
from backend.translation.chunk_manager import ChunkManager
from backend.translation.translation_service import TranslationService
from backend.services.llm_service import ILLMService

def test_glossary_manager() -> None:
    mgr = GlossaryManager()
    mgr.add_protected_word("AutoShort Studio")
    mgr.add_terminology("AI", "Trí tuệ nhân tạo")

    prompt = mgr.format_for_prompt()
    assert "AutoShort Studio" in prompt
    assert "AI" in prompt
    assert "Trí tuệ nhân tạo" in prompt


def test_translation_cache() -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        cache_file = os.path.join(tmp_root, "cache.json")
        cache = TranslationCache(cache_file_path=cache_file)
        
        assert cache.get("Hello", "es") is None
        
        cache.set("Hello", "es", "Hola")
        assert cache.get("Hello", "es") == "Hola"
        
        cache.clear()
        assert cache.get("Hello", "es") is None


def test_chunk_manager_splitting() -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        state_file = os.path.join(tmp_root, "state.json")
        mgr = ChunkManager(state_file_path=state_file, chunk_size=5, max_retries=2)
        
        segments = [{"id": i, "text": f"seg {i}"} for i in range(12)]
        chunks = mgr.split_segments(segments)
        
        assert len(chunks) == 3  # Chunks sizes: 5, 5, 2
        assert len(chunks[0]) == 5
        assert len(chunks[2]) == 2

        # Check completed states and checkpoints
        assert mgr.is_chunk_completed(0) is False
        mgr.save_chunk_translations(0, [{"id": 0, "text": "trans"}])
        assert mgr.is_chunk_completed(0) is True


@pytest.mark.asyncio
async def test_chatanywhere_translation_provider() -> None:
    # Setup Mock LLM Service
    mock_llm = MagicMock(spec=ILLMService)
    mock_llm.chat = AsyncMock(return_value=json.dumps([{"id": 0, "text": "Hola"}]))

    provider = ChatAnywhereTranslationProvider(mock_llm)
    res = await provider.translate_segments([{"id": 0, "text": "Hello"}], "es", "Mock glossary")
    
    assert len(res) == 1
    assert res[0]["text"] == "Hola"
    mock_llm.chat.assert_called_once()


@pytest.mark.asyncio
async def test_translation_service_resume_retry_merge_export() -> None:
    with tempfile.TemporaryDirectory() as tmp_root:
        state_file = os.path.join(tmp_root, "state.json")
        output_dir = os.path.join(tmp_root, "output")
        cache_file = os.path.join(tmp_root, "cache.json")

        # Mock Provider with retry simulation
        mock_provider = MagicMock()
        
        # First call fails, second call succeeds to check retry logic
        call_count = 0
        async def fake_translate(segments: list, target_lang: str, glossary: str) -> list:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Temporary connection timeout")
            return [{"id": seg["id"], "text": "Hola"} for seg in segments]
            
        mock_provider.translate_segments = fake_translate

        # Setup service dependencies
        cache = TranslationCache(cache_file_path=cache_file)
        glossary = GlossaryManager()
        service = TranslationService(mock_provider, cache, glossary)

        # Setup transcript structures
        words = [Word(word="Hello", start=0.0, end=1.0, probability=0.9)]
        seg = Segment(id=0, start=0.0, end=1.0, text="Hello", words=words, confidence=0.9)
        transcript = Transcript(text="Hello", language="en", language_probability=0.9, duration=1.0, segments=[seg])

        # Execute translation (will trigger retry on first chunk)
        res = await service.translate_transcript(
            transcript=transcript,
            target_lang="es",
            state_file_path=state_file,
            chunk_size=5,
            max_retries=3,
            output_dir=output_dir
        )

        assert res.text == "Hola"
        assert res.segments[0].text == "Hola"
        assert res.segments[0].start == 0.0  # Structure check
        assert res.segments[0].words[0].word == "Hello"  # Words layout preserved
        
        # Verify files exist in output directories
        assert os.path.exists(os.path.join(output_dir, "translated_transcript.json"))
        assert os.path.exists(os.path.join(output_dir, "translated_transcript.txt"))
        assert os.path.exists(os.path.join(output_dir, "translated_transcript.srt"))

        # Verify cache write checks
        assert cache.get("Hello", "es") == "Hola"

        # Verify task resume checkpoints checks
        call_count = 0
        res_cached = await service.translate_transcript(
            transcript=transcript,
            target_lang="es",
            state_file_path=state_file,
            chunk_size=5,
            max_retries=3
        )
        assert res_cached.text == "Hola"
        # No provider calls are executed because chunk checkpoints are set
        assert call_count == 0
