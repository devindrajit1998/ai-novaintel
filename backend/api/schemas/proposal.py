from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class ProposalSection(BaseModel):
    id: int
    title: str
    content: str
    order: Optional[int] = 0
    required: Optional[bool] = False

class ProposalCreate(BaseModel):
    project_id: int
    title: Optional[str] = "Proposal"
    sections: Optional[List[Dict]] = None
    template_type: Optional[str] = "full"

class ProposalUpdate(BaseModel):
    title: Optional[str] = None
    sections: Optional[List[Dict]] = None
    template_type: Optional[str] = None

class ProposalGenerateRequest(BaseModel):
    project_id: int
    template_type: Optional[str] = "full"
    use_insights: Optional[bool] = True
    selected_case_study_ids: Optional[List[int]] = None

class ProposalSaveDraftRequest(BaseModel):
    proposal_id: int
    sections: List[Dict]
    title: Optional[str] = None

class ProposalSubmitRequest(BaseModel):
    message: Optional[str] = None
    manager_id: Optional[int] = None  # Specific manager to send for approval

class ProposalReviewRequest(BaseModel):
    action: str  # approve, reject, hold
    feedback: Optional[str] = None

class ProposalResponse(BaseModel):
    id: int
    project_id: int
    title: str
    sections: Optional[List[Dict]]
    template_type: str
    last_exported_at: Optional[datetime]
    export_format: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Approval Workflow
    status: str
    submitter_message: Optional[str]
    admin_feedback: Optional[str]
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[int]
    
    class Config:
        from_attributes = True

class ProposalPreviewResponse(BaseModel):
    proposal_id: int
    title: str
    sections: List[Dict]
    template_type: str
    word_count: Optional[int] = None
    section_count: Optional[int] = None

class RegenerateSectionRequest(BaseModel):
    proposal_id: int
    section_id: int
    section_title: str

class AcceptRegenerationRequest(BaseModel):
    proposal_id: int
    section_id: Optional[int] = None  # If None, accept full proposal regeneration
    accept: bool = True  # True to accept new version, False to keep old
    new_content: Optional[str] = None  # New content for section regeneration (if section_id provided)
    new_sections: Optional[List[Dict]] = None  # New sections for full proposal regeneration

