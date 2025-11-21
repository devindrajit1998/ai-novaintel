"""
Migration script to add user_id column to case_studies table.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import engine
from sqlalchemy import text

def run_migration():
    """Add user_id column to case_studies table if it doesn't exist."""
    print("Starting migration: Add user_id to case_studies table...")
    
    with engine.connect() as conn:
        try:
            # Check if column already exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='case_studies' AND column_name='user_id'
            """)
            result = conn.execute(check_query)
            if result.fetchone():
                print("Column user_id already exists. Skipping migration.")
                return
            
            # Add user_id column
            alter_query = text("""
                ALTER TABLE case_studies 
                ADD COLUMN user_id INTEGER REFERENCES users(id)
            """)
            conn.execute(alter_query)
            conn.commit()
            print("Successfully added user_id column to case_studies table.")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    run_migration()

