from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class ILogger(ABC):
    """Port interface for structured logging across use cases, tracking core workflow tags."""
    
    @abstractmethod
    def info(
        self, 
        message: str, 
        trace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Logs standard informational logs with correlation tags.
        
        Args:
            message (str): Log message text.
            trace_id (Optional[str]): Distributed tracing identifier.
            project_id (Optional[str]): Correlated user project key.
            workflow_id (Optional[str]): Running workflow instance.
            provider_id (Optional[str]): Target provider adapter ID.
            context (Optional[Dict[str, Any]]): Additional metadata context.
        """
        pass

    @abstractmethod
    def warning(
        self, 
        message: str, 
        trace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Logs minor errors or alerts.
        
        Args:
            message (str): Log message text.
            trace_id (Optional[str]): Distributed tracing identifier.
            project_id (Optional[str]): Correlated user project key.
            workflow_id (Optional[str]): Running workflow instance.
            provider_id (Optional[str]): Target provider adapter ID.
            context (Optional[Dict[str, Any]]): Additional metadata context.
        """
        pass

    @abstractmethod
    def error(
        self, 
        message: str, 
        trace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Logs severe process failures.
        
        Args:
            message (str): Log message text.
            trace_id (Optional[str]): Distributed tracing identifier.
            project_id (Optional[str]): Correlated user project key.
            workflow_id (Optional[str]): Running workflow instance.
            provider_id (Optional[str]): Target provider adapter ID.
            context (Optional[Dict[str, Any]]): Additional metadata context.
        """
        pass

    @abstractmethod
    def debug(
        self, 
        message: str, 
        trace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Logs fine-grained developer diagnostics traces.
        
        Args:
            message (str): Log message text.
            trace_id (Optional[str]): Distributed tracing identifier.
            project_id (Optional[str]): Correlated user project key.
            workflow_id (Optional[str]): Running workflow instance.
            provider_id (Optional[str]): Target provider adapter ID.
            context (Optional[Dict[str, Any]]): Additional metadata context.
        """
        pass
