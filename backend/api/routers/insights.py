from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from models.user import User
from models.project import Project
from models.insights import Insights
from api.schemas.insights import InsightsResponse
from utils.dependencies import get_current_user

router = APIRouter()

class InsightsStatusResponse(BaseModel):
    exists: bool
    project_id: int
    message: str

@router.get("/get", response_model=InsightsResponse)
async def get_insights(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get insights for a project.
    Returns 404 if insights haven't been generated yet.
    Run /agents/run-all first to generate insights.
    """
    try:
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
        
        # Get insights
        insights = db.query(Insights).filter(Insights.project_id == project_id).first()
        
        if not insights:
            # Check if workflow has been run (check for RFP document)
            from models.rfp_document import RFPDocument
            rfp_doc = db.query(RFPDocument).filter(RFPDocument.project_id == project_id).first()
            
            if rfp_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insights not found for this project. Please run the agents workflow first using POST /agents/run-all with project_id and rfp_document_id"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insights not found. Please upload an RFP document first, then run the agents workflow using POST /agents/run-all"
                )
        
        # Convert Insights model to response - ensure proper serialization
        try:
            # Replace company name placeholders in proposal_draft before returning
            from utils.proposal_utils import replace_placeholders_in_proposal_draft
            company_name = current_user.company_name
            if company_name and insights.proposal_draft:
                insights.proposal_draft = replace_placeholders_in_proposal_draft(
                    insights.proposal_draft, 
                    company_name
                )
            
            # Use Pydantic model for proper serialization
            response_data = InsightsResponse.model_validate(insights)
            return response_data
        except Exception as serialization_error:
            import traceback
            print(f"Error serializing insights: {serialization_error}")
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error serializing insights: {str(serialization_error)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error fetching insights: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching insights: {str(e)}"
        )

@router.get("/status", response_model=InsightsStatusResponse)
async def check_insights_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if insights exist for a project.
    Returns status without requiring insights to exist.
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
    
    # Check if insights exist
    insights = db.query(Insights).filter(Insights.project_id == project_id).first()
    
    if insights:
        return InsightsStatusResponse(
            exists=True,
            project_id=project_id,
            message="Insights are available. Use /insights/get to retrieve them."
        )
    else:
        return InsightsStatusResponse(
            exists=False,
            project_id=project_id,
            message="Insights not generated yet. Run /agents/run-all to generate insights."
        )

