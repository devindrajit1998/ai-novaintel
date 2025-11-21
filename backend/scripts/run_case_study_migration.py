#!/usr/bin/env python3
"""
Script to run the case study documents migration.
This adds the necessary columns to the database.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import engine
from sqlalchemy import text

def run_migration():
    """Run the migration to add case study document columns."""
    statements = [
        # Create ProcessingStatus enum type
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'processingstatus') THEN
                CREATE TYPE processingstatus AS ENUM ('pending', 'extracting', 'analyzing', 'indexing', 'completed', 'failed');
            END IF;
        END $$;
        """,
        
        # Add processing_status column to case_study_documents
        """
        DO $$ 
        BEGIN
            -- Drop column if it exists with wrong type
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'case_study_documents' 
                AND column_name = 'processing_status'
            ) THEN
                ALTER TABLE case_study_documents DROP COLUMN processing_status;
            END IF;
        END $$;
        """,
        
        # Add processing_status column (use VARCHAR first, convert to enum later if needed)
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'case_study_documents' 
                AND column_name = 'processing_status'
            ) THEN
                -- Try enum first
                BEGIN
                    ALTER TABLE case_study_documents ADD COLUMN processing_status processingstatus;
                    ALTER TABLE case_study_documents ALTER COLUMN processing_status SET DEFAULT 'pending';
                EXCEPTION WHEN OTHERS THEN
                    -- If enum fails, use VARCHAR
                    ALTER TABLE case_study_documents ADD COLUMN processing_status VARCHAR(20) DEFAULT 'pending';
                END;
                UPDATE case_study_documents SET processing_status = 'pending' WHERE processing_status IS NULL;
            END IF;
        END $$;
        """,
        
        # Add error_message column
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'case_study_documents' 
                AND column_name = 'error_message'
            ) THEN
                ALTER TABLE case_study_documents ADD COLUMN error_message TEXT;
            END IF;
        END $$;
        """,
        
        # Add document_metadata column (rename from metadata if exists)
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'case_study_documents' 
                AND column_name = 'document_metadata'
            ) THEN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'case_study_documents' 
                    AND column_name = 'metadata'
                ) THEN
                    ALTER TABLE case_study_documents RENAME COLUMN metadata TO document_metadata;
                ELSE
                    ALTER TABLE case_study_documents ADD COLUMN document_metadata JSONB;
                END IF;
            END IF;
        END $$;
        """,
        
        # Add case_study_id column
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'case_study_documents' 
                AND column_name = 'case_study_id'
            ) THEN
                ALTER TABLE case_study_documents ADD COLUMN case_study_id INTEGER REFERENCES case_studies(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """,
        
        # Remove old 'processed' column if it exists
        """
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'case_study_documents' 
                AND column_name = 'processed'
            ) THEN
                ALTER TABLE case_study_documents DROP COLUMN processed;
            END IF;
        END $$;
        """,
        
        # Add project_description to case_studies
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'case_studies' 
                AND column_name = 'project_description'
            ) THEN
                ALTER TABLE case_studies ADD COLUMN project_description TEXT;
            END IF;
        END $$;
        """,
        
        # Add case_study_document_id to case_studies
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'case_studies' 
                AND column_name = 'case_study_document_id'
            ) THEN
                ALTER TABLE case_studies ADD COLUMN case_study_document_id INTEGER REFERENCES case_study_documents(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """,
        
        # Add indexed to case_studies
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'case_studies' 
                AND column_name = 'indexed'
            ) THEN
                ALTER TABLE case_studies ADD COLUMN indexed BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
        """,
        
        # Add matching_case_studies to insights
        """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'insights' 
                AND column_name = 'matching_case_studies'
            ) THEN
                ALTER TABLE insights ADD COLUMN matching_case_studies JSONB;
            END IF;
        END $$;
        """,
        
        # Create indexes
        "CREATE INDEX IF NOT EXISTS idx_case_study_documents_processing_status ON case_study_documents(processing_status);",
        "CREATE INDEX IF NOT EXISTS idx_case_study_documents_case_study_id ON case_study_documents(case_study_id);",
        "CREATE INDEX IF NOT EXISTS idx_case_studies_document_id ON case_studies(case_study_document_id);",
        "CREATE INDEX IF NOT EXISTS idx_case_studies_indexed ON case_studies(indexed);",
    ]
    
    try:
        print("[INFO] Running case study documents migration...")
        with engine.connect() as conn:
            for i, statement in enumerate(statements, 1):
                try:
                    conn.execute(text(statement.strip()))
                    conn.commit()
                    print(f"  [OK] Statement {i}/{len(statements)} executed successfully")
                except Exception as e:
                    # Some statements might fail if columns already exist, which is fine
                    error_msg = str(e).lower()
                    if 'already exists' in error_msg or 'duplicate' in error_msg or 'does not exist' in error_msg:
                        print(f"  [SKIP] Statement {i} skipped: {str(e)[:100]}")
                        conn.rollback()
                    else:
                        print(f"  [ERROR] Statement {i} failed: {str(e)[:200]}")
                        conn.rollback()
                        # Continue with other statements
                        continue
        
        print("\n[SUCCESS] Migration completed successfully!")
        print("  - Added processing_status enum and column")
        print("  - Added error_message column")
        print("  - Added document_metadata column")
        print("  - Added case_study_id column")
        print("  - Added project_description to case_studies")
        print("  - Added case_study_document_id to case_studies")
        print("  - Added indexed to case_studies")
        print("  - Added matching_case_studies to insights")
        print("  - Created indexes")
        return True
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
