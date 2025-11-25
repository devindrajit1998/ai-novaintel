from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base
from utils.timezone import now_utc_from_ist

class CaseStudy(Base):
    __tablename__ = "case_studies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Creator of the case study
    title = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    impact = Column(String, nullable=False)  # e.g., "45% Faster Claims Processing"
    description = Column(Text, nullable=True)
    project_description = Column(Text, nullable=True)  # Detailed project description
    case_study_document_id = Column(Integer, ForeignKey("case_study_documents.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # Link to source project
    indexed = Column(Boolean, default=False)  # Whether this case study is indexed in RAG
    created_at = Column(DateTime, default=now_utc_from_ist)
    updated_at = Column(DateTime, default=now_utc_from_ist, onupdate=now_utc_from_ist)
    
    # Relationships
    # User who created this case study
    creator = relationship("User", foreign_keys=[user_id])
    # Document that created this case study (via case_study_document_id)
    document = relationship(
        "CaseStudyDocument",
        foreign_keys=[case_study_document_id],
        back_populates="created_case_study"
    )
    # Document that created this case study (via CaseStudyDocument.case_study_id) - alternative path
    source_document = relationship(
        "CaseStudyDocument",
        foreign_keys="CaseStudyDocument.case_study_id",
        back_populates="case_study"
    )

