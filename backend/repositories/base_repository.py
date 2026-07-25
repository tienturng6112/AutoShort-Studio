from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar, Any

T = TypeVar("T")

class IRepository(Generic[T], ABC):
    """Port interface for SQLAlchemy data CRUD gateways."""
    
    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        """Loads a record matching the unique identifier key.
        
        Args:
            id (Any): PK identifier.
            
        Returns:
            Optional[T]: Deserialized Domain Entity or database row, or None.
        """
        pass
        
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Loads paginated list of all tables records.
        
        Args:
            skip (int): Paginated offset skip count.
            limit (int): Paginated chunk limits.
            
        Returns:
            List[T]: List of records.
        """
        pass
        
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Stores a new record inside the persistence adapter.
        
        Args:
            entity (T): Domain schema instance.
            
        Returns:
            T: Created and flushed instance containing auto-keys.
        """
        pass
        
    @abstractmethod
    async def update(self, entity: T, updates: dict[str, Any]) -> T:
        """Modifies attributes of an existing persistence model.
        
        Args:
            entity (T): target instance reference.
            updates (dict[str, Any]): Dictionary mapping updated columns to values.
            
        Returns:
            T: Modified entity.
        """
        pass
        
    @abstractmethod
    async def delete(self, id: Any) -> Optional[T]:
        """Removes the matching record from database.
        
        Args:
            id (Any): Unique key.
            
        Returns:
            Optional[T]: Deleted instance, or None if not found.
        """
        pass
