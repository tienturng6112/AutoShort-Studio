from typing import Any, Dict, List, Optional
from backend.providers.speech.base_speech_provider import BaseSpeechProvider

class VoiceManager:
    """Manages registered TTS providers and handles queries for available voices."""

    def __init__(self) -> None:
        self._providers: Dict[str, BaseSpeechProvider] = {}

    def register_provider(self, name: str, provider: BaseSpeechProvider) -> None:
        """Registers a TTS provider by name.
        
        Args:
            name (str): Provider unique name.
            provider (BaseSpeechProvider): The provider instance.
        """
        self._providers[name] = provider

    async def list_voices(
        self, 
        language: Optional[str] = None, 
        gender: Optional[str] = None, 
        provider_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Queries and filters voices based on search criteria.
        
        Args:
            language (Optional[str]): Language filter (e.g. 'en', 'vi').
            gender (Optional[str]): Gender filter ('Male', 'Female').
            provider_name (Optional[str]): Provider filter ('edge-tts').
            
        Returns:
            List[Dict[str, Any]]: Filtered voice descriptor objects.
        """
        all_voices = []
        
        # Resolve target providers
        if provider_name:
            if provider_name in self._providers:
                target_providers = [(provider_name, self._providers[provider_name])]
            else:
                target_providers = []
        else:
            target_providers = list(self._providers.items())

        for p_name, prov in target_providers:
            voices = await prov.list_voices()
            for v in voices:
                # 1. Filter language locale
                if language:
                    v_lang = v.get("language", "").lower()
                    if language.lower() not in v_lang:
                        continue
                # 2. Filter gender
                if gender:
                    v_gender = v.get("gender", "").lower()
                    if gender.lower() != v_gender:
                        continue
                all_voices.append(v)
                
        return all_voices
