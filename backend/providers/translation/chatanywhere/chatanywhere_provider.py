import json
import time
from typing import Any, Dict, List, Optional
from openai import OpenAI
from backend.core.exceptions import AIProviderException
from backend.providers.translation.base_translation_provider import BaseTranslationProvider

class ChatAnywhereTranslationProvider(BaseTranslationProvider):
    """Concrete translation adapter leveraging OpenAI SDK directly."""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None) -> None:
        # Config Flow Audit Assertions
        if not api_key:
            raise ValueError("ChatAnywhereTranslationProvider config error: api_key is missing or empty at provider instantiation.")
        assert len(api_key) > 0, "ChatAnywhereTranslationProvider config error: api_key length must be > 0."
        
        self.api_key = api_key
        self.base_url = base_url or "https://api.chatanywhere.tech/v1"
        self._model = model or "gpt-4o-mini"
        self._quality_setting = "Balanced"
        self._client: Optional[OpenAI] = None
        
        # Log flow audit
        print(f"\n[CONFIG FLOW AUDIT - PROVIDER CONSTRUCTOR]")
        print(f"  api_key exists:               True")
        print(f"  api_key length:               {len(self.api_key)}")
        print(f"  base_url:                     {self.base_url}")
        print(f"  model:                        {self._model}")
        print(f"============================================\n")

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client

    def set_quality(self, quality: str):
        self._quality_setting = quality

    async def test_connection(self) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            client = self._get_client()
            models_list = client.models.list()
            models = [m.id for m in models_list.data]
            latency = int((time.perf_counter() - start) * 1000)
            return {
                "success": True,
                "message": "Connected",
                "status_code": 200,
                "models": models,
                "latency_ms": latency
            }
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return {
                "success": False,
                "message": str(e),
                "status_code": getattr(e, "status_code", None),
                "models": None,
                "latency_ms": latency
            }

    async def list_models(self) -> List[str]:
        status_code = None
        raw_count = 0
        parsed_count = 0
        models = []
        raw_response_preview = []
        url = f"{self.base_url}/models"
        try:
            client = self._get_client()
            models_list = client.models.list()
            raw_response_preview = [m.id for m in models_list.data]
            models = list(raw_response_preview)
            raw_count = len(models_list.data)
            parsed_count = len(models)
            status_code = 200
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to query ChatAnywhere translation models: {e}")

        if not models:
            models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
            parsed_count = len(models)

        print(f"\n[RAW CHATANYWHERE TRANSLATION MODEL LISTING AUDIT]")
        print(f"  Provider:             ChatAnywhere (Translation)")
        print(f"  Endpoint:             {url}")
        print(f"  Status Code:          {status_code}")
        print(f"  Raw API count:        {raw_count}")
        print(f"  Raw model IDs:        {raw_response_preview}")
        print(f"  Returned model IDs:   {models}")
        print(f"===================================================\n")

        return models

    async def translate_segments(
        self, 
        segments: List[Dict[str, Any]], 
        target_lang: str, 
        glossary: Optional[Dict[str, str]] = None,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # 1. Compile translation rules system prompt
        if target_lang.lower() in ["vi", "vietnamese"]:
            system_instruction = (
                "You are a professional Chinese → Vietnamese movie subtitle translator.\n"
                "Requirements:\n"
                "- Translate naturally using Vietnamese conversational style (prefer natural spoken Vietnamese).\n"
                "- Preserve original meaning and emotional tone.\n"
                "- Preserve humor and sarcasm.\n"
                "- Never summarize.\n"
                "- Keep subtitle timing unchanged.\n"
                "- Preserve names (never translate proper names into pronouns).\n"
                "- Never use literal Chinese sentence structure.\n"
                "- Return JSON only.\n\n"
                "Relationship Rules for Vietnamese pronoun selection:\n"
                "- Infer relationships from previous subtitles.\n"
                "- Keep the same pronouns throughout the movie.\n"
                "- If uncertain, omit pronouns rather than guessing.\n"
                "- If speaking to parents: use 'mẹ' / 'ba' / 'con'.\n"
                "- If an older person speaks to a younger person: use 'con' for the younger person.\n"
                "- If a younger person speaks to an elder: use 'cháu' / 'con'.\n"
                "- If friends: use 'tớ' / 'cậu'.\n"
                "- If husband and wife: use 'anh' / 'em'.\n"
                "- If the relationship is unknown: avoid the literal pronoun 'bạn' and omit pronouns rather than guessing.\n\n"
                "You MUST preserve the input segment IDs exactly. Keep the JSON structure identical but add a 'confidence' field (0-100) scoring your confidence in the translation accuracy based on context.\n"
                "Translate ONLY the 'text' property value.\n"
                f"Translation Quality Setting: {self._quality_setting}\n"
                "Format the output as a valid, raw JSON list matching the input structure (e.g. [{\"id\": 0, \"text\": \"...\", \"confidence\": 98}]), with no extra conversational formatting."
            )
        else:
            system_instruction = (
                f"You are a professional translator translating text segments to the target language: '{target_lang}'.\n"
                "You MUST preserve the input segment IDs exactly. Keep the JSON structure identical but add a 'confidence' field (0-100) scoring your translation accuracy.\n"
                "Translate ONLY the 'text' property value.\n"
                f"Translation Quality Setting: {self._quality_setting}\n"
                "Format the output as a valid, raw JSON list matching the input structure (e.g. [{\"id\": 0, \"text\": \"...\", \"confidence\": 95}]), with no extra conversational formatting."
            )
        if glossary:
            system_instruction += f"\n\nGlossary Rules:\n{glossary}"
            
        if context:
            system_instruction += f"\n\nContext Context (Previous Scene Dialogue / Speakers):\n{context}"

        prompt_content = json.dumps(segments, ensure_ascii=False)

        try:
            client = self._get_client()
            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt_content}
            ]
            response = client.chat.completions.create(
                model=self._model,
                messages=messages
            )
            response_text = response.choices[0].message.content or ""
        except Exception as e:
            raise AIProviderException(f"ChatAnywhere translation request failed: {str(e)}")

        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            lines = cleaned_text.splitlines()
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        try:
            translated_data = json.loads(cleaned_text)
            if isinstance(translated_data, dict):
                if "id" in translated_data and "text" in translated_data:
                    translated_data = [translated_data]
                else:
                    for val in translated_data.values():
                        if isinstance(val, list):
                            translated_data = val
                            break
            if not isinstance(translated_data, list):
                raise ValueError(f"Expected a list mapping translated segments. Got: {type(translated_data)}")
            return translated_data
        except Exception as e:
            raise AIProviderException(f"Translation provider failed to parse LLM response: {str(e)}. Raw response: {response_text}")
