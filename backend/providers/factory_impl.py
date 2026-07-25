from typing import Type
from backend.providers.base_provider import BaseProvider
from backend.providers.config import ProviderConfig
from backend.providers.factory import IProviderFactory
from backend.core.secrets_manager import ISecretsManager

class ProviderFactory(IProviderFactory):
    """Implementation of ProviderFactory dynamically building and instantiating provider objects."""

    def __init__(self, secrets_manager: ISecretsManager) -> None:
        self._secrets_manager = secrets_manager

    def create_provider(self, provider_class: Type[BaseProvider], config: ProviderConfig) -> BaseProvider:
        decrypted_key = None
        if config.api_key:
            decrypted_key = self._secrets_manager.decrypt(config.api_key)
            
        return provider_class(
            name=provider_class.__name__,
            api_key=decrypted_key,
            base_url=config.base_url
        )
