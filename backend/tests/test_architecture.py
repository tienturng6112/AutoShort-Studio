import pytest
from backend.core.container import DependencyContainer, Lifetime
from backend.providers.base_provider import BaseProvider
from backend.workflow.base_node import BaseNode

def test_di_container_singleton():
    DependencyContainer.clear()
    class ITestService:
        pass
    class ConcreteService(ITestService):
        pass
    
    # Register factory with SINGLETON lifetime
    DependencyContainer.register(ITestService, lambda: ConcreteService(), Lifetime.SINGLETON)
    
    res1 = DependencyContainer.resolve(ITestService)
    res2 = DependencyContainer.resolve(ITestService)
    assert res1 is res2
    assert isinstance(res1, ConcreteService)

def test_di_container_transient():
    DependencyContainer.clear()
    class ITestService:
        pass
    class ConcreteService(ITestService):
        pass
        
    # Register factory with TRANSIENT lifetime
    DependencyContainer.register(ITestService, lambda: ConcreteService(), Lifetime.TRANSIENT)
    
    res1 = DependencyContainer.resolve(ITestService)
    res2 = DependencyContainer.resolve(ITestService)
    assert res1 is not res2
    assert isinstance(res1, ConcreteService)
    assert isinstance(res2, ConcreteService)

def test_di_container_scoped():
    DependencyContainer.clear()
    class ITestService:
        pass
    class ConcreteService(ITestService):
        pass
        
    # Register factory with SCOPED lifetime
    DependencyContainer.register(ITestService, lambda: ConcreteService(), Lifetime.SCOPED)
    
    # Outside scope resolving should fail
    with pytest.raises(RuntimeError) as exc:
        DependencyContainer.resolve(ITestService)
    assert "outside of an active scope" in str(exc.value)
    
    # Within scope resolving should succeed and cache within the scope
    DependencyContainer.begin_scope()
    res1 = DependencyContainer.resolve(ITestService)
    res2 = DependencyContainer.resolve(ITestService)
    assert res1 is res2
    assert isinstance(res1, ConcreteService)
    DependencyContainer.end_scope()
    
    # After ending scope, resolving should fail again
    with pytest.raises(RuntimeError):
        DependencyContainer.resolve(ITestService)

def test_di_container_unregistered_key_error():
    DependencyContainer.clear()
    class IUnregistered:
        pass
        
    with pytest.raises(KeyError) as exc_info:
        DependencyContainer.resolve(IUnregistered)
        
    assert "has not been registered" in str(exc_info.value)

def test_abstract_provider_instantiation_fails():
    # Attempting to instantiate an abstract class with abstract methods should raise TypeError
    with pytest.raises(TypeError):
        # BaseProvider has abstract methods: test_connection, list_models, chat, stream_chat, embeddings
        BaseProvider(name="mock")

def test_abstract_node_instantiation_fails():
    with pytest.raises(TypeError):
        # BaseNode has abstract methods: validate_inputs, execute, rollback
        BaseNode(name="mock")


