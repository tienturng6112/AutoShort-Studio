import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from backend.providers.translation.deepl.deepl_provider import DeepLTranslationProvider

@pytest.mark.asyncio
async def test_endpoint_targeting_free():
    # Ends with :fx -> Free API URL
    provider = DeepLTranslationProvider(api_key="mock-key-123:fx")
    assert provider.base_url == "https://api-free.deepl.com/v2/translate"

@pytest.mark.asyncio
async def test_endpoint_targeting_pro():
    # Does not end with :fx -> Pro API URL
    provider = DeepLTranslationProvider(api_key="mock-key-123")
    assert provider.base_url == "https://api.deepl.com/v2/translate"

@pytest.mark.asyncio
async def test_batch_translation_success():
    provider = DeepLTranslationProvider(api_key="mock-key-123:fx", batch_size=2)
    segments = [
        {"id": 0, "text": "Hello"},
        {"id": 1, "text": "World"},
        {"id": 2, "text": "Test"}
    ]
    
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(side_effect=[
        {"translations": [{"text": "Hola"}, {"text": "Mundo"}]},
        {"translations": [{"text": "Prueba"}]}
    ])
    
    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        results = await provider.translate_segments(segments, target_lang="es")
        
        assert len(results) == 3
        assert results[0] == {"id": 0, "text": "Hola"}
        assert results[1] == {"id": 1, "text": "Mundo"}
        assert results[2] == {"id": 2, "text": "Prueba"}
        assert mock_post.call_count == 2

@pytest.mark.asyncio
async def test_retry_on_429_success():
    provider = DeepLTranslationProvider(api_key="mock-key-123:fx", batch_size=5)
    segments = [{"id": 0, "text": "Hello"}]
    
    mock_response_rate_limit = AsyncMock()
    mock_response_rate_limit.status_code = 429
    
    mock_response_success = AsyncMock()
    mock_response_success.status_code = 200
    mock_response_success.json = MagicMock(return_value={"translations": [{"text": "Hola"}]})
    
    with patch("httpx.AsyncClient.post") as mock_post, patch("asyncio.sleep", return_value=None) as mock_sleep:
        mock_post.side_effect = [mock_response_rate_limit, mock_response_success]
        
        results = await provider.translate_segments(segments, target_lang="es")
        
        assert results == [{"id": 0, "text": "Hola"}]
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once_with(1.0)

@pytest.mark.asyncio
async def test_retry_exhausted_fallback():
    provider = DeepLTranslationProvider(api_key="mock-key-123:fx", batch_size=5)
    segments = [{"id": 0, "text": "Hello"}]
    
    mock_response_err = AsyncMock()
    mock_response_err.status_code = 500
    mock_response_err.text = "Internal Server Error"
    
    with patch("httpx.AsyncClient.post", return_value=mock_response_err) as mock_post, patch("asyncio.sleep", return_value=None):
        results = await provider.translate_segments(segments, target_lang="es")
        
        # Should fallback to original text without crashing
        assert results == [{"id": 0, "text": "Hello"}]
        assert mock_post.call_count == 5
