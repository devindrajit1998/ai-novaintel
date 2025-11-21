from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="presales_manager")
    is_active = Column(Boolean, default=False)  # Changed: requires email verification
    email_verified = Column(Boolean, default=False)  # NEW: Email verification status
    email_verification_token = Column(String, nullable=True)  # NEW: Verification token
    email_verified_at = Column(DateTime, nullable=True)  # NEW: Verification timestamp
    # User Settings
    proposal_tone = Column(String, default="professional")  # professional, friendly, technical, executive, consultative
    ai_response_style = Column(String, default="balanced")  # concise, balanced, detailed
    secure_mode = Column(Boolean, default=False)  # PII sanitization enabled
    auto_save_insights = Column(Boolean, default=True)  # Auto-save AI insights
    theme_preference = Column(String, default="light")  # light, dark, system
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

