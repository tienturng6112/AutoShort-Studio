import enum
from typing import Any, Dict, Type, Callable, Optional, Union

class Lifetime(enum.Enum):
    """Lifetime scopes for injected dependencies."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"

class DependencyContainer:
    """Dependency Injection Container managing Singleton, Scoped, and Transient lifetimes."""
    
    _registry: Dict[Type[Any], Dict[str, Any]] = {}
    _singletons: Dict[Type[Any], Any] = {}
    _active_scope: Optional[Dict[Type[Any], Any]] = None

    @classmethod
    def register(
        cls, 
        port: Type[Any], 
        factory_or_instance: Union[Any, Callable[[], Any]], 
        lifetime: Lifetime = Lifetime.SINGLETON
    ) -> None:
        """Binds a concrete class factory or instance to its abstract port interface.
        
        Args:
            port (Type[Any]): The target abstract interface or class.
            factory_or_instance (Union[Any, Callable[[], Any]]): Instantiation factory or resolved object.
            lifetime (Lifetime): Object lifecycle scope.
        """
        cls._registry[port] = {
            "factory": factory_or_instance if callable(factory_or_instance) else lambda: factory_or_instance,
            "lifetime": lifetime
        }
        if lifetime == Lifetime.SINGLETON and not callable(factory_or_instance):
            cls._singletons[port] = factory_or_instance

    @classmethod
    def resolve(cls, port: Type[Any]) -> Any:
        """Retrieves the registered adapter instance for the specified port.
        
        Args:
            port (Type[Any]): The port type lookup.
            
        Returns:
            Any: The resolved concrete instance.
            
        Raises:
            KeyError: If no adapter has been registered for the port.
            RuntimeError: If resolving a Scoped service outside an active scope.
        """
        if port not in cls._registry:
            raise KeyError(f"Dependency Injection Error: Port {port.__name__} has not been registered in the Container.")
            
        reg = cls._registry[port]
        lifetime = reg["lifetime"]
        factory = reg["factory"]
        
        if lifetime == Lifetime.SINGLETON:
            if port not in cls._singletons:
                cls._singletons[port] = factory()
            return cls._singletons[port]
            
        elif lifetime == Lifetime.SCOPED:
            if cls._active_scope is None:
                raise RuntimeError(
                    f"Dependency Injection Error: Resolving Scoped service {port.__name__} outside of an active scope."
                )
            if port not in cls._active_scope:
                cls._active_scope[port] = factory()
            return cls._active_scope[port]
            
        else:  # Lifetime.TRANSIENT
            return factory()

    @classmethod
    def begin_scope(cls) -> Dict[Type[Any], Any]:
        """Starts a scoped request/session context.
        
        Returns:
            Dict[Type[Any], Any]: The active scope dictionary.
        """
        cls._active_scope = {}
        return cls._active_scope

    @classmethod
    def end_scope(cls) -> None:
        """Destroys and clears the active scoped context."""
        if cls._active_scope is not None:
            cls._active_scope.clear()
        cls._active_scope = None

    @classmethod
    def clear(cls) -> None:
        """Clears all registry mappings, singletons, and active scopes."""
        cls._registry.clear()
        cls._singletons.clear()
        cls._active_scope = None
