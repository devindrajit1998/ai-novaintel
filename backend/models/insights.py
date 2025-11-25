from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base
from utils.timezone import now_utc_from_ist

class Insights(Base):
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    
    # Summary
    executive_summary = Column(Text, nullable=True)
    rfp_summary = Column(JSON, nullable=True)  # RFP summary data
    
    # Challenges (stored as JSON array)
    challenges = Column(JSON, nullable=True)  # List of challenge objects
    
    # Value propositions (stored as JSON array)
    value_propositions = Column(JSON, nullable=True)  # List of value prop strings
    
    # Discovery questions (stored as JSON)
    discovery_questions = Column(JSON, nullable=True)  # {category: [questions]}

    # Case studies (stored as JSON array)
    matching_case_studies = Column(JSON, nullable=True)  # List of case study objects
    
    # Proposal draft
    proposal_draft = Column(JSON, nullable=True)  # Proposal draft data

    # Tags/keywords
    tags = Column(JSON, nullable=True)  # List of tags
    
    # AI metadata
    ai_model_used = Column(Text, nullable=True)
    analysis_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now_utc_from_ist)
    updated_at = Column(DateTime, default=now_utc_from_ist, onupdate=now_utc_from_ist)
    
    # Relationships
    project = relationship("Project", back_populates="insights")

