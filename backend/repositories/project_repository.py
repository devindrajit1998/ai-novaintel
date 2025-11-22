"""
Repository for Project data access.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from repositories.base_repository import BaseRepository
from models.project import Project


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project operations."""
    
    def __init__(self, db: Session):
        super().__init__(Project, db)
    
    def get_by_owner(self, owner_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get projects by owner ID."""
        return self.db.query(self.model).filter(
            self.model.owner_id == owner_id
        ).offset(skip).limit(limit).all()
    
    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get projects by status."""
        return self.db.query(self.model).filter(
            self.model.status == status
        ).offset(skip).limit(limit).all()

