import pytest
from unittest.mock import MagicMock, patch
from backend.core.secrets_manager_impl import SimpleSecretsManager
from backend.providers.llm.chatanywhere.chatanywhere_provider import ChatAnywhereProvider
from backend.providers.config import ProviderConfig
from backend.providers.capabilities import ProviderCapabilities
from backend.providers.metadata import ProviderMetadata
from backend.providers.registry_impl import ProviderRegistry
from backend.providers.manager_impl import ProviderManager
from backend.providers.model_registry_impl import ModelRegistry
from backend.providers.factory_impl import ProviderFactory

@pytest.mark.asyncio
@patch("backend.providers.llm.chatanywhere.chatanywhere_provider.OpenAI")
async def test_chatanywhere_connection_and_list_models(mock_openai_class: MagicMock) -> None:
    # Setup mock OpenAI client
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock models.list() output
    mock_model_1 = MagicMock()
    mock_model_1.id = "gpt-3.5-turbo"
    mock_model_2 = MagicMock()
    mock_model_2.id = "gpt-4"
    mock_client.models.list.return_value.data = [mock_model_1, mock_model_2]

    # Instantiate provider
    provider = ChatAnywhereProvider(name="chatanywhere", api_key="secret-key", base_url="http://mock-url")
    
    # 1. Test test_connection()
    connected = await provider.test_connection()
    assert connected["success"] is True
    mock_client.models.list.assert_called_once()
    assert "latency_ms" in connected

    # 2. Test list_models()
    models = await provider.list_models()
    assert models == ["gpt-3.5-turbo", "gpt-4"]


@pytest.mark.asyncio
@patch("backend.providers.llm.chatanywhere.chatanywhere_provider.OpenAI")
async def test_provider_registration_and_model_cache(mock_openai_class: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_model = MagicMock()
    mock_model.id = "gpt-3.5-turbo"
    mock_client.models.list.return_value.data = [mock_model]

    # Initialize registries
    registry = ProviderRegistry()
    manager = ProviderManager()
    model_reg = ModelRegistry(manager)
    secrets_mgr = SimpleSecretsManager()
    factory = ProviderFactory(secrets_mgr)

    # Setup config & metadata
    # bW9jay1rZXk= is base64 for "mock-key"
    config = ProviderConfig(api_key="bW9jay1rZXk=", base_url="http://mock")
    caps = ProviderCapabilities(supports_chat=True, supports_stream=True)
    meta = ProviderMetadata(provider_id="chatanywhere", display_name="ChatAnywhere", capabilities=caps)

    # Registry registration
    registry.register_provider(ChatAnywhereProvider, meta)
    assert meta in registry.get_available_providers()

    # Dynamic creation using Factory & SecretsManager decryption
    provider_instance = factory.create_provider(ChatAnywhereProvider, config)
    assert provider_instance.api_key == "mock-key"

    # Registry resolution
    resolved_instance = registry.resolve_provider("chatanywhere")
    assert isinstance(resolved_instance, ChatAnywhereProvider)

    # Register instance in Manager
    manager.register_provider("chatanywhere", provider_instance, meta)
    assert manager.get_provider("chatanywhere") is provider_instance

    # 3. Model Cache check
    assert model_reg.get_cached_models("chatanywhere") == []
    
    # Trigger cache refresh
    refreshed = await model_reg.refresh_models("chatanywhere")
    assert refreshed == ["gpt-3.5-turbo"]
    assert model_reg.get_cached_models("chatanywhere") == ["gpt-3.5-turbo"]
