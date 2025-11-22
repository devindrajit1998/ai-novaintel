"""
Repository for Proposal data access.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from repositories.base_repository import BaseRepository
from models.proposal import Proposal


class ProposalRepository(BaseRepository[Proposal]):
    """Repository for Proposal operations."""
    
    def __init__(self, db: Session):
        super().__init__(Proposal, db)
    
    def get_by_project_id(self, project_id: int) -> Optional[Proposal]:
        """Get proposal by project ID."""
        return self.db.query(self.model).filter(
            self.model.project_id == project_id
        ).first()
    
    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Proposal]:
        """Get proposals by status."""
        return self.db.query(self.model).filter(
            self.model.status == status
        ).offset(skip).limit(limit).all()
    
    def get_pending_approval(self) -> List[Proposal]:
        """Get all pending approval proposals."""
        return self.get_by_status("pending_approval")
    
    def update_status(
        self,
        proposal_id: int,
        status: str,
        admin_feedback: Optional[str] = None,
        reviewed_by: Optional[int] = None
    ) -> Optional[Proposal]:
        """Update proposal status and review information."""
        proposal = self.get_by_id(proposal_id)
        if not proposal:
            return None
        
        proposal.status = status
        if admin_feedback is not None:
            proposal.admin_feedback = admin_feedback
        if reviewed_by is not None:
            proposal.reviewed_by = reviewed_by
        
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

