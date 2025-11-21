from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from db.database import get_db
from models.user import User
from models.project import Project
from models.proposal import Proposal
from models.insights import Insights
from api.schemas.proposal import (
    ProposalCreate,
    ProposalUpdate,
    ProposalResponse,
    ProposalGenerateRequest,
    ProposalSaveDraftRequest,
    ProposalPreviewResponse,
    RegenerateSectionRequest,
    ProposalSubmitRequest,
    ProposalReviewRequest
)
from models.notification import Notification
from utils.dependencies import get_current_user
from services.proposal_templates import ProposalTemplates
from services.proposal_export import proposal_exporter

router = APIRouter()

@router.post("/save", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def save_proposal(
    proposal_data: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save or create a proposal."""
    try:
        # Verify project ownership
        project = db.query(Project).filter(
            Project.id == proposal_data.project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check if proposal already exists
        existing_proposal = db.query(Proposal).filter(
            Proposal.project_id == proposal_data.project_id
        ).first()
        
        if existing_proposal:
            # Update existing proposal
            update_data = proposal_data.model_dump(exclude_unset=True, exclude={"project_id"})
            for field, value in update_data.items():
                setattr(existing_proposal, field, value)
            db.commit()
            db.refresh(existing_proposal)
            return existing_proposal
        else:
            # Create new proposal
            new_proposal = Proposal(**proposal_data.model_dump())
            db.add(new_proposal)
            db.commit()
            db.refresh(new_proposal)
            return new_proposal
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save proposal: {str(e)}"
        )

@router.get("/by-project/{project_id}", response_model=ProposalResponse)
async def get_proposal_by_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get proposal for a specific project."""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get proposal for this project
    proposal = db.query(Proposal).filter(
        Proposal.project_id == project_id
    ).first()
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found for this project"
        )
    
    return proposal

@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific proposal."""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == proposal.project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return proposal

@router.put("/{proposal_id}", response_model=ProposalResponse)
async def update_proposal(
    proposal_id: int,
    proposal_data: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a proposal."""
    try:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Verify project ownership
        project = db.query(Project).filter(
            Project.id == proposal.project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update proposal
        update_data = proposal_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(proposal, field, value)
        
        db.commit()
        db.refresh(proposal)
        
        return proposal
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update proposal: {str(e)}"
        )

@router.post("/generate", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def generate_proposal(
    request: ProposalGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a new proposal from template, optionally populated with insights.
    """
    try:
        # Verify project ownership
        project = db.query(Project).filter(
            Project.id == request.project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check if proposal already exists
        existing_proposal = db.query(Proposal).filter(
            Proposal.project_id == request.project_id
        ).first()
        
        # Get template
        sections = ProposalTemplates.get_template(request.template_type)

        # Always try to populate with insights if available
        insights = db.query(Insights).filter(
            Insights.project_id == request.project_id
        ).first()

        if insights:
            # Get matching case studies from insights
            matching_case_studies = []
            
            # If selected_case_study_ids provided, prioritize those
            if request.selected_case_study_ids:
                from models.case_study import CaseStudy
                selected_case_studies = db.query(CaseStudy).filter(
                    CaseStudy.id.in_(request.selected_case_study_ids)
                ).all()
                matching_case_studies = [
                    {
                        "id": cs.id,
                        "title": cs.title,
                        "industry": cs.industry,
                        "impact": cs.impact,
                        "description": cs.description,
                        "project_description": cs.project_description
                    }
                    for cs in selected_case_studies
                ]
                # Also include any from insights that weren't selected (as fallback)
                if insights.matching_case_studies:
                    for cs in insights.matching_case_studies:
                        if cs.get("id") not in request.selected_case_study_ids:
                            matching_case_studies.append(cs)
            elif insights.matching_case_studies:
                matching_case_studies = insights.matching_case_studies
            elif insights.challenges:
                # Fallback: Try to get case studies from database based on challenges
                from models.case_study import CaseStudy
                all_case_studies = db.query(CaseStudy).limit(5).all()
                matching_case_studies = [
                    {
                        "id": cs.id,
                        "title": cs.title,
                        "industry": cs.industry,
                        "impact": cs.impact,
                        "description": cs.description
                    }
                    for cs in all_case_studies
                ]
            
            insights_dict = {
                "rfp_summary": insights.executive_summary or "",
                "challenges": insights.challenges or [],
                "value_propositions": insights.value_propositions or [],
                "matching_case_studies": matching_case_studies
            }
            
            # Get user settings for proposal generation
            proposal_tone = current_user.proposal_tone or "professional"
            ai_response_style = current_user.ai_response_style or "balanced"
            secure_mode = current_user.secure_mode if current_user.secure_mode is not None else False
            
            # Use AI to generate full content if use_insights is True, otherwise use basic population
            sections = ProposalTemplates.populate_from_insights(
                request.template_type,
                insights_dict,
                use_ai=request.use_insights,
                proposal_tone=proposal_tone,
                ai_response_style=ai_response_style,
                secure_mode=secure_mode
            )
        
        if existing_proposal:
            # Update existing proposal with new AI-generated content
            existing_proposal.sections = sections
            existing_proposal.template_type = request.template_type
            existing_proposal.title = f"{project.client_name} - Proposal"
            existing_proposal.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_proposal)
            return existing_proposal
        else:
            # Create new proposal
            new_proposal = Proposal(
                project_id=request.project_id,
                title=f"{project.client_name} - Proposal",
                sections=sections,
                template_type=request.template_type
            )
            
            db.add(new_proposal)
            db.commit()
            db.refresh(new_proposal)
            
            return new_proposal
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate proposal: {str(e)}"
        )

@router.post("/save-draft", response_model=ProposalResponse)
async def save_draft(
    request: ProposalSaveDraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save proposal draft (autosave functionality).
    """
    try:
        proposal = db.query(Proposal).filter(Proposal.id == request.proposal_id).first()
        
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Verify project ownership
        project = db.query(Project).filter(
            Project.id == proposal.project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update sections
        proposal.sections = request.sections
        
        if request.title:
            proposal.title = request.title
        
        proposal.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(proposal)
        
        return proposal
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save draft: {str(e)}"
        )

@router.post("/regenerate-section", response_model=Dict[str, Any])
async def regenerate_section(
    request: RegenerateSectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Regenerate a specific section's content using AI based on insights.
    """
    # Get proposal
    proposal = db.query(Proposal).filter(Proposal.id == request.proposal_id).first()
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == proposal.project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get insights
    insights = db.query(Insights).filter(
        Insights.project_id == proposal.project_id
    ).first()
    
    if not insights:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insights not found. Please run the workflow first."
        )
    
    # Get matching case studies
    matching_case_studies = []
    if hasattr(insights, 'matching_case_studies') and insights.matching_case_studies:
        matching_case_studies = insights.matching_case_studies
    else:
        from models.case_study import CaseStudy
        all_case_studies = db.query(CaseStudy).limit(5).all()
        matching_case_studies = [
            {
                "id": cs.id,
                "title": cs.title,
                "industry": cs.industry,
                "impact": cs.impact,
                "description": cs.description
            }
            for cs in all_case_studies
        ]
    
    # Generate new content for the section
    try:
        from services.proposal_templates import ProposalTemplates
        
        insights_dict = {
            "rfp_summary": insights.executive_summary or "",
            "challenges": insights.challenges or [],
            "value_propositions": insights.value_propositions or [],
            "matching_case_studies": matching_case_studies
        }
        
        new_content = ProposalTemplates._generate_section_content_ai(
            section_title=request.section_title,
            rfp_summary=insights_dict["rfp_summary"],
            challenges=insights_dict["challenges"],
            value_propositions=insights_dict["value_propositions"],
            case_studies=insights_dict["matching_case_studies"]
        )
        
        # Update the section in the proposal
        sections = proposal.sections or []
        updated_sections = []
        section_found = False
        
        for section in sections:
            section_id = section.get("id") if isinstance(section, dict) else None
            if section_id == request.section_id:
                # Update this section
                updated_section = section.copy() if isinstance(section, dict) else {"id": request.section_id, "title": request.section_title}
                updated_section["content"] = new_content
                updated_sections.append(updated_section)
                section_found = True
            else:
                updated_sections.append(section)
        
        if not section_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found in proposal"
            )
        
        # Save updated sections
        proposal.sections = updated_sections
        proposal.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(proposal)
        
        return {
            "success": True,
            "section_id": request.section_id,
            "content": new_content,
            "message": "Section regenerated successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error regenerating section: {str(e)}"
        )

@router.get("/{proposal_id}/preview", response_model=ProposalPreviewResponse)
async def preview_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get proposal preview with metadata.
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == proposal.project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Calculate word count
    word_count = 0
    sections = proposal.sections or []
    for section in sections:
        content = section.get('content', '') if isinstance(section, dict) else ''
        word_count += len(content.split())
    
    return ProposalPreviewResponse(
        proposal_id=proposal.id,
        title=proposal.title,
        sections=sections,
        template_type=proposal.template_type,
        word_count=word_count,
        section_count=len(sections)
    )

@router.get("/export/{proposal_id}/pdf")
async def export_pdf(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export proposal as PDF."""
    try:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Verify project ownership
        project = db.query(Project).filter(
            Project.id == proposal.project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Export to PDF
        buffer = proposal_exporter.export_pdf(
            title=proposal.title,
            sections=proposal.sections or [],
            project_name=project.name,
            client_name=project.client_name
        )
        
        # Save export
        file_path = proposal_exporter.save_export(buffer, "pdf", proposal_id)
        
        # Update metadata
        proposal.last_exported_at = datetime.utcnow()
        proposal.export_format = "pdf"
        db.commit()
        
        return FileResponse(
            file_path,
            media_type="application/pdf",
            filename=f"{proposal.title.replace(' ', '_')}.pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting PDF: {str(e)}"
        )

@router.get("/export/{proposal_id}/docx")
async def export_docx(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export proposal as DOCX."""
    try:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Verify project ownership
        project = db.query(Project).filter(
            Project.id == proposal.project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Export to DOCX
        buffer = proposal_exporter.export_docx(
            title=proposal.title,
            sections=proposal.sections or [],
            project_name=project.name,
            client_name=project.client_name
        )
        
        # Save export
        file_path = proposal_exporter.save_export(buffer, "docx", proposal_id)
        
        # Update metadata
        proposal.last_exported_at = datetime.utcnow()
        proposal.export_format = "docx"
        db.commit()
        
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"{proposal.title.replace(' ', '_')}.docx"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting DOCX: {str(e)}"
        )

@router.get("/export/{proposal_id}/pptx")
async def export_pptx(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export proposal as PowerPoint."""
    try:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Verify project ownership
        project = db.query(Project).filter(
            Project.id == proposal.project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Export to PPTX
        buffer = proposal_exporter.export_pptx(
            title=proposal.title,
            sections=proposal.sections or [],
            project_name=project.name,
            client_name=project.client_name
        )
        
        # Save export
        file_path = proposal_exporter.save_export(buffer, "pptx", proposal_id)
        
        # Update metadata
        proposal.last_exported_at = datetime.utcnow()
        proposal.export_format = "pptx"
        db.commit()
        
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=f"{proposal.title.replace(' ', '_')}.pptx"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export proposal: {str(e)}"
        )


@router.post("/{proposal_id}/submit", response_model=ProposalResponse)
async def submit_proposal(
    proposal_id: int,
    request: ProposalSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a proposal for approval."""
    try:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Verify ownership
        project = db.query(Project).filter(
            Project.id == proposal.project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check current status - prevent resubmission if already submitted
        if proposal.status == "pending_approval":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Proposal is already pending approval"
            )
            
        # Update status
        proposal.status = "pending_approval"
        proposal.submitter_message = request.message
        proposal.submitted_at = datetime.utcnow()
        
        # Create notification and send email to selected manager or all managers
        MANAGER_ROLE = "pre_sales_manager"
        
        # Import email service
        from utils.email_service import send_proposal_submission_email
        
        if request.manager_id:
            # Send to specific manager
            manager = db.query(User).filter(
                User.id == request.manager_id,
                User.role == MANAGER_ROLE,
                User.is_active == True
            ).first()
            
            if not manager:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Selected manager not found or inactive"
                )
            
            # Create in-app notification
            notification = Notification(
                user_id=manager.id,
                type="info",
                title="New Proposal Submitted",
                message=f"Proposal '{proposal.title}' submitted by {current_user.full_name}",
                metadata_={"proposal_id": proposal.id, "project_id": project.id, "submitter_id": current_user.id}
            )
            db.add(notification)
            
            # Send email notification (non-blocking)
            try:
                await send_proposal_submission_email(
                    manager_email=manager.email,
                    manager_name=manager.full_name,
                    proposal_title=proposal.title,
                    submitter_name=current_user.full_name,
                    submitter_message=request.message,
                    proposal_id=proposal.id,
                    project_id=project.id
                )
            except Exception as e:
                print(f"[WARNING] Failed to send email to manager {manager.email}: {e}")
        else:
            # Send to all managers (backward compatibility)
            managers = db.query(User).filter(
                User.role == MANAGER_ROLE,
                User.is_active == True,
                User.email_verified == True
            ).all()
            
            for manager in managers:
                # Create in-app notification
                notification = Notification(
                    user_id=manager.id,
                    type="info",
                    title="New Proposal Submitted",
                    message=f"Proposal '{proposal.title}' submitted by {current_user.full_name}",
                    metadata_={"proposal_id": proposal.id, "project_id": project.id, "submitter_id": current_user.id}
                )
                db.add(notification)
                
                # Send email notification (non-blocking)
                try:
                    await send_proposal_submission_email(
                        manager_email=manager.email,
                        manager_name=manager.full_name,
                        proposal_title=proposal.title,
                        submitter_name=current_user.full_name,
                        submitter_message=request.message,
                        proposal_id=proposal.id,
                        project_id=project.id
                    )
                except Exception as e:
                    print(f"[WARNING] Failed to send email to manager {manager.email}: {e}")
        
        db.commit()
        db.refresh(proposal)
        return proposal
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit proposal: {str(e)}"
        )

@router.post("/{proposal_id}/review", response_model=ProposalResponse)
async def review_proposal(
    proposal_id: int,
    request: ProposalReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Review a proposal (Approve/Reject/Hold). Only for managers."""
    MANAGER_ROLE = "pre_sales_manager"
    
    if current_user.role != MANAGER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Pre-Sales Managers can review proposals"
        )
    
    try:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Validate action
        ALLOWED_ACTIONS = ["approve", "reject", "hold"]
        if request.action not in ALLOWED_ACTIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action. Allowed actions: {', '.join(ALLOWED_ACTIONS)}"
            )
        
        # Check if proposal is in a reviewable state
        if proposal.status != "pending_approval":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Proposal is not pending approval. Current status: {proposal.status}"
            )
        
        # Update status
        if request.action == "approve":
            proposal.status = "approved"
        elif request.action == "reject":
            proposal.status = "rejected"
        elif request.action == "hold":
            proposal.status = "on_hold"
        
        proposal.admin_feedback = request.feedback
        proposal.reviewed_at = datetime.utcnow()
        proposal.reviewed_by = current_user.id
        
        # Notify the submitter
        project = db.query(Project).filter(Project.id == proposal.project_id).first()
        if project:
            notification = Notification(
                user_id=project.owner_id,
                type="success" if request.action == "approve" else "warning",
                title=f"Proposal {request.action.capitalize()}d",
                message=f"Your proposal '{proposal.title}' has been {request.action}ed. Feedback: {request.feedback or 'None'}",
                metadata_={"proposal_id": proposal.id}
            )
            db.add(notification)
        
        db.commit()
        db.refresh(proposal)
        return proposal
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review proposal: {str(e)}"
        )

@router.get("/admin/dashboard", response_model=List[ProposalResponse])
async def admin_dashboard(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get proposals for admin dashboard."""
    MANAGER_ROLE = "pre_sales_manager"
    ALLOWED_STATUSES = ["draft", "pending_approval", "approved", "rejected", "on_hold"]
    
    if current_user.role != MANAGER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    query = db.query(Proposal)
    
    if status:
        if status not in ALLOWED_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Allowed statuses: {', '.join(ALLOWED_STATUSES)}"
            )
        query = query.filter(Proposal.status == status)
    
    # Order by submitted_at desc (nulls last)
    from sqlalchemy import desc
    proposals = query.order_by(desc(Proposal.submitted_at).nullslast()).all()
    return proposals

@router.get("/admin/analytics")
async def admin_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analytics for admin dashboard."""
    MANAGER_ROLE = "pre_sales_manager"
    
    if current_user.role != MANAGER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    from sqlalchemy import func, case
    from models.project import Project
    from models.insights import Insights
    
    # Proposal statistics
    total_proposals = db.query(func.count(Proposal.id)).scalar() or 0
    pending_proposals = db.query(func.count(Proposal.id)).filter(Proposal.status == "pending_approval").scalar() or 0
    approved_proposals = db.query(func.count(Proposal.id)).filter(Proposal.status == "approved").scalar() or 0
    rejected_proposals = db.query(func.count(Proposal.id)).filter(Proposal.status == "rejected").scalar() or 0
    on_hold_proposals = db.query(func.count(Proposal.id)).filter(Proposal.status == "on_hold").scalar() or 0
    
    # Project statistics
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    active_projects = db.query(func.count(Project.id)).filter(Project.status.in_(["Active", "Submitted"])).scalar() or 0
    
    # User statistics
    total_analysts = db.query(func.count(User.id)).filter(User.role == "pre_sales_analyst", User.is_active == True).scalar() or 0
    total_managers = db.query(func.count(User.id)).filter(User.role == MANAGER_ROLE, User.is_active == True).scalar() or 0
    
    # Recent activity (last 7 days)
    from datetime import timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_submissions = db.query(func.count(Proposal.id)).filter(
        Proposal.submitted_at >= seven_days_ago
    ).scalar() or 0
    recent_approvals = db.query(func.count(Proposal.id)).filter(
        Proposal.reviewed_at >= seven_days_ago,
        Proposal.status == "approved"
    ).scalar() or 0
    
    # Approval rate
    reviewed_proposals = approved_proposals + rejected_proposals
    approval_rate = (approved_proposals / reviewed_proposals * 100) if reviewed_proposals > 0 else 0
    
    # Proposals by status (for chart)
    proposals_by_status = {
        "draft": db.query(func.count(Proposal.id)).filter(Proposal.status == "draft").scalar() or 0,
        "pending_approval": pending_proposals,
        "approved": approved_proposals,
        "rejected": rejected_proposals,
        "on_hold": on_hold_proposals,
    }
    
    return {
        "proposals": {
            "total": total_proposals,
            "pending": pending_proposals,
            "approved": approved_proposals,
            "rejected": rejected_proposals,
            "on_hold": on_hold_proposals,
            "by_status": proposals_by_status,
        },
        "projects": {
            "total": total_projects,
            "active": active_projects,
        },
        "users": {
            "analysts": total_analysts,
            "managers": total_managers,
            "total": total_analysts + total_managers,
        },
        "activity": {
            "recent_submissions": recent_submissions,
            "recent_approvals": recent_approvals,
            "approval_rate": round(approval_rate, 2),
        }
    }

