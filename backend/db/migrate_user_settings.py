"""
Auto-migration: Add user settings columns if they don't exist.
This runs automatically on server startup.
"""
from sqlalchemy import text
from db.database import engine

def migrate_user_settings():
    """Add missing user settings columns to users table."""
    columns_to_add = [
        ("proposal_tone", "VARCHAR(50)", "'professional'"),
        ("ai_response_style", "VARCHAR(50)", "'balanced'"),
        ("secure_mode", "BOOLEAN", "FALSE"),
        ("auto_save_insights", "BOOLEAN", "TRUE"),
        ("theme_preference", "VARCHAR(20)", "'light'"),
        ("company_name", "VARCHAR(255)", "NULL"),
        ("company_logo", "VARCHAR(500)", "NULL"),
    ]
    
    try:
        with engine.connect() as conn:
            # Check if users table exists using direct SQL query
            table_check = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                )
            """)
            result = conn.execute(table_check)
            if not result.scalar():
                print("⚠ Users table does not exist yet. It will be created automatically.")
                return
            
            # Check which columns exist using direct SQL query (avoids domain loading issue)
            # Use a simpler scalar aggregation approach to avoid psycopg row iteration issues
            columns_query = text("""
                SELECT string_agg(column_name, ',') as columns
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            """)
            result = conn.execute(columns_query)
            col_string = result.scalar()
            existing_columns = set(col_string.split(',')) if col_string else set()
            
            added_count = 0
            for column_name, column_type, default_value in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        # Add column with default value (handle NULL specially)
                        if default_value == "NULL":
                            alter_query = text(f"""
                                ALTER TABLE users 
                                ADD COLUMN {column_name} {column_type}
                            """)
                        else:
                            alter_query = text(f"""
                                ALTER TABLE users 
                                ADD COLUMN {column_name} {column_type} DEFAULT {default_value}
                            """)
                        conn.execute(alter_query)
                        conn.commit()
                        print(f"✓ Added column: {column_name}")
                        added_count += 1
                    except Exception as e:
                        print(f"⚠ Failed to add column {column_name}: {e}")
                        conn.rollback()
            
            if added_count > 0:
                print(f"✓ Migration complete: Added {added_count} column(s) to users table")
            else:
                print("✓ All user settings columns already exist")
            
    except Exception as e:
        print(f"⚠ Migration error: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise - allow server to start even if migration fails

