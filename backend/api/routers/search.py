"""
Global search endpoint for searching across projects, case studies, and users.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List
from db.database import get_db
from models.user import User
from models.project import Project
from models.case_study import CaseStudy
from utils.dependencies import get_current_user

router = APIRouter()

@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=2, description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Global search across projects, case studies, and users.
    """
    search_term = f"%{q.lower()}%"
    results = []
    
    # Search projects (owned by current user)
    projects = db.query(Project).filter(
        Project.owner_id == current_user.id,
        or_(
            func.lower(Project.name).like(search_term),
            func.lower(Project.client_name).like(search_term),
            func.lower(Project.description).like(search_term),
            func.lower(Project.industry).like(search_term)
        )
    ).limit(5).all()
    
    for project in projects:
        results.append({
            "id": project.id,
            "type": "project",
            "title": project.name,
            "subtitle": project.client_name,
            "metadata": f"{project.industry} • {project.status}"
        })
    
    # Search case studies (globally visible)
    case_studies = db.query(CaseStudy).filter(
        or_(
            func.lower(CaseStudy.title).like(search_term),
            func.lower(CaseStudy.description).like(search_term),
            func.lower(CaseStudy.industry).like(search_term),
            func.lower(CaseStudy.impact).like(search_term)
        )
    ).limit(5).all()
    
    for case_study in case_studies:
        results.append({
            "id": case_study.id,
            "type": "case_study",
            "title": case_study.title,
            "subtitle": case_study.industry,
            "metadata": case_study.impact
        })
    
    return results

