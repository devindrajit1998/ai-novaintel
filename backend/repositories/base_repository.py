"""
Base repository with common CRUD operations.
"""
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from db.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common database operations."""
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get entity by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        Get all entities with optional filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field: value filters
            order_by: Field name to order by (with optional - prefix for DESC)
        """
        query = self.db.query(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        # Apply ordering
        if order_by:
            if order_by.startswith("-"):
                # Descending order
                field = order_by[1:]
                if hasattr(self.model, field):
                    query = query.order_by(getattr(self.model, field).desc())
            else:
                # Ascending order
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, **kwargs) -> ModelType:
        """Create a new entity."""
        entity = self.model(**kwargs)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """Update an entity by ID."""
        entity = self.get_by_id(id)
        if not entity:
            return None
        
        for field, value in kwargs.items():
            if hasattr(entity, field):
                setattr(entity, field, value)
        
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, id: int) -> bool:
        """Delete an entity by ID."""
        entity = self.get_by_id(id)
        if not entity:
            return False
        
        self.db.delete(entity)
        self.db.commit()
        return True
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters."""
        query = self.db.query(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        return query.count()
    
    def exists(self, id: int) -> bool:
        """Check if entity exists."""
        return self.get_by_id(id) is not None

