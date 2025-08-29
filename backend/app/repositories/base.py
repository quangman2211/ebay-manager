"""
Base Repository Implementation
Following SOLID principles - Dependency Inversion and Single Responsibility
YAGNI: Essential CRUD operations only
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import EbayManagerException

ModelType = TypeVar("ModelType")

class BaseRepositoryInterface(ABC, Generic[ModelType]):
    """
    SOLID: Interface Segregation & Dependency Inversion
    Abstract base for all repository interfaces
    """

    @abstractmethod
    async def create(self, obj: ModelType) -> ModelType:
        """Create new entity"""
        pass

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def update(self, id: int, update_data: Dict[str, Any]) -> ModelType:
        """Update entity by ID"""
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Delete entity by ID"""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all entities with pagination"""
        pass

class BaseRepository(BaseRepositoryInterface[ModelType]):
    """
    SOLID: Single Responsibility - Basic CRUD operations only
    YAGNI: Essential database operations, no complex querying
    """

    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    async def create(self, obj: ModelType) -> ModelType:
        """Create new entity"""
        try:
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise EbayManagerException(f"Failed to create {self.model.__name__}: {str(e)}")

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get entity by ID"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get {self.model.__name__}: {str(e)}")

    async def update(self, id: int, update_data: Dict[str, Any]) -> ModelType:
        """Update entity by ID"""
        try:
            entity = self.db.query(self.model).filter(self.model.id == id).first()
            if not entity:
                raise EbayManagerException(f"{self.model.__name__} not found")
            
            for key, value in update_data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            raise EbayManagerException(f"Failed to update {self.model.__name__}: {str(e)}")

    async def delete(self, id: int) -> bool:
        """Delete entity by ID"""
        try:
            entity = self.db.query(self.model).filter(self.model.id == id).first()
            if entity:
                self.db.delete(entity)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            raise EbayManagerException(f"Failed to delete {self.model.__name__}: {str(e)}")

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all entities with pagination"""
        try:
            return self.db.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get {self.model.__name__} list: {str(e)}")

    async def count(self) -> int:
        """Get total count of entities"""
        try:
            return self.db.query(self.model).count()
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to count {self.model.__name__}: {str(e)}")

    async def bulk_update(self, ids: List[int], update_data: Dict[str, Any]) -> int:
        """YAGNI: Simple bulk update operation"""
        try:
            if not ids:
                return 0
            
            updated_count = self.db.query(self.model).filter(
                self.model.id.in_(ids)
            ).update(
                update_data,
                synchronize_session=False
            )
            
            self.db.commit()
            return updated_count
        except SQLAlchemyError as e:
            self.db.rollback()
            raise EbayManagerException(f"Failed to bulk update {self.model.__name__}: {str(e)}")