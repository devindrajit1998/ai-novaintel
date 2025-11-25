"""
Service layer for Proposal business logic.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import sys
from repositories.proposal_repository import ProposalRepository
from repositories.project_repository import ProjectRepository
from models.proposal import Proposal
from models.project import Project
from models.user import User
from models.notification import Notification
from utils.email_service import send_proposal_submission_email


class ProposalService:
    """Service for proposal business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.proposal_repo = ProposalRepository(db)
        self.project_repo = ProjectRepository(db)
    
    def get_proposal(self, proposal_id: int, user_id: int) -> Optional[Proposal]:
        """
        Get proposal with ownership verification.
        
        Args:
            proposal_id: Proposal ID
            user_id: User ID for ownership check
        
        Returns:
            Proposal if found and user has access, None otherwise
        """
        proposal = self.proposal_repo.get_by_id(proposal_id)
        if not proposal:
            return None
        
        # Verify ownership
        project = self.project_repo.get_by_id(proposal.project_id)
        if not project or project.owner_id != user_id:
            return None
        
        return proposal
    
    def get_proposal_by_project(self, project_id: int, user_id: int) -> Optional[Proposal]:
        """Get proposal for a project with ownership verification."""
        project = self.project_repo.get_by_id(project_id)
        if not project or project.owner_id != user_id:
            return None
        
        return self.proposal_repo.get_by_project_id(project_id)
    
    def create_proposal(
        self,
        project_id: int,
        user_id: int,
        title: str = "Proposal",
        sections: Optional[List[Dict[str, Any]]] = None,
        template_type: str = "full"
    ) -> Optional[Proposal]:
        """Create a new proposal."""
        # Verify ownership
        project = self.project_repo.get_by_id(project_id)
        if not project or project.owner_id != user_id:
            return None
        
        # Check if proposal already exists
        existing = self.proposal_repo.get_by_project_id(project_id)
        if existing:
            return None  # Proposal already exists
        
        proposal = self.proposal_repo.create(
            project_id=project_id,
            title=title,
            sections=sections,
            template_type=template_type,
            status="draft"
        )
        
        return proposal
    
    def update_proposal(
        self,
        proposal_id: int,
        user_id: int,
        **updates
    ) -> Optional[Proposal]:
        """Update proposal with ownership verification."""
        proposal = self.get_proposal(proposal_id, user_id)
        if not proposal:
            return None
        
        # Don't allow status changes through update (use submit/review methods)
        updates.pop('status', None)
        updates.pop('submitted_at', None)
        updates.pop('reviewed_at', None)
        updates.pop('reviewed_by', None)
        
        return self.proposal_repo.update(proposal_id, **updates)
    
    async def submit_proposal(
        self,
        proposal_id: int,
        user: User,
        message: Optional[str] = None,
        manager_id: Optional[int] = None
    ) -> Optional[Proposal]:
        """
        Submit proposal for approval.
        
        Args:
            proposal_id: Proposal ID
            user: User submitting the proposal
            message: Optional message from submitter
            manager_id: Optional specific manager ID
        
        Returns:
            Updated proposal or None if error
        """
        proposal = self.get_proposal(proposal_id, user.id)
        if not proposal:
            return None
        
        # Check current status
        if proposal.status == "pending_approval":
            return None  # Already submitted
        
        # Update status
        proposal.status = "pending_approval"
        proposal.submitter_message = message
        from utils.timezone import now_utc_from_ist
        proposal.submitted_at = now_utc_from_ist()
        
        # Get project for email
        project = self.project_repo.get_by_id(proposal.project_id)
        if not project:
            return None
        
        # Send email to all admins
        ADMIN_ROLE = "pre_sales_manager"
        from models.user import User as UserModel
        admins = self.db.query(UserModel).filter(
            UserModel.role == ADMIN_ROLE,
            UserModel.is_active == True,
            UserModel.email_verified == True
        ).all()
        
        # Prepare proposal data for email
        proposal_sections = proposal.sections if proposal.sections else []
        submitted_at_str = proposal.submitted_at.strftime("%Y-%m-%d %H:%M:%S UTC") if proposal.submitted_at else None
        
        # Send email and create notification for all admins
        for admin in admins:
            # Create in-app notification
            notification = Notification(
                user_id=admin.id,
                type="info",
                title="New Proposal Submitted",
                message=f"Proposal '{proposal.title}' submitted by {user.full_name}",
                metadata_={"proposal_id": proposal.id, "project_id": project.id, "submitter_id": user.id}
            )
            self.db.add(notification)
            
            # Send email notification
            try:
                await send_proposal_submission_email(
                    manager_email=admin.email,
                    manager_name=admin.full_name,
                    proposal_title=proposal.title,
                    submitter_name=user.full_name,
                    submitter_message=message,
                    proposal_id=proposal.id,
                    project_id=project.id,
                    project_name=project.name,
                    client_name=project.client_name,
                    industry=project.industry,
                    region=project.region,
                    proposal_sections=proposal_sections,
                    template_type=proposal.template_type,
                    submitted_at=submitted_at_str
                )
            except Exception as e:
                # Error already logged in email_service with full details
                print(f"[PROPOSAL SUBMISSION WARNING] Email notification failed for admin: {admin.email}, Proposal ID: {proposal.id}", file=sys.stderr, flush=True)
        
        self.db.commit()
        self.db.refresh(proposal)
        
        return proposal
    
    def review_proposal(
        self,
        proposal_id: int,
        reviewer: User,
        action: str,
        feedback: Optional[str] = None
    ) -> Optional[Proposal]:
        """
        Review proposal (approve/reject/hold).
        
        Args:
            proposal_id: Proposal ID
            reviewer: User reviewing the proposal
            action: "approve", "reject", or "hold"
            feedback: Optional feedback
        
        Returns:
            Updated proposal or None if error
        """
        MANAGER_ROLE = "pre_sales_manager"
        if reviewer.role != MANAGER_ROLE:
            return None
        
        proposal = self.proposal_repo.get_by_id(proposal_id)
        if not proposal:
            return None
        
        # Validate action
        ALLOWED_ACTIONS = ["approve", "reject", "hold"]
        if action not in ALLOWED_ACTIONS:
            return None
        
        # Check if proposal is in a reviewable state
        if proposal.status not in ["pending_approval", "on_hold"]:
            return None
        
        # Update status
        status_map = {
            "approve": "approved",
            "reject": "rejected",
            "hold": "on_hold"
        }
        
        proposal = self.proposal_repo.update_status(
            proposal_id=proposal_id,
            status=status_map[action],
            admin_feedback=feedback,
            reviewed_by=reviewer.id
        )
        
        if proposal:
            from utils.timezone import now_utc_from_ist
            proposal.reviewed_at = now_utc_from_ist()
            self.db.commit()
            self.db.refresh(proposal)
        
        return proposal

