from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.project import ProjectStatus, ProjectType

class ProjectCreate(BaseModel):
    name: str
    client_name: str
    industry: str
    region: str
    project_type: ProjectType
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    industry: Optional[str] = None
    region: Optional[str] = None
    project_type: Optional[ProjectType] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    client_name: str
    industry: str
    region: str
    project_type: ProjectType
    description: Optional[str]
    status: ProjectStatus
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

