from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from db.database import Base
from utils.timezone import now_utc_from_ist

class ProjectStatus(str, enum.Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    SUBMITTED = "Submitted"
    WON = "Won"
    LOST = "Lost"
    ARCHIVED = "Archived"

class ProjectType(str, enum.Enum):
    NEW = "new"
    EXPANSION = "expansion"
    RENEWAL = "renewal"

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    client_name = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    region = Column(String, nullable=False)
    project_type = Column(SQLEnum(ProjectType), default=ProjectType.NEW)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=now_utc_from_ist)
    updated_at = Column(DateTime, default=now_utc_from_ist, onupdate=now_utc_from_ist)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    rfp_documents = relationship("RFPDocument", back_populates="project", cascade="all, delete-orphan")
    insights = relationship("Insights", back_populates="project", uselist=False, cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="project", cascade="all, delete-orphan")

