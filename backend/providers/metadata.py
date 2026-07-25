from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from backend.providers.capabilities import ProviderCapabilities

class ProviderMetadata(BaseModel):
    """Correlation descriptor mapping identification details to provider capabilities."""
    provider_id: str = Field(..., description="Machine-readable unique key identifier")
    display_name: str = Field(..., description="Friendly display name shown in user interface")
    provider_type: str = Field(default="generic", description="Type of provider (tts, translation, etc)")
    version: str = Field(default="1.0.0", description="Version of the provider")
    author: str = Field(default="Unknown", description="Author of the provider plugin")
    homepage: str = Field(default="", description="Homepage URL")
    description: str = Field(default="", description="Short description of the provider")
    capabilities: ProviderCapabilities = Field(..., description="Capabilities capabilities indicators matrix")
    
    models: List[str] = Field(default_factory=list, description="List of supported models")
    voices: List[Dict[str, Any]] = Field(default_factory=list, description="List of supported voices")
    limits: Dict[str, Any] = Field(default_factory=dict, description="Usage limits e.g. requests_per_minute")
