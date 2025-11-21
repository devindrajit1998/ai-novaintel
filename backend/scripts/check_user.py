#!/usr/bin/env python3
"""
Script to check user status and manually verify email if needed.
Usage: python scripts/check_user.py <email>
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from models.user import User
from utils.security import verify_password, get_password_hash

def check_user(email: str):
    """Check user status and details."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User not found: {email}")
            return
        
        print(f"\n✓ User found: {email}")
        print(f"  ID: {user.id}")
        print(f"  Full Name: {user.full_name}")
        print(f"  Email Verified: {user.email_verified}")
        print(f"  Is Active: {user.is_active}")
        print(f"  Role: {user.role}")
        print(f"  Created At: {user.created_at}")
        print(f"  Password Hash: {user.hashed_password[:50]}...")
        print(f"  Hash Scheme: {'pbkdf2' if 'pbkdf2' in user.hashed_password else 'bcrypt' if 'bcrypt' in user.hashed_password else 'unknown'}")
        
        if not user.email_verified:
            print(f"\n⚠️  Email not verified! User cannot login.")
            print(f"   To verify manually, use: python scripts/verify_user_email.py {email}")
        
    finally:
        db.close()

def test_password(email: str, password: str):
    """Test password verification."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User not found: {email}")
            return
        
        print(f"\n🔐 Testing password for: {email}")
        try:
            is_valid = verify_password(password, user.hashed_password)
            if is_valid:
                print(f"✓ Password is CORRECT")
            else:
                print(f"❌ Password is INCORRECT")
        except Exception as e:
            print(f"❌ Password verification error: {e}")
            import traceback
            traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_user.py <email> [password]")
        print("  If password is provided, it will test password verification")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    
    check_user(email)
    
    if password:
        test_password(email, password)

