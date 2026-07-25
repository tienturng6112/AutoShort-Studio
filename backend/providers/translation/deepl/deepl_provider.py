import logging
import asyncio
import time
import httpx
from typing import Any, Dict, List, Optional
from backend.providers.translation.base_translation_provider import BaseTranslationProvider

logger = logging.getLogger("DeepLTranslationProvider")

class DeepLTranslationProvider(BaseTranslationProvider):
    """Translation adapter leveraging Meta/DeepL REST API with batching, retries, and telemetry."""

    def __init__(
        self, 
        api_key: str, 
        batch_size: int = 10, 
        glossary_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> None:
        """Initializes the DeepL provider with necessary keys and settings.
        
        Args:
            api_key (str): DeepL API authentication key.
            batch_size (int): Number of text segments to batch per API request.
            glossary_id (Optional[str]): Pre-created DeepL glossary ID.
            context (Optional[str]): Context parameter to guide DeepL translations.
        """
        self.api_key = api_key.strip()
        self.batch_size = max(1, batch_size)
        self.glossary_id = glossary_id
        self.context = context
        
        # Free API keys end with :fx; Pro keys do not.
        is_free = self.api_key.endswith(":fx")
        self.base_url = "https://api-free.deepl.com/v2/translate" if is_free else "https://api.deepl.com/v2/translate"
        logger.info(f"Initialized DeepLTranslationProvider targeting: {self.base_url}")

    async def test_connection(self) -> Dict[str, Any]:
        """Tests the DeepL API connection using the /v2/usage endpoint."""
        import time
        start = time.perf_counter()
        
        if not self.api_key:
            return {
                "success": False,
                "message": "API Key is required",
                "status_code": None,
                "models": None,
                "latency_ms": 0
            }
            
        is_free = self.api_key.endswith(":fx")
        usage_url = "https://api-free.deepl.com/v2/usage" if is_free else "https://api.deepl.com/v2/usage"
        
        headers = {
            "Authorization": f"DeepL-Auth-Key {self.api_key}"
        }
        
        print(f"[DeepL Test] Key length: {len(self.api_key)}")
        print(f"[DeepL Test] Base URL type: {'Free' if is_free else 'Pro'}")
        print(f"[DeepL Test] Request URL: {usage_url}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(usage_url, headers=headers)
                print(f"[DeepL Test] HTTP status: {response.status_code}")
                latency = int((time.perf_counter() - start) * 1000)
                
                if response.status_code != 200:
                    print(f"[DeepL Test] Response body: {response.text}")
                    
                    if response.status_code == 403:
                        msg = "Authorization failed: Invalid API key or wrong endpoint (Free vs Pro)."
                    elif response.status_code == 404:
                        msg = "Endpoint not found. Check if the correct API URL is being used."
                    else:
                        msg = f"DeepL API error ({response.status_code}): {response.text}"
                        
                    return {
                        "success": False,
                        "message": msg,
                        "status_code": response.status_code,
                        "models": None,
                        "latency_ms": latency
                    }
                        
                return {
                    "success": True,
                    "message": "Connected",
                    "status_code": 200,
                    "models": ["default"],
                    "latency_ms": latency
                }
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return {
                "success": False,
                "message": f"Network Error: {str(e)}",
                "status_code": None,
                "models": None,
                "latency_ms": latency
            }

    async def list_models(self) -> List[str]:
        # DeepL does not expose selectable textual models for standard translation
        return ["default"]

    async def translate_segments(
        self, 
        segments: List[Dict[str, Any]], 
        target_lang: str, 
        glossary: Optional[Dict[str, str]] = None,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Translates segments using DeepL API in configurable batch sizes.
        
        Args:
            segments (List[Dict[str, Any]]): List of input segments to translate, e.g. [{"id": 0, "text": "..."}]
            target_lang (str): Destination language code, e.g. 'vi'.
            glossary (Optional[Dict[str, str]]): Glossary instructions (not used directly in DeepL API).
            context (Optional[str]): Context parameter to guide DeepL translations.
            
        Returns:
            List[Dict[str, Any]]: List of translated segments.
        """
        if not self.api_key:
            raise ValueError("DeepL API Key is missing or empty.")

        # Normalize target language code (DeepL uses uppercase, e.g. 'VI', 'EN-US')
        target = target_lang.upper()
        if target == "EN":
            target = "EN-US"
        elif target == "PT":
            target = "PT-PT"

        results = []
        
        # Process in batches of self.batch_size
        for i in range(0, len(segments), self.batch_size):
            batch = segments[i:i + self.batch_size]
            batch_texts = [item["text"] for item in batch]
            
            # Skip requests with all empty/whitespace strings
            if all(not text.strip() for text in batch_texts):
                for item in batch:
                    results.append({"id": item["id"], "text": item["text"]})
                continue

            translated_texts = []
            retries = 5
            delay = 1.0
            total_latency = 0.0
            attempt_count = 0
            
            payload = {
                "text": batch_texts,
                "target_lang": target
            }
            # Append context parameter if provided
            active_context = context or self.context
            if active_context:
                payload["context"] = active_context
            # Append glossary_id if configured
            if self.glossary_id:
                payload["glossary_id"] = self.glossary_id

            success = False
            for attempt in range(retries):
                attempt_count += 1
                start_time = time.perf_counter()
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            self.base_url,
                            headers={
                                "Authorization": f"DeepL-Auth-Key {self.api_key}",
                                "Content-Type": "application/json"
                            },
                            json=payload,
                            timeout=15.0
                        )
                    latency = time.perf_counter() - start_time
                    total_latency += latency
                    
                    if response.status_code == 200:
                        data = response.json()
                        translated_texts = [t["text"] for t in data["translations"]]
                        success = True
                        
                        # Log success metrics: provider, latency, characters, retry count, cache hit/miss
                        total_chars = sum(len(text) for text in batch_texts)
                        logger.info(
                            f"[DeepLTelemetry] provider=DeepL latency={latency:.3f}s characters={total_chars} "
                            f"retry_count={attempt} cache_hit_miss=miss"
                        )
                        break
                    elif response.status_code in [429, 500, 503]:
                        logger.warning(
                            f"DeepL batch request got status {response.status_code}. "
                            f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{retries})..."
                        )
                        await asyncio.sleep(delay)
                        delay *= 2.0
                    else:
                        # Non-retryable error code
                        response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    latency = time.perf_counter() - start_time
                    total_latency += latency
                    # Do not retry on non-retryable status codes
                    status_code = e.response.status_code
                    if status_code not in [429, 500, 503]:
                        logger.error(f"DeepL batch request failed with non-retryable status code {status_code}: {str(e)}")
                        raise RuntimeError(f"DeepL API error ({status_code}): {e.response.text}")
                    
                    if attempt == retries - 1:
                        logger.error(f"DeepL batch request failed: {str(e)}")
                        raise RuntimeError(f"DeepL request failed after retries: {str(e)}")
                    await asyncio.sleep(delay)
                    delay *= 2.0
                except Exception as e:
                    latency = time.perf_counter() - start_time
                    total_latency += latency
                    if attempt == retries - 1:
                        logger.error(f"DeepL batch request failed: {str(e)}")
                        raise RuntimeError(f"DeepL request failed: {str(e)}")
                    else:
                        await asyncio.sleep(delay)
                        delay *= 2.0

            # Map the batch results
            for idx, item in enumerate(batch):
                trans_text = translated_texts[idx] if idx < len(translated_texts) else item["text"]
                results.append({"id": item["id"], "text": trans_text})

        return results
