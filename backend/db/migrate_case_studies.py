"""
Auto-migration: Add missing columns to case_studies table if they don't exist.
This runs automatically on server startup.
"""
from sqlalchemy import text
from db.database import engine

def migrate_case_studies():
    """Add missing columns to case_studies table."""
    columns_to_add = [
        ("user_id", "INTEGER", "NULL", True),  # (name, type, default, nullable)
        ("project_description", "TEXT", "NULL", True),
        ("case_study_document_id", "INTEGER", "NULL", True),
        ("project_id", "INTEGER", "NULL", True),
        ("indexed", "BOOLEAN", "FALSE", True),
    ]
    
    try:
        with engine.connect() as conn:
            # Check if case_studies table exists using direct SQL query
            table_check = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'case_studies'
                )
            """)
            result = conn.execute(table_check)
            if not result.scalar():
                print("⚠ Case studies table does not exist yet. It will be created automatically.")
                return
            
            # Check which columns exist using direct SQL query (avoids domain loading issue)
            # Use a simpler scalar aggregation approach to avoid psycopg row iteration issues
            columns_query = text("""
                SELECT string_agg(column_name, ',') as columns
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'case_studies'
            """)
            result = conn.execute(columns_query)
            col_string = result.scalar()
            existing_columns = set(col_string.split(',')) if col_string else set()
            
            added_count = 0
            for column_name, column_type, default_value, nullable in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        # Add column with default value
                        nullable_clause = "" if nullable else "NOT NULL"
                        alter_query = text(f"""
                            ALTER TABLE case_studies 
                            ADD COLUMN {column_name} {column_type} DEFAULT {default_value} {nullable_clause}
                        """)
                        conn.execute(alter_query)
                        conn.commit()
                        print(f"✓ Added column to case_studies: {column_name}")
                        added_count += 1
                    except Exception as e:
                        print(f"⚠ Failed to add column {column_name} to case_studies: {e}")
                        conn.rollback()
            
            # Update existing_columns after adding new ones
            if added_count > 0:
                result = conn.execute(columns_query)
                col_string = result.scalar()
                existing_columns = set(col_string.split(',')) if col_string else set()
            
            # Add foreign key constraints if columns exist and constraints don't
            if 'user_id' in existing_columns:
                try:
                    fk_check = text("""
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE table_name = 'case_studies' 
                        AND constraint_name = 'case_studies_user_id_fkey'
                    """)
                    result = conn.execute(fk_check)
                    if not result.fetchone():
                        fk_query = text("""
                            ALTER TABLE case_studies 
                            ADD CONSTRAINT case_studies_user_id_fkey 
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                        """)
                        conn.execute(fk_query)
                        conn.commit()
                        print("✓ Added foreign key constraint: case_studies.user_id -> users.id")
                except Exception as e:
                    print(f"⚠ Failed to add foreign key constraint for user_id: {e}")
                    conn.rollback()
            
            if 'project_id' in existing_columns:
                try:
                    fk_check = text("""
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE table_name = 'case_studies' 
                        AND constraint_name = 'case_studies_project_id_fkey'
                    """)
                    result = conn.execute(fk_check)
                    if not result.fetchone():
                        fk_query = text("""
                            ALTER TABLE case_studies 
                            ADD CONSTRAINT case_studies_project_id_fkey 
                            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
                        """)
                        conn.execute(fk_query)
                        conn.commit()
                        print("✓ Added foreign key constraint: case_studies.project_id -> projects.id")
                except Exception as e:
                    print(f"⚠ Failed to add foreign key constraint for project_id: {e}")
                    conn.rollback()
            
            if added_count > 0:
                print(f"✓ Migration complete: Added {added_count} column(s) to case_studies table")
            else:
                print("✓ All case_studies columns already exist")
            
    except Exception as e:
        print(f"⚠ Case studies migration error: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise - allow server to start even if migration fails

