"""
Multi-agent workflow API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import User
from models.project import Project
from models.rfp_document import RFPDocument
from api.schemas.workflow import (
    RunWorkflowRequest,
    RunWorkflowResponse,
    GetStateRequest,
    GetStateResponse
)
from utils.dependencies import get_current_user
from workflows.workflow_manager import workflow_manager

router = APIRouter()

@router.post("/run-all", response_model=RunWorkflowResponse)
async def run_all_agents(
    request: RunWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run the complete multi-agent workflow.
    Executes all agents in sequence:
    1. RFP Analyzer
    2. Challenge Extractor
    3. Discovery Question Agent
    4. Value Proposition Agent
    5. Case Study Matcher
    6. Proposal Builder
    """
    import sys
    import traceback
    
    try:
        # Force immediate output
        sys.stdout.flush()
        sys.stderr.flush()
        
        print("\n" + "="*60, file=sys.stderr, flush=True)
        print("🔥 ENDPOINT CALLED: /agents/run-all", file=sys.stderr, flush=True)
        print("="*60, file=sys.stderr, flush=True)
        
        print(f"\n{'='*60}", flush=True)
        print(f"RUNNING AGENTS WORKFLOW", flush=True)
        print(f"Project ID: {request.project_id}", flush=True)
        print(f"RFP Document ID: {request.rfp_document_id}", flush=True)
        print(f"User ID: {current_user.id}", flush=True)
        print(f"User Email: {current_user.email}", flush=True)
        print(f"{'='*60}\n", flush=True)
    except Exception as e:
        print(f"ERROR in initial logging: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
    
    # Verify project ownership
    print(f"Checking project ownership: project_id={request.project_id}, user_id={current_user.id}")
    project = db.query(Project).filter(
        Project.id == request.project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        # Check if project exists but belongs to different user
        project_exists = db.query(Project).filter(
            Project.id == request.project_id
        ).first()
        
        if project_exists:
            print(f"❌ Project {request.project_id} exists but belongs to user {project_exists.owner_id}, not {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Project {request.project_id} does not belong to user {current_user.id}"
            )
        else:
            print(f"❌ Project {request.project_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {request.project_id}"
            )
    
    print(f"✓ Project {request.project_id} ownership verified")
    
    # Verify RFP document belongs to project
    print(f"Checking RFP document: rfp_document_id={request.rfp_document_id}, project_id={request.project_id}")
    rfp_doc = db.query(RFPDocument).filter(
        RFPDocument.id == request.rfp_document_id,
        RFPDocument.project_id == request.project_id
    ).first()
    
    if not rfp_doc:
        # Check if RFP document exists but belongs to different project
        rfp_exists = db.query(RFPDocument).filter(
            RFPDocument.id == request.rfp_document_id
        ).first()
        
        if rfp_exists:
            print(f"❌ RFP document {request.rfp_document_id} exists but belongs to project {rfp_exists.project_id}, not {request.project_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: RFP document {request.rfp_document_id} belongs to project {rfp_exists.project_id}, not {request.project_id}"
            )
        else:
            print(f"❌ RFP document {request.rfp_document_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RFP document not found: {request.rfp_document_id}"
            )
    
    print(f"✓ RFP document {request.rfp_document_id} verified")
    
    # Run workflow
    print(f"🚀 Starting workflow execution...")
    selected_tasks = request.selected_tasks or {
        "challenges": True,
        "questions": True,
        "cases": True,
        "proposal": True
    }
    print(f"Selected tasks: {selected_tasks}")
    result = workflow_manager.run_workflow(
        project_id=request.project_id,
        rfp_document_id=request.rfp_document_id,
        db=db,
        selected_tasks=selected_tasks
    )
    
    if not result.get("success"):
        print(f"❌ Workflow failed: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {result.get('error')}"
        )
    
    print(f"✓ Workflow completed successfully")
    return RunWorkflowResponse(**result)

@router.post("/get-state", response_model=GetStateResponse)
async def get_workflow_state(
    request: GetStateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Get workflow state by state_id.
    Useful for debugging and monitoring workflow execution.
    """
    state = workflow_manager.get_state(request.state_id)
    
    if not state:
        return GetStateResponse(
            success=False,
            error="State not found. It may have expired or never existed."
        )
    
    return GetStateResponse(
        success=True,
        state=state
    )

@router.get("/status")
async def get_workflow_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get workflow status for a project.
    Returns current step and progress information.
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
    
    # Get workflow state from manager
    state = workflow_manager.get_state_by_project(project_id)
    
    if not state:
        # Check if insights exist (workflow completed)
        from models.insights import Insights
        insights = db.query(Insights).filter(Insights.project_id == project_id).first()
        if insights:
            return {
                "status": "completed",
                "current_step": "completed",
                "progress": {
                    "rfp_analyzer": True,
                    "challenge_extractor": insights.challenges is not None,
                    "value_proposition": insights.value_propositions is not None,
                    "discovery_question": insights.discovery_questions is not None,
                    "case_study_matcher": insights.matching_case_studies is not None,
                    "proposal_builder": insights.proposal_draft is not None,
                }
            }
        return {
            "status": "not_started",
            "current_step": None,
            "progress": {}
        }
    
    # Determine progress based on state
    progress = {
        "rfp_analyzer": state.get("rfp_summary") is not None,
        "challenge_extractor": state.get("challenges") is not None,
        "value_proposition": state.get("value_propositions") is not None,
        "discovery_question": state.get("discovery_questions") is not None,
        "case_study_matcher": state.get("matching_case_studies") is not None,
        "proposal_builder": state.get("proposal_draft") is not None,
    }
    
    return {
        "status": "running",
        "current_step": state.get("current_step", "start"),
        "progress": progress,
        "execution_log": state.get("execution_log", [])
    }

@router.get("/debug")
async def debug_workflow(
    state_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Debug endpoint to inspect workflow state.
    Returns detailed state information including errors and execution log.
    """
    state = workflow_manager.get_state(state_id)
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="State not found"
        )
    
    return {
        "state_id": state_id,
        "current_step": state.get("current_step"),
        "errors": state.get("errors", []),
        "warnings": state.get("warnings", []),
        "execution_log": state.get("execution_log", []),
        "has_rfp_summary": state.get("rfp_summary") is not None,
        "has_challenges": state.get("challenges") is not None,
        "has_discovery_questions": state.get("discovery_questions") is not None,
        "has_value_propositions": state.get("value_propositions") is not None,
        "has_case_studies": state.get("matching_case_studies") is not None,
        "has_proposal": state.get("proposal_draft") is not None,
        "full_state": state
    }

