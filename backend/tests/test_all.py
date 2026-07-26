import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.core.database import Base
from backend.app.repositories.base import BaseRepository
from backend.app.models.models import Provider, Project, Setting
from backend.app.repositories.repositories import ProviderRepository, SettingRepository
from backend.app.providers.factory import AIProviderFactory
from backend.app.services.prompt_service import PromptService
import pytest_asyncio

# Test Database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    # Setup in-memory SQLite engine
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
        
    await engine.dispose()

@pytest.mark.asyncio
async def test_database_crud(db_session: AsyncSession):
    # Test Create Provider
    repo = ProviderRepository(db_session)
    provider = await repo.create({
        "name": "mock-provider",
        "api_key": "test_key",
        "base_url": "http://mock.endpoint",
        "is_active": True
    })
    await db_session.commit()
    
    assert provider.id is not None
    assert provider.name == "mock-provider"
    
    # Test Get Active
    actives = await repo.get_active()
    assert len(actives) == 1
    assert actives[0].name == "mock-provider"
    
    # Test Update
    updated = await repo.update(provider, {"api_key": "new_key"})
    await db_session.commit()
    assert updated.api_key == "new_key"
    
    # Test Delete
    deleted = await repo.delete(provider.id)
    await db_session.commit()
    assert deleted.id == provider.id
    
    check_get = await repo.get(provider.id)
    assert check_get is None

@pytest.mark.asyncio
async def test_settings_repository(db_session: AsyncSession):
    repo = SettingRepository(db_session)
    
    # Test default getter
    val = await repo.get_value("test_setting", default="fallback")
    assert val == "fallback"
    
    # Test setting value
    setting = await repo.set_value("test_setting", "my_value")
    await db_session.commit()
    
    check_val = await repo.get_value("test_setting")
    assert check_val == "my_value"

def test_ai_provider_factory():
    # Test ChatAnywhere factory resolution
    p_ca = AIProviderFactory.get_provider("chatanywhere", api_key="sk-ca")
    assert p_ca.provider_name == "chatanywhere"
    assert p_ca.base_url == "https://api.chatanywhere.tech/v1"
    
