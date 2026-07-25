from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional, Tuple, Any
from backend.providers.manager import IProviderManager
from backend.services.conversation import Conversation

class ILLMService(ABC):
    """Port interface orchestrating completions calls against active AI providers."""
    
    @abstractmethod
    async def chat(
        self, 
        conversation: Conversation, 
        model: Optional[str] = None, 
        json_mode: bool = False,
        provider_id: Optional[str] = None
    ) -> str:
        """Executes a synchronous completions request, appending the response to the conversation history.
        
        Args:
            conversation (Conversation): Tracked chat turn history context.
            model (Optional[str]): Explicit override target model name.
            json_mode (bool): Enforces raw JSON outputs.
            provider_id (Optional[str]): Explicit target provider ID.
            
        Returns:
            str: Completed response text.
        """
        pass

    @abstractmethod
    async def stream_chat(
        self, 
        conversation: Conversation, 
        model: Optional[str] = None,
        provider_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Executes a streaming completions request, yielding tokens and appending the final content to history.
        
        Args:
            conversation (Conversation): Tracked chat turn history context.
            model (Optional[str]): Target model identifier name.
            provider_id (Optional[str]): Explicit target provider ID.
            
        Returns:
            AsyncGenerator[str, None]: Generated text tokens.
        """
        pass


class LLMService(ILLMService):
    """Implementation of ILLMService managing active provider routing and model fallbacks."""
    
    def __init__(self, provider_manager: Optional[Any] = None) -> None:
        if provider_manager is None:
            from backend.providers.llm.manager import LLMProviderManager
            provider_manager = LLMProviderManager()
        self._manager = provider_manager

    def _resolve_provider_and_model(self, requested_model: Optional[str] = None, provider_id: Optional[str] = None) -> Tuple[Any, str]:
        """Resolves the provider and target model parameters."""
        if not provider_id:
            raise ValueError("LLM Service Error: provider_id is required. Active/default provider fallback is disabled.")
        provider = self._manager.get(provider_id)
        if not provider:
            raise RuntimeError(f"LLM Service Routing Error: Provider '{provider_id}' not resolved.")
        model_name = requested_model or "gpt-3.5-turbo"
        return provider, model_name

    async def chat(
        self, 
        conversation: Conversation, 
        model: Optional[str] = None, 
        json_mode: bool = False,
        provider_id: Optional[str] = None
    ) -> str:
        provider, model_name = self._resolve_provider_and_model(model, provider_id)
        
        # Extracts last user query and the system prompt to fit standard provider calls
        history = conversation.get_history()
        system_prompt = next((msg["content"] for msg in history if msg["role"] == "system"), None)
        user_messages = [msg["content"] for msg in history if msg["role"] == "user"]
        prompt = user_messages[-1] if user_messages else ""
        
        response = await provider.chat(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model_name,
            json_mode=json_mode
        )
        conversation.add_assistant_message(response)
        return response

    async def stream_chat(
        self, 
        conversation: Conversation, 
        model: Optional[str] = None,
        provider_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        provider, model_name = self._resolve_provider_and_model(model, provider_id)
        
        history = conversation.get_history()
        system_prompt = next((msg["content"] for msg in history if msg["role"] == "system"), None)
        user_messages = [msg["content"] for msg in history if msg["role"] == "user"]
        prompt = user_messages[-1] if user_messages else ""
        
        full_chunks = []
        async for chunk in provider.stream_chat(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model_name
        ):
            full_chunks.append(chunk)
            yield chunk
            
        conversation.add_assistant_message("".join(full_chunks))
