from pydantic import BaseModel, Field
from typing import Dict, Optional

class ProviderConfig(BaseModel):
    """Configuration settings schema for instantiating an AI or media provider."""
    api_key: Optional[str] = Field(default=None, description="Encrypted or plain API access token")
    base_url: Optional[str] = Field(default=None, description="Custom endpoint base gateway URL")
    default_model: Optional[str] = Field(default=None, description="Default model descriptor used as fallback")
    timeout: int = Field(default=30, description="Max request execution timeout limit in seconds")
    retry: int = Field(default=3, description="Max automatic execution retry limit on failed requests")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom HTTP headers payload passed to provider requests")
