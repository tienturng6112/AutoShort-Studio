import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.providers.base_provider import BaseProvider
from backend.providers.manager import IProviderManager
from backend.services.conversation import Conversation
from backend.services.cost_estimator import CostEstimator, ModelPricing
from backend.services.llm_service import LLMService
from backend.services.script_generator import ScriptGenerationService
from backend.services.token_counter import TokenCounter

def test_conversation_lifecycle() -> None:
    conv = Conversation(system_message="system instruction")
    assert len(conv.get_history()) == 1
    assert conv.get_history()[0] == {"role": "system", "content": "system instruction"}

    conv.add_user_message("user prompt")
    conv.add_assistant_message("assistant reply")
    assert len(conv.get_history()) == 3
    assert conv.get_history()[1] == {"role": "user", "content": "user prompt"}
    assert conv.get_history()[2] == {"role": "assistant", "content": "assistant reply"}

    conv.reset()
    assert len(conv.get_history()) == 1
    assert conv.get_history()[0] == {"role": "system", "content": "system instruction"}


def test_token_counter() -> None:
    text = "Hello world! This is a test script."
    count = TokenCounter.count_string_tokens(text)
    assert count > 0

    conv_messages = [
        {"role": "system", "content": "You are a writer."},
        {"role": "user", "content": "Write a script."}
    ]
    conv_count = TokenCounter.count_conversation_tokens(conv_messages)
    assert conv_count > 0


def test_cost_estimator() -> None:
    estimator = CostEstimator()
    pricing = ModelPricing(prompt_rate_per_1k=0.015, completion_rate_per_1k=0.02)
    estimator.update_pricing("custom-model", pricing)
    
    # 1000 prompt tokens = $0.015, 2000 completion tokens = $0.04
    est = estimator.estimate_cost("custom-model", 1000, 2000)
    assert est.prompt_cost == pytest.approx(0.015)
    assert est.completion_cost == pytest.approx(0.04)
    assert est.total_cost == pytest.approx(0.055)


@pytest.mark.asyncio
async def test_llm_service_and_script_generator() -> None:
    # Setup Mock Provider
    mock_provider = MagicMock(spec=BaseProvider)
    mock_provider.chat = AsyncMock(return_value="Engaging script output.")
    
    # Setup Mock Provider Manager
    mock_manager = MagicMock()
    mock_manager.get.return_value = mock_provider
    
    # Instantiate LLMService
    llm_service = LLMService(mock_manager)
    
    # Verify script generator with local YAML template path
    generator = ScriptGenerationService(
        llm_service=llm_service, 
        prompt_template_path="backend/prompts/script_generation.yaml",
        llm_provider_id="openai"
    )
    
    script = await generator.generate_script(topic="Quantum Mechanics")
    assert script == "Engaging script output."
    
    # Verify mock provider call parameters
    mock_provider.chat.assert_called_once()
    args, kwargs = mock_provider.chat.call_args
    assert "Quantum Mechanics" in kwargs.get("prompt", "")
    assert kwargs.get("model") == "gpt-3.5-turbo"
