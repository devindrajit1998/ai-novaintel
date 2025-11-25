from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base
from utils.timezone import now_utc_from_ist
import enum

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"

class CaseStudyDocument(Base):
    __tablename__ = "case_study_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf or docx
    extracted_text = Column(Text, nullable=True)
    # Use String instead of SQLEnum to work with VARCHAR column
    processing_status = Column(String(20), default=ProcessingStatus.PENDING.value)
    error_message = Column(Text, nullable=True)
    document_metadata = Column(JSON, nullable=True)  # Store extracted metadata
    case_study_id = Column(Integer, ForeignKey("case_studies.id"), nullable=True)  # Link to created case study
    created_at = Column(DateTime, default=now_utc_from_ist)
    updated_at = Column(DateTime, default=now_utc_from_ist, onupdate=now_utc_from_ist)
    
    # Relationships
    user = relationship("User", backref="case_study_documents")
    # Case study created from this document (via case_study_id)
    case_study = relationship(
        "CaseStudy",
        foreign_keys=[case_study_id],
        back_populates="source_document"
    )
    # Case studies that reference this document as their source (via case_study_document_id)
    created_case_study = relationship(
        "CaseStudy",
        foreign_keys="CaseStudy.case_study_document_id",
        back_populates="document"
    )
