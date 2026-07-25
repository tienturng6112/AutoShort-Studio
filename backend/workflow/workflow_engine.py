from abc import ABC, abstractmethod
from backend.workflow.base_node import BaseNode

class IWorkflowEngine(ABC):
    """Port interface for Node-Based Workflow Orchestrator."""
    
    @abstractmethod
    def register_node(self, node: BaseNode) -> None:
        """Registers a node to the execution pipeline."""
        pass
        
    @abstractmethod
    async def execute_workflow(self, project_id: str) -> None:
        """Orchestrates pipeline nodes execution sequence, supporting state checkpoints, logging, retries, and clean rollbacks."""
        pass
