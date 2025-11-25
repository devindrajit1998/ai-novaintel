from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from utils.timezone import now_utc_from_ist, now_ist
import sys
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
    AcceptRegenerationRequest,
    ProposalSubmitRequest,
    ProposalReviewRequest
)
from models.notification import Notification
from utils.dependencies import get_current_user
from services.proposal_templates import ProposalTemplates
from services.proposal_export import proposal_exporter
from utils.websocket_manager import global_ws_manager

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
    
    # Replace company name placeholders in proposal sections before returning
    from utils.proposal_utils import replace_company_placeholders
    company_name = current_user.company_name
    if company_name and proposal.sections:
        for section in proposal.sections:
            if isinstance(section, dict) and section.get("content"):
                section["content"] = replace_company_placeholders(section["content"], company_name)
    
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
    
    # Replace company name placeholders in proposal sections before returning
    from utils.proposal_utils import replace_company_placeholders
    company_name = current_user.company_name
    if company_name and proposal.sections:
        for section in proposal.sections:
            if isinstance(section, dict) and section.get("content"):
                section["content"] = replace_company_placeholders(section["content"], company_name)
    
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

@router.post("/generate", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
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
            
            # Replace company name placeholders in sections
            from utils.proposal_utils import replace_company_placeholders
            company_name = current_user.company_name
            if company_name and sections:
                for section in sections:
                    if isinstance(section, dict) and section.get("content"):
                        section["content"] = replace_company_placeholders(section["content"], company_name)
        
        # Store old sections if regenerating
        old_sections = existing_proposal.sections if existing_proposal else []
        if old_sections is None:
            old_sections = []
        
        if existing_proposal:
            # Don't save yet - return both old and new for comparison
            # The frontend will call accept-regeneration to save
            return {
                "id": existing_proposal.id,
                "project_id": existing_proposal.project_id,
                "title": f"{project.client_name} - Proposal",
                "sections": sections,
                "template_type": request.template_type,
                "old_sections": old_sections,
                "is_regeneration": True,
                "status": existing_proposal.status,
                "created_at": existing_proposal.created_at.isoformat() if existing_proposal.created_at else None,
                "updated_at": existing_proposal.updated_at.isoformat() if existing_proposal.updated_at else None
            }
        else:
            # Create new proposal (no comparison needed for new proposals)
            new_proposal = Proposal(
                project_id=request.project_id,
                title=f"{project.client_name} - Proposal",
                sections=sections,
                template_type=request.template_type
            )
            
            db.add(new_proposal)
            db.commit()
            db.refresh(new_proposal)
            
            # Convert to dict for consistency with regeneration response
            proposal_dict = ProposalResponse.model_validate(new_proposal).model_dump()
            return proposal_dict
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
        
        proposal.updated_at = now_utc_from_ist()
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
        
        # Replace company name placeholders in new content
        from utils.proposal_utils import replace_company_placeholders
        company_name = current_user.company_name
        if company_name:
            new_content = replace_company_placeholders(new_content, company_name)
        
        # Get old content before updating
        sections = proposal.sections or []
        old_content = None
        section_found = False
        
        for section in sections:
            section_id = section.get("id") if isinstance(section, dict) else None
            if section_id == request.section_id:
                old_content = section.get("content", "") if isinstance(section, dict) else ""
                section_found = True
                break
        
        if not section_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found in proposal"
            )
        
        # Return both old and new content for comparison (don't save yet)
        return {
            "success": True,
            "section_id": request.section_id,
            "section_title": request.section_title,
            "old_content": old_content,
            "new_content": new_content,
            "message": "Section regenerated successfully. Please review and accept to save."
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error regenerating section: {str(e)}"
        )

