from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from db.database import get_db
from models.user import User
from models.case_study import CaseStudy
from api.schemas.case_study import CaseStudyCreate, CaseStudyUpdate, CaseStudyResponse
from utils.dependencies import get_current_user
from services.case_study_trainer import case_study_trainer

router = APIRouter()

@router.get("", response_model=List[CaseStudyResponse])
async def list_case_studies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    industry: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """List all case studies globally (visible to all users), optionally filtered by industry."""
    from sqlalchemy.orm import joinedload
    query = db.query(CaseStudy).options(joinedload(CaseStudy.creator))
    
    if industry:
        query = query.filter(CaseStudy.industry == industry)
    
    case_studies = query.offset(skip).limit(limit).all()
    # Convert to response format with creator name
    result = []
    for cs in case_studies:
        cs_dict = {
            "id": cs.id,
            "user_id": cs.user_id,
            "title": cs.title,
            "industry": cs.industry,
            "impact": cs.impact,
            "description": cs.description,
            "project_description": cs.project_description,
            "created_at": cs.created_at,
            "updated_at": cs.updated_at,
            "creator_name": cs.creator.full_name if cs.creator else None
        }
        result.append(cs_dict)
    return result

@router.post("", response_model=CaseStudyResponse, status_code=status.HTTP_201_CREATED)
async def create_case_study(
    case_study_data: CaseStudyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new case study."""
    case_study_dict = case_study_data.model_dump()
    case_study_dict["user_id"] = current_user.id
    new_case_study = CaseStudy(**case_study_dict)
    
    db.add(new_case_study)
    db.commit()
    db.refresh(new_case_study)
    
    # Return with creator name
    return {
        "id": new_case_study.id,
        "user_id": new_case_study.user_id,
        "title": new_case_study.title,
        "industry": new_case_study.industry,
        "impact": new_case_study.impact,
        "description": new_case_study.description,
        "project_description": new_case_study.project_description,
        "created_at": new_case_study.created_at,
        "updated_at": new_case_study.updated_at,
        "creator_name": current_user.full_name
    }

@router.get("/{case_study_id}", response_model=CaseStudyResponse)
async def get_case_study(
    case_study_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific case study."""
    from sqlalchemy.orm import joinedload
    case_study = db.query(CaseStudy).options(joinedload(CaseStudy.creator)).filter(CaseStudy.id == case_study_id).first()
    
    if not case_study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case study not found"
        )
    
    return {
        "id": case_study.id,
        "user_id": case_study.user_id,
        "title": case_study.title,
        "industry": case_study.industry,
        "impact": case_study.impact,
        "description": case_study.description,
        "project_description": case_study.project_description,
        "created_at": case_study.created_at,
        "updated_at": case_study.updated_at,
        "creator_name": case_study.creator.full_name if case_study.creator else None
    }

@router.put("/{case_study_id}", response_model=CaseStudyResponse)
async def update_case_study(
    case_study_id: int,
    case_study_data: CaseStudyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a case study."""
    case_study = db.query(CaseStudy).filter(CaseStudy.id == case_study_id).first()
    
    if not case_study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case study not found"
        )
    
    # Update fields
    update_data = case_study_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case_study, field, value)
    
    db.commit()
    db.refresh(case_study)
    
    return case_study

@router.delete("/{case_study_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case_study(
    case_study_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a case study."""
    case_study = db.query(CaseStudy).filter(CaseStudy.id == case_study_id).first()
    
    if not case_study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case study not found"
        )
    
    db.delete(case_study)
    db.commit()
    
    return None

class SimilaritySearchRequest(BaseModel):
    query: str
    industry: Optional[str] = None
    top_k: int = 5

@router.post("/search-similar")
async def search_similar_case_studies(
    request: SimilaritySearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for similar case studies using RAG similarity search."""
    try:
        results = case_study_trainer.find_similar_case_studies(
            query=request.query,
            industry=request.industry,
            top_k=request.top_k
        )
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching case studies: {str(e)}"
        )

