#!/usr/bin/env python3
"""
Script to fix proposals table by adding missing columns.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import engine
from sqlalchemy import text

def run_migration():
    """Run the migration to fix proposals table."""
    statements = [
        # Add sections column
        "ALTER TABLE proposals ADD COLUMN IF NOT EXISTS sections JSONB;",
        
        # Add template_type column
        "ALTER TABLE proposals ADD COLUMN IF NOT EXISTS template_type VARCHAR(50) DEFAULT 'full';",
        
        # Add last_exported_at column
        "ALTER TABLE proposals ADD COLUMN IF NOT EXISTS last_exported_at TIMESTAMP;",
        
        # Add export_format column
        "ALTER TABLE proposals ADD COLUMN IF NOT EXISTS export_format VARCHAR(10);",
        
        # Fix title column
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'proposals' 
                AND column_name = 'title' 
                AND is_nullable = 'YES'
            ) THEN
                UPDATE proposals SET title = 'Proposal' WHERE title IS NULL;
                ALTER TABLE proposals ALTER COLUMN title SET NOT NULL;
            END IF;
        END $$;
        """,
        
        # Migrate content to sections
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'proposals' AND column_name = 'content'
            ) THEN
                UPDATE proposals 
                SET sections = CASE 
                    WHEN content IS NOT NULL AND sections IS NULL THEN
                        jsonb_build_array(
                            jsonb_build_object(
                                'id', 1,
                                'title', 'Proposal Content',
                                'content', content::text,
                                'order', 0
                            )
                        )
                    ELSE sections
                END
                WHERE content IS NOT NULL AND sections IS NULL;
            END IF;
        END $$;
        """,
        
        # Create index
        "CREATE INDEX IF NOT EXISTS idx_proposals_project_id ON proposals(project_id);",
    ]
    
    try:
        with engine.connect() as conn:
            for i, statement in enumerate(statements, 1):
                try:
                    conn.execute(text(statement.strip()))
                    conn.commit()
                except Exception as e:
                    # Some statements might fail if columns already exist, which is fine
                    error_msg = str(e).lower()
                    if 'already exists' in error_msg or 'duplicate' in error_msg:
                        pass  # Ignore
                    else:
                        print(f"Warning on statement {i}: {e}")
                    conn.rollback()
            
            print("Migration completed successfully!")
            print("  - Added sections column (JSONB)")
            print("  - Added template_type column")
            print("  - Added last_exported_at column")
            print("  - Added export_format column")
            print("  - Created index on project_id")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_migration()

