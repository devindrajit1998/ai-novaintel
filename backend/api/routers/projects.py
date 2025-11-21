from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.user import User
from models.project import Project
from api.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from utils.dependencies import get_current_user
from utils.websocket_manager import global_ws_manager

router = APIRouter()

@router.post("/create", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project.
    
    Required fields:
    - name: str
    - client_name: str
    - industry: str
    - region: str
    - project_type: "new" | "expansion" | "renewal"
    - description: str (optional)
    
    Example request:
    {
      "name": "Project Name",
      "client_name": "Client Name",
      "industry": "Healthcare",
      "region": "North America",
      "project_type": "new",
      "description": "Optional description"
    }
    """
    try:
        print(f"Creating project for user: {current_user.email} (ID: {current_user.id})")
        print(f"Project data received: {project_data.model_dump()}")
        
        new_project = Project(
            **project_data.model_dump(),
            owner_id=current_user.id
        )
        
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        # Broadcast project creation via WebSocket
        try:
            from utils.websocket_manager import global_ws_manager
            await global_ws_manager.broadcast({
                "type": "project_created",
                "project": {
                    "id": new_project.id,
                    "name": new_project.name,
                    "owner_id": new_project.owner_id,
                    "created_at": new_project.created_at.isoformat() if hasattr(new_project.created_at, 'isoformat') else str(new_project.created_at)
                }
            }, subscription_type="projects")
        except Exception as e:
            print(f"Error broadcasting project creation: {e}")
        
        print(f"✓ Project created: {new_project.id} - {new_project.name}")
        return new_project
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error creating project: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.get("/list", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List all projects for the current user."""
    projects = db.query(Project).filter(
        Project.owner_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a project."""
    try:
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Update fields
        update_data = project_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        db.commit()
        db.refresh(project)
        
        # Broadcast project update via WebSocket
        try:
            from utils.websocket_manager import global_ws_manager
            await global_ws_manager.broadcast({
                "type": "project_updated",
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "status": project.status,
                    "owner_id": project.owner_id,
                    "updated_at": project.updated_at.isoformat() if hasattr(project.updated_at, 'isoformat') else str(project.updated_at)
                }
            }, subscription_type="projects")
        except Exception as e:
            print(f"Error broadcasting project update: {e}")
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project."""
    try:
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        db.delete(project)
        db.commit()
        
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )

@router.post("/{project_id}/publish-case-study")
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
    from models.insights import Insights
    from models.case_study import CaseStudy
    from models.notification import Notification
    from utils.timezone import now_ist
    from services.case_study_trainer import CaseStudyTrainer
    
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
    from models.project import Project
    from models.insights import Insights
    from models.case_study import CaseStudy
    from models.notification import Notification
    from services.case_study_trainer import CaseStudyTrainer
    
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
            impact="See project details",  # Default impact
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
    from models.notification import Notification
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        notification.status = status
        notification.message = message
        if metadata:
            notification.metadata_ = {**(notification.metadata_ or {}), **metadata}
        db.commit()

@router.get("/admin/all", response_model=List[ProjectResponse])
async def get_all_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get all projects across all users. Only accessible to managers."""
    MANAGER_ROLE = "pre_sales_manager"
    if current_user.role != MANAGER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Manager role required."
        )
    
    projects = db.query(Project).offset(skip).limit(limit).all()
    return projects

@router.get("/admin/{project_id}", response_model=ProjectResponse)
async def admin_get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project for admin review (no ownership check)."""
    if current_user.role != "pre_sales_manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Manager role required."
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project

