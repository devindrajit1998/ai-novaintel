from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MessageCreate(BaseModel):
    conversation_id: int
    content: str


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_name: str
    sender_email: str
    content: str
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    participant_ids: List[int]  # List of user IDs to include in conversation
    name: Optional[str] = None  # For group chats


class ConversationResponse(BaseModel):
    id: int
    name: Optional[str]
    is_group: bool
    created_at: datetime
    updated_at: datetime
    participants: List[dict]
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int


class WebSocketMessage(BaseModel):
    type: str  # "message", "typing", "read_receipt", "user_joined", "user_left"
    conversation_id: int
    sender_id: Optional[int] = None
    content: Optional[str] = None
    message_id: Optional[int] = None
    timestamp: Optional[datetime] = None

