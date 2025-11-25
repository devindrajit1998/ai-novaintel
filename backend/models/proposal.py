from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, String, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base
from utils.timezone import now_utc_from_ist

class Proposal(Base):
    __tablename__ = "proposals"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=False, default="Proposal")
    
    # Sections stored as JSON array of {id, title, content}
    sections = Column(JSON, nullable=True)
    
    # Template type
    template_type = Column(String, default="full")  # executive, full, one-page
    
    # Export metadata
    last_exported_at = Column(DateTime, nullable=True)
    export_format = Column(String, nullable=True)  # pdf, docx
    
    created_at = Column(DateTime, default=now_utc_from_ist)
    updated_at = Column(DateTime, default=now_utc_from_ist, onupdate=now_utc_from_ist)
    
    # Relationships
    project = relationship("Project", back_populates="proposals")

    # Approval Workflow
    status = Column(String, default="draft")  # draft, pending_approval, approved, rejected, on_hold
    submitter_message = Column(Text, nullable=True)
    admin_feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

