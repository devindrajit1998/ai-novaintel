from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CaseStudyCreate(BaseModel):
    title: str
    industry: str
    impact: str
    description: Optional[str] = None

class CaseStudyUpdate(BaseModel):
    title: Optional[str] = None
    industry: Optional[str] = None
    impact: Optional[str] = None
    description: Optional[str] = None

class CaseStudyResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    title: str
    industry: str
    impact: str
    description: Optional[str] = None
    project_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    creator_name: Optional[str] = None  # Will be populated from relationship
    
    class Config:
        from_attributes = True

