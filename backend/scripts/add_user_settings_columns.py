"""
Migration script to add user settings columns to users table.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import engine
from sqlalchemy import text

def run_migration():
    """Add user settings columns to users table if they don't exist."""
    print("Starting migration: Add user settings columns to users table...")
    
    columns_to_add = [
        ("proposal_tone", "VARCHAR(50) DEFAULT 'professional'"),
        ("ai_response_style", "VARCHAR(50) DEFAULT 'balanced'"),
        ("secure_mode", "BOOLEAN DEFAULT FALSE"),
        ("auto_save_insights", "BOOLEAN DEFAULT TRUE"),
        ("theme_preference", "VARCHAR(20) DEFAULT 'light'"),
    ]
    
    with engine.connect() as conn:
        try:
            for column_name, column_def in columns_to_add:
                # Check if column already exists
                check_query = text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='{column_name}'
                """)
                result = conn.execute(check_query)
                if result.fetchone():
                    print(f"Column {column_name} already exists. Skipping.")
                    continue
                
                # Add column
                alter_query = text(f"""
                    ALTER TABLE users 
                    ADD COLUMN {column_name} {column_def}
                """)
                conn.execute(alter_query)
                print(f"Successfully added {column_name} column to users table.")
            
            conn.commit()
            print("Migration completed successfully.")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    run_migration()

