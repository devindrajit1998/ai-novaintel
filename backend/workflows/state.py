"""
State management for multi-agent workflow.
"""
from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
import operator

class WorkflowState(TypedDict):
    """Global state for the presales workflow."""
    
    # Input
    project_id: int
    rfp_document_id: int
    rfp_text: Optional[str]
    retrieved_context: Optional[str]
    selected_tasks: Optional[Dict[str, bool]]  # {challenges: bool, questions: bool, cases: bool, proposal: bool}
    
    # RFP Analyzer Output
    rfp_summary: Optional[str]
    context_overview: Optional[str]
    business_objectives: Optional[List[str]]
    project_scope: Optional[str]
    
    # Challenge Extractor Output
    challenges: Optional[List[Dict[str, Any]]]
    
    # Discovery Question Output
    discovery_questions: Optional[Dict[str, List[str]]]
    
    # Value Proposition Output
    value_propositions: Optional[List[str]]
    
    # Case Study Matcher Output
    matching_case_studies: Optional[List[Dict[str, Any]]]
    
    # Proposal Builder Output
    proposal_draft: Optional[Dict[str, Any]]
    
    # Metadata
    current_step: str
    errors: Annotated[List[str], operator.add]
    warnings: Annotated[List[str], operator.add]
    execution_log: Annotated[List[Dict[str, Any]], operator.add]

def create_initial_state(
    project_id: int,
    rfp_document_id: int,
    rfp_text: Optional[str] = None,
    retrieved_context: Optional[str] = None,
    selected_tasks: Optional[Dict[str, bool]] = None
) -> WorkflowState:
    """Create initial workflow state."""
    # Default to all tasks enabled if not specified
    if selected_tasks is None:
        selected_tasks = {
            "challenges": True,
            "questions": True,
            "cases": True,
            "proposal": True
        }
    
    return {
        "project_id": project_id,
        "rfp_document_id": rfp_document_id,
        "rfp_text": rfp_text,
        "retrieved_context": retrieved_context,
        "selected_tasks": selected_tasks,
        "rfp_summary": None,
        "context_overview": None,
        "business_objectives": None,
        "project_scope": None,
        "challenges": None,
        "discovery_questions": None,
        "value_propositions": None,
        "matching_case_studies": None,
        "proposal_draft": None,
        "current_step": "start",
        "errors": [],
        "warnings": [],
        "execution_log": []
    }

