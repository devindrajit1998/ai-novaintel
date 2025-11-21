"""
Publish project as case study endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import User
from models.project import Project
from models.insights import Insights
from models.case_study import CaseStudy
from models.notification import Notification
from utils.dependencies import get_current_user
from utils.timezone import now_ist
from services.case_study_trainer import CaseStudyTrainer

router = APIRouter()

@router.post("/projects/{project_id}/publish-case-study")
async def publish_project_as_case_study(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Publish a project as a case study.
    This runs as a background job and sends a notification when complete.
    """
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
    
    # Check if project already published
    existing_case_study = db.query(CaseStudy).filter(
        CaseStudy.project_id == project_id
    ).first()
    
    if existing_case_study:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project already published as case study"
        )
    
    # Create initial notification
    notification = Notification(
        user_id=current_user.id,
        type="info",
        title="Publishing Project as Case Study",
        message=f"Publishing '{project.name}' as a case study. This may take a few moments...",
        status="processing",
        metadata={"project_id": project_id, "job_type": "publish_case_study"}
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    # Start background job
    background_tasks.add_task(
        _publish_project_background,
        project_id=project_id,
        user_id=current_user.id,
        notification_id=notification.id
    )
    
    return {
        "message": "Case study publication started",
        "notification_id": notification.id,
        "status": "processing"
    }

async def _publish_project_background(
    project_id: int,
    user_id: int,
    notification_id: int
):
    """Background task to publish project as case study."""
    from db.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get project and insights
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            _update_notification(db, notification_id, "failed", "Project not found")
            return
        
        insights = db.query(Insights).filter(Insights.project_id == project_id).first()
        
        # Extract case study data from project and insights
        case_study_data = {
            "title": f"{project.client_name} - {project.project_type}",
            "industry": project.industry,
            "description": project.description or "",
            "project_description": project.description or "",
            "user_id": user_id,
        }
        
        # Add insights data if available
        if insights:
            if insights.challenges:
                # Extract key challenges
                challenges_text = "\n".join([
                    ch.get("description", "") if isinstance(ch, dict) else str(ch)
                    for ch in (insights.challenges[:3] if isinstance(insights.challenges, list) else [])
                ])
                case_study_data["description"] += f"\n\nKey Challenges:\n{challenges_text}"
            
            if insights.value_propositions:
                value_props_text = "\n".join([
                    vp if isinstance(vp, str) else str(vp)
                    for vp in (insights.value_propositions[:3] if isinstance(insights.value_propositions, list) else [])
                ])
                case_study_data["description"] += f"\n\nValue Propositions:\n{value_props_text}"
            
            if insights.executive_summary:
                case_study_data["project_description"] = insights.executive_summary
        
        # Create case study
        case_study = CaseStudy(
            title=case_study_data["title"],
            industry=case_study_data["industry"],
            description=case_study_data["description"],
            project_description=case_study_data["project_description"],
            user_id=case_study_data["user_id"],
            project_id=project_id
        )
        
        db.add(case_study)
        db.commit()
        db.refresh(case_study)
        
        # Index in RAG
        try:
            trainer = CaseStudyTrainer()
            trainer._index_case_study_in_rag(case_study, db)
            case_study.indexed = True
            db.commit()
        except Exception as e:
            print(f"Warning: Failed to index case study in RAG: {e}")
        
        # Update notification
        _update_notification(
            db,
            notification_id,
            "completed",
            f"Successfully published '{project.name}' as a case study.",
            {"case_study_id": case_study.id}
        )
        
    except Exception as e:
        print(f"Error publishing project as case study: {e}")
        import traceback
        traceback.print_exc()
        _update_notification(
            db,
            notification_id,
            "failed",
            f"Failed to publish case study: {str(e)}"
        )
    finally:
        db.close()

def _update_notification(
    db: Session,
    notification_id: int,
    status: str,
    message: str,
    metadata: dict = None
):
    """Update notification status."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        notification.status = status
        notification.message = message
        if metadata:
            notification.metadata_ = {**(notification.metadata_ or {}), **metadata}
        db.commit()

