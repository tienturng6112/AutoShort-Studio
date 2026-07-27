from typing import Optional
from backend.prompts.prompt_loader import PromptLoader
from backend.services.conversation import Conversation
from backend.services.llm_service import ILLMService

class ScriptGenerationService:
    """Service coordinates script drafting by loading dynamic templates, forming conversations, and querying LLMs."""
    
    def __init__(self, llm_service: ILLMService, prompt_template_path: str, llm_provider_id: str = "llm") -> None:
        self._llm_service = llm_service
        self._template_path = prompt_template_path
        self._llm_provider_id = llm_provider_id

    async def generate_script(self, topic: str, model_override: Optional[str] = None, provider_id_override: Optional[str] = None) -> str:
        """Loads prompt layouts from YAML, formats variables, and queries the LLM.
        
        Args:
            topic (str): The video target topic parameter.
            model_override (Optional[str]): Target model identifier.
            provider_id_override (Optional[str]): Target provider identifier override.
            
        Returns:
            str: The raw generated video script text.
        """
        # 1. Load templates dynamically
        templates = PromptLoader.load_from_yaml(self._template_path)
        system_prompt = templates.get("system_prompt", "You are an expert video scriptwriter.")
        user_template = templates.get("user_template", "Write a short video script on: {topic}")
        
        # 2. Format user template variables
        user_prompt = user_template.format(topic=topic)
        
        # 3. Build Conversation context
        conversation = Conversation(system_message=system_prompt)
        conversation.add_user_message(user_prompt)
        
        # 4. Execute completions
        pid = provider_id_override or self._llm_provider_id
        script_output = await self._llm_service.chat(conversation, model=model_override, provider_id=pid)
        return script_output
