import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, List, Type

class DomainEvent:
    """Base class for all Domain events, capturing creation timestamp and unique identifier."""
    
    def __init__(self) -> None:
        self.event_id: str = str(uuid.uuid4())
        self.timestamp: datetime = datetime.utcnow()


class IEventBus(ABC):
    """Port interface for central Event Bus subscription and dispatch."""
    
    @abstractmethod
    def subscribe(
        self, 
        event_type: Type[DomainEvent], 
        handler: Callable[[Any], Coroutine[Any, Any, None]]
    ) -> None:
        """Subscribes an asynchronous handler to a specific DomainEvent type.
        
        Args:
            event_type (Type[DomainEvent]): Class type of event.
            handler (Callable[[Any], Coroutine[Any, Any, None]]): Async listener function.
        """
        pass

    @abstractmethod
    def unsubscribe(
        self, 
        event_type: Type[DomainEvent], 
        handler: Callable[[Any], Coroutine[Any, Any, None]]
    ) -> None:
        """Removes an active asynchronous handler subscription.
        
        Args:
            event_type (Type[DomainEvent]): Class type.
            handler (Callable[[Any], Coroutine[Any, Any, None]]): Async handler reference.
        """
        pass

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publishes an event asynchronously, triggering all registered listeners in parallel.
        
        Args:
            event (DomainEvent): The target domain event instance.
        """
        pass


class AsyncEventBus(IEventBus):
    """Concrete in-memory Asynchronous Event Bus adapter."""
    
    def __init__(self) -> None:
        self._handlers: Dict[Type[DomainEvent], List[Callable[[Any], Coroutine[Any, Any, None]]]] = {}

    def subscribe(
        self, 
        event_type: Type[DomainEvent], 
        handler: Callable[[Any], Coroutine[Any, Any, None]]
    ) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(
        self, 
        event_type: Type[DomainEvent], 
        handler: Callable[[Any], Coroutine[Any, Any, None]]
    ) -> None:
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(type(event), [])
        # Trigger all coroutine handlers concurrently in the background
        tasks = [asyncio.create_task(handler(event)) for handler in handlers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
