from typing import List, Optional, Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.base import BaseRepository
from backend.app.models.models import Provider, Model, Project, Asset, Prompt, History, Log, Setting

class ProviderRepository(BaseRepository[Provider]):
    def __init__(self, db: AsyncSession):
        super().__init__(Provider, db)
        
    async def get_active(self) -> List[Provider]:
        result = await self.db.execute(select(self.model).filter(self.model.is_active == True))
        return list(result.scalars().all())
        
    async def get_by_name(self, name: str) -> Optional[Provider]:
        result = await self.db.execute(select(self.model).filter(self.model.name == name))
        return result.scalars().first()

class ModelRepository(BaseRepository[Model]):
    def __init__(self, db: AsyncSession):
        super().__init__(Model, db)
        
    async def get_by_provider(self, provider_id: str) -> List[Model]:
        result = await self.db.execute(select(self.model).filter(self.model.provider_id == provider_id))
        return list(result.scalars().all())

class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)
        
    async def get_by_status(self, status: str) -> List[Project]:
        result = await self.db.execute(select(self.model).filter(self.model.status == status))
        return list(result.scalars().all())

class AssetRepository(BaseRepository[Asset]):
    def __init__(self, db: AsyncSession):
        super().__init__(Asset, db)
        
    async def get_by_project(self, project_id: str) -> List[Asset]:
        result = await self.db.execute(select(self.model).filter(self.model.project_id == project_id))
        return list(result.scalars().all())

class PromptRepository(BaseRepository[Prompt]):
    def __init__(self, db: AsyncSession):
        super().__init__(Prompt, db)
        
    async def get_by_group(self, group: str) -> List[Prompt]:
        result = await self.db.execute(select(self.model).filter(self.model.group == group))
        return list(result.scalars().all())
        
    async def get_by_group_and_name(self, group: str, name: str) -> Optional[Prompt]:
        result = await self.db.execute(
            select(self.model).filter(self.model.group == group, self.model.name == name)
        )
        return result.scalars().first()

class HistoryRepository(BaseRepository[History]):
    def __init__(self, db: AsyncSession):
        super().__init__(History, db)
        
    async def get_by_project(self, project_id: str) -> List[History]:
        result = await self.db.execute(
            select(self.model).filter(self.model.project_id == project_id).order_by(self.model.timestamp.desc())
        )
        return list(result.scalars().all())

class LogRepository(BaseRepository[Log]):
    def __init__(self, db: AsyncSession):
        super().__init__(Log, db)
        
    async def get_recent(self, limit: int = 100) -> List[Log]:
        result = await self.db.execute(
            select(self.model).order_by(self.model.timestamp.desc()).limit(limit)
        )
        return list(result.scalars().all())

class SettingRepository(BaseRepository[Setting]):
    def __init__(self, db: AsyncSession):
        super().__init__(Setting, db)
        
    async def get(self, key: Any) -> Optional[Setting]:
        result = await self.db.execute(select(self.model).filter(self.model.key == key))
        return result.scalars().first()
        
    async def delete(self, key: Any) -> Optional[Setting]:
        db_obj = await self.get(key)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.flush()
        return db_obj
        
    async def get_value(self, key: str, default: Any = None) -> Any:
        setting = await self.get(key)
        if setting:
            # Handle wrapping dict or raw value
            return setting.value.get("value") if isinstance(setting.value, dict) and "value" in setting.value else setting.value
        return default
        
    async def set_value(self, key: str, value: Any) -> Setting:
        setting = await self.get(key)
        payload = {"value": value}
        if setting:
            setting.value = payload
            self.db.add(setting)
            await self.db.flush()
            return setting
        else:
            setting = Setting(key=key, value=payload)
            self.db.add(setting)
            await self.db.flush()
            return setting