@router.post("/accept-regeneration", response_model=Dict[str, Any])
async def accept_regeneration(
    request: AcceptRegenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accept or reject a regenerated proposal/section.
    If accept=True, saves the new version. If accept=False, keeps the old version.
    For section regeneration, the new_content should be passed in the request body.
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
        
        if request.accept:
            # Accept new version
            if request.section_id and request.new_content:
                # Section regeneration - update specific section with new content
                sections = proposal.sections or []
                updated_sections = []
                for section in sections:
                    if isinstance(section, dict) and section.get("id") == request.section_id:
                        # Update with new content
                        updated_section = section.copy()
                        updated_section["content"] = request.new_content
                        updated_sections.append(updated_section)
                    else:
                        updated_sections.append(section)
                proposal.sections = updated_sections
            elif request.new_sections:
                # Full proposal regeneration - update all sections
                proposal.sections = request.new_sections
            proposal.updated_at = now_utc_from_ist()
            db.commit()
            db.refresh(proposal)
            # Convert proposal to dict for serialization
            proposal_dict = ProposalResponse.model_validate(proposal).model_dump()
            return {
                "success": True,
                "message": "Regeneration accepted and saved",
                "proposal": proposal_dict
            }
        else:
            # Reject new version - keep old version (proposal is already unchanged)
            db.refresh(proposal)
            # Convert proposal to dict for serialization
            proposal_dict = ProposalResponse.model_validate(proposal).model_dump()
            return {
                "success": True,
                "message": "Regeneration rejected, keeping original version",
                "proposal": proposal_dict
            }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accepting regeneration: {str(e)}"
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
            client_name=project.client_name,
            company_name=current_user.company_name
        )
        
        # Save export
        file_path = proposal_exporter.save_export(buffer, "pdf", proposal_id)
        
        # Update metadata
        proposal.last_exported_at = now_utc_from_ist()
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
            client_name=project.client_name,
            company_name=current_user.company_name
        )
        
        # Save export
        file_path = proposal_exporter.save_export(buffer, "docx", proposal_id)
        
        # Update metadata
        proposal.last_exported_at = now_utc_from_ist()
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
            client_name=project.client_name,
            company_name=current_user.company_name
        )
        
        # Save export
        file_path = proposal_exporter.save_export(buffer, "pptx", proposal_id)
        
        # Update metadata
        proposal.last_exported_at = now_utc_from_ist()
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
        proposal.submitted_at = now_utc_from_ist()
        
        # Always send email to all admins (pre_sales_manager role)
        ADMIN_ROLE = "pre_sales_manager"
        
        # Import email service
        from utils.email_service import send_proposal_submission_email
        
        # Get all active admins with verified emails
        admins = db.query(User).filter(
            User.role == ADMIN_ROLE,
            User.is_active == True,
            User.email_verified == True
        ).all()
        
        if not admins:
            print(f"[WARNING] No active admins with verified emails found. Email notifications will not be sent for proposal {proposal.id}")
        
        # Prepare proposal data for email
        proposal_sections = proposal.sections if proposal.sections else []
        from utils.timezone import format_ist
        submitted_at_str = format_ist(proposal.submitted_at, "%Y-%m-%d %H:%M:%S IST") if proposal.submitted_at else None
        
        # Send email and create notification for all admins
        for admin in admins:
            # Create in-app notification
            notification = Notification(
                user_id=admin.id,
                type="info",
                title="New Proposal Submitted",
                message=f"Proposal '{proposal.title}' submitted by {current_user.full_name}",
                metadata_={"proposal_id": proposal.id, "project_id": project.id, "submitter_id": current_user.id}
            )
            db.add(notification)
            
            # Send email notification with all proposal data (non-blocking)
            import sys
            try:
                await send_proposal_submission_email(
                    manager_email=admin.email,
                    manager_name=admin.full_name,
                    proposal_title=proposal.title,
                    submitter_name=current_user.full_name,
                    submitter_message=request.message,
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
        
        # If a specific manager_id was provided, also send notification to that manager
        # (in addition to all admins, if not already included)
        if request.manager_id:
            specific_manager = db.query(User).filter(
                User.id == request.manager_id,
                User.role == ADMIN_ROLE,
                User.is_active == True
            ).first()
            
            if specific_manager:
                # Check if this manager is already in the admins list (to avoid duplicate notifications)
                admin_ids = [admin.id for admin in admins]
                if specific_manager.id not in admin_ids:
                    # Create additional notification for specific manager if not already an admin
                    notification = Notification(
                        user_id=specific_manager.id,
                        type="info",
                        title="New Proposal Submitted",
                        message=f"Proposal '{proposal.title}' submitted by {current_user.full_name}",
                        metadata_={"proposal_id": proposal.id, "project_id": project.id, "submitter_id": current_user.id}
                    )
                    db.add(notification)
        
        db.commit()
        db.refresh(proposal)
        
        # Broadcast proposal submission via WebSocket
        try:
            await global_ws_manager.broadcast({
                "type": "proposal_submitted",
                "proposal": {
                    "id": proposal.id,
                    "project_id": proposal.project_id,
                    "title": proposal.title,
                    "status": proposal.status,
                    "submitted_at": proposal.submitted_at.isoformat() if proposal.submitted_at else None,
                    "submitter_id": current_user.id
                }
            }, subscription_type="proposals")
        except Exception as e:
            print(f"Error broadcasting proposal submission: {e}")
        
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
        
        # Check if proposal is in a reviewable state (can review pending_approval or on_hold proposals)
        if proposal.status not in ["pending_approval", "on_hold"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Proposal cannot be reviewed from current status: {proposal.status}. Only pending_approval or on_hold proposals can be reviewed."
            )
        
        # Update status
        if request.action == "approve":
            proposal.status = "approved"
        elif request.action == "reject":
            proposal.status = "rejected"
        elif request.action == "hold":
            proposal.status = "on_hold"
        
        proposal.admin_feedback = request.feedback
        proposal.reviewed_at = now_utc_from_ist()
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
        
        # Broadcast proposal review via WebSocket
        try:
            await global_ws_manager.broadcast({
                "type": "proposal_reviewed",
                "proposal": {
                    "id": proposal.id,
                    "project_id": proposal.project_id,
                    "title": proposal.title,
                    "status": proposal.status,
                    "reviewed_at": proposal.reviewed_at.isoformat() if proposal.reviewed_at else None,
                    "reviewed_by": proposal.reviewed_by
                }
            }, subscription_type="proposals")
            
            # Also notify the proposal owner
            if project:
                await global_ws_manager.send_to_user(project.owner_id, {
                    "type": "proposal_reviewed",
                    "proposal": {
                        "id": proposal.id,
                        "title": proposal.title,
                        "status": proposal.status,
                        "action": request.action,
                        "feedback": request.feedback
                    }
                })
        except Exception as e:
            print(f"Error broadcasting proposal review: {e}")
        
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

@router.get("/admin/{proposal_id}", response_model=ProposalResponse)
async def admin_get_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific proposal for admin review (no ownership check)."""
    MANAGER_ROLE = "pre_sales_manager"
    
    if current_user.role != MANAGER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Manager role required."
        )
    
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    
    return proposal

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
    from datetime import date
    seven_days_ago = now_utc_from_ist() - timedelta(days=7)
    thirty_days_ago = now_utc_from_ist() - timedelta(days=30)
    recent_submissions = db.query(func.count(Proposal.id)).filter(
        Proposal.submitted_at >= seven_days_ago
    ).scalar() or 0
    recent_approvals = db.query(func.count(Proposal.id)).filter(
        Proposal.reviewed_at >= seven_days_ago
    ).filter(
        Proposal.status == "approved"
    ).scalar() or 0
    
    # Time-series data for last 30 days (daily)
    daily_submissions = []
    daily_approvals = []
    for i in range(30):
        day = now_utc_from_ist() - timedelta(days=30-i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        submissions_count = db.query(func.count(Proposal.id)).filter(
            Proposal.submitted_at >= day_start
        ).filter(
            Proposal.submitted_at <= day_end
        ).scalar() or 0
        
        approvals_count = db.query(func.count(Proposal.id)).filter(
            Proposal.reviewed_at >= day_start
        ).filter(
            Proposal.reviewed_at <= day_end
        ).filter(
            Proposal.status == "approved"
        ).scalar() or 0
        
        daily_submissions.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "label": day_start.strftime("%b %d"),
            "value": submissions_count
        })
        daily_approvals.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "label": day_start.strftime("%b %d"),
            "value": approvals_count
        })
    
    # Weekly data (last 4 weeks)
    weekly_data = []
    for i in range(4):
        week_start = now_utc_from_ist() - timedelta(days=28-i*7)
        week_end = week_start + timedelta(days=6)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_end.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        weekly_submissions = db.query(func.count(Proposal.id)).filter(
            Proposal.submitted_at >= week_start
        ).filter(
            Proposal.submitted_at <= week_end
        ).scalar() or 0
        
        weekly_approvals = db.query(func.count(Proposal.id)).filter(
            Proposal.reviewed_at >= week_start
        ).filter(
            Proposal.reviewed_at <= week_end
        ).filter(
            Proposal.status == "approved"
        ).scalar() or 0
        
        weekly_rejections = db.query(func.count(Proposal.id)).filter(
            Proposal.reviewed_at >= week_start
        ).filter(
            Proposal.reviewed_at <= week_end
        ).filter(
            Proposal.status == "rejected"
        ).scalar() or 0
        
        weekly_data.append({
            "week": f"Week {4-i}",
            "label": week_start.strftime("%b %d"),
            "submissions": weekly_submissions,
            "approvals": weekly_approvals,
            "rejections": weekly_rejections
        })
    
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
        },
        "time_series": {
            "daily_submissions": daily_submissions,
            "daily_approvals": daily_approvals,
            "weekly": weekly_data
        }
    }

