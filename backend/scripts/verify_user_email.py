#!/usr/bin/env python3
"""
Script to manually verify a user's email (for testing/development).
Usage: python scripts/verify_user_email.py <email>
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from models.user import User

def verify_user_email(email: str):
    """Manually verify a user's email."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User not found: {email}")
            return False
        
        if user.email_verified:
            print(f"✓ Email already verified for: {email}")
            return True
        
        # Verify email
        user.email_verified = True
        user.is_active = True
        user.email_verified_at = datetime.utcnow()
        user.email_verification_token = None
        
        db.commit()
        db.refresh(user)
        
        print(f"✓ Email verified successfully for: {email}")
        print(f"  User is now active and can login")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying email: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/verify_user_email.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    verify_user_email(email)
