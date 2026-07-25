from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ProviderHealthStatus(BaseModel):
    """Health parameters monitoring connection health and latencies of an active provider."""
    connection_status: str = Field(default="unknown", description="Status code (healthy, degraded, offline, unknown)")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the last diagnostics check")
    latency_ms: float = Field(default=-1.0, description="Response roundtrip latency in milliseconds")
    model_cache: List[str] = Field(default_factory=list, description="List of cached active models")

class IProviderHealth(ABC):
    """Port interface monitoring real-time connectivity state, latency, and status caches."""
    
    @abstractmethod
    async def check_health(self, provider_id: str) -> ProviderHealthStatus:
        """Executes connection test diagnostics to update the cached status.
        
        Args:
            provider_id (str): Target registered provider key.
            
        Returns:
            ProviderHealthStatus: Analyzed status parameters.
        """
        pass

    @abstractmethod
    def get_status(self, provider_id: str) -> Optional[ProviderHealthStatus]:
        """Retrieves current cached diagnostics status data.
        
        Args:
            provider_id (str): Target provider key.
            
        Returns:
            Optional[ProviderHealthStatus]: Diagnostic status, if cached.
        """
        pass
