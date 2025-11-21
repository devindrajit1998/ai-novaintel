"""
Notification schemas.
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class NotificationCreate(BaseModel):
    type: str  # success, error, info, warning
    title: str
    message: str
    status: Optional[str] = "pending"
    metadata: Optional[Dict[str, Any]] = None

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    status: str
    is_read: bool
    read_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        # Allow access to both metadata and metadata_ attributes
        populate_by_name = True

