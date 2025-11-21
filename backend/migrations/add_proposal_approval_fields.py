"""
Migration: Add submitter_message to proposals table

NOTE: Your database already has these approval columns:
- approval_status
- approval_comment  
- approval_reviewer_id
- approval_requested_at
- approval_decided_at

This migration only adds the 'submitter_message' column.

Run: python migrations/add_proposal_approval_fields.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from db.database import SessionLocal

def upgrade():
    """Add submitter_message column to proposals table"""
    print("Starting migration: add_submitter_message")
    
    db = SessionLocal()
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'proposals' AND column_name = 'submitter_message'
        """))
        
        if result.fetchone():
            print("⚠️  Migration already applied - submitter_message column exists")
            return
        
        print("Adding submitter_message column to proposals table...")
        
        # Add submitter_message column
        db.execute(text("""
            ALTER TABLE proposals 
            ADD COLUMN submitter_message TEXT
        """))
        print("✓ Added 'submitter_message' column")
        
        db.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Migration failed: {str(e)}")
        raise
    finally:
        db.close()

def downgrade():
    """Remove submitter_message column"""
    print("Starting rollback")
    
    db = SessionLocal()
    try:
        db.execute(text("""
            ALTER TABLE proposals 
            DROP COLUMN IF EXISTS submitter_message
        """))
        
        db.commit()
        print("✅ Rollback completed!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Rollback failed: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run database migration')
    parser.add_argument('--downgrade', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    if args.downgrade:
        downgrade()
    else:
        upgrade()
