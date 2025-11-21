"""
Pydantic schemas for workflow endpoints.
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any

class RunWorkflowRequest(BaseModel):
    project_id: int
    rfp_document_id: int
    selected_tasks: Optional[Dict[str, bool]] = None  # {challenges: bool, questions: bool, cases: bool, proposal: bool}

class RunWorkflowResponse(BaseModel):
    success: bool
    state_id: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class GetStateRequest(BaseModel):
    state_id: str

class GetStateResponse(BaseModel):
    success: bool
    state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

