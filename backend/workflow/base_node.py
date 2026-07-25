from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseNode(ABC):
    """Abstract base class for workflow pipeline nodes (Command Pattern)."""
    
    def __init__(self, name: str, retry_limit: int = 3):
        self.name = name
        self.retry_limit = retry_limit

    @abstractmethod
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validates node inputs before execution."""
        pass

    @abstractmethod
    async def execute(self, context: Any) -> Dict[str, Any]:
        """
        Executes business process step logic.
        Returns dictionary containing outputs to add to the pipeline context.
        """
        pass

    @abstractmethod
    async def rollback(self, context: Any) -> bool:
        """Rolls back side effects in case of later step failures."""
        pass
