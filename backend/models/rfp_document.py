from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base
from utils.timezone import now_utc_from_ist

class RFPDocument(Base):
    __tablename__ = "rfp_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)  # in bytes
    file_type = Column(String, nullable=False)  # pdf, docx
    uploaded_at = Column(DateTime, default=now_utc_from_ist)
    
    # Extracted metadata
    extracted_text = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="rfp_documents")

