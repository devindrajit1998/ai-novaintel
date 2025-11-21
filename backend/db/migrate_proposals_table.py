"""
Auto-migration: Fix proposals table to match the model.
This runs automatically on server startup.
"""
from sqlalchemy import text
from db.database import engine

def migrate_proposals_table():
    """Fix proposals table schema to match the model."""
    try:
        with engine.connect() as conn:
            # Check if proposals table exists
            table_check = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'proposals'
                )
            """)
            result = conn.execute(table_check)
            if not result.scalar():
                print("⚠ Proposals table does not exist yet. It will be created automatically.")
                return
            
            # Check which columns exist
            # Use a simpler scalar aggregation approach to avoid psycopg row iteration issues
            columns_query = text("""
                SELECT string_agg(column_name, ',') as columns
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'proposals'
            """)
            result = conn.execute(columns_query)
            col_string = result.scalar()
            existing_columns = set(col_string.split(',')) if col_string else set()
            
            added_count = 0
            
            # Add sections column if it doesn't exist (migrate from content if needed)
            if 'sections' not in existing_columns:
                try:
                    # Check if content column exists
                    if 'content' in existing_columns:
                        # Add sections column first
                        alter_query = text("""
                            ALTER TABLE proposals 
                            ADD COLUMN sections JSONB
                        """)
                        conn.execute(alter_query)
                        conn.commit()
                        
                        # Migrate content to sections format
                        migrate_query = text("""
                            UPDATE proposals 
                            SET sections = CASE 
                                WHEN content IS NOT NULL THEN
                                    jsonb_build_array(
                                        jsonb_build_object(
                                            'id', 1,
                                            'title', 'Proposal Content',
                                            'content', content::text,
                                            'order', 0
                                        )
                                    )
                                ELSE '[]'::jsonb
                            END
                            WHERE sections IS NULL
                        """)
                        conn.execute(migrate_query)
                        conn.commit()
                    else:
                        # Just add sections column
                        alter_query = text("""
                            ALTER TABLE proposals 
                            ADD COLUMN sections JSONB DEFAULT '[]'::jsonb
                        """)
                        conn.execute(alter_query)
                        conn.commit()
                    
                    print("✓ Added column: sections")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to add column sections: {e}")
                    conn.rollback()
            
            # Add template_type if missing
            if 'template_type' not in existing_columns:
                try:
                    alter_query = text("""
                        ALTER TABLE proposals 
                        ADD COLUMN template_type VARCHAR(50) DEFAULT 'full'
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Added column: template_type")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to add column template_type: {e}")
                    conn.rollback()
            
            # Add last_exported_at if missing
            if 'last_exported_at' not in existing_columns:
                try:
                    alter_query = text("""
                        ALTER TABLE proposals 
                        ADD COLUMN last_exported_at TIMESTAMP
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Added column: last_exported_at")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to add column last_exported_at: {e}")
                    conn.rollback()
            
            # Add export_format if missing
            if 'export_format' not in existing_columns:
                try:
                    alter_query = text("""
                        ALTER TABLE proposals 
                        ADD COLUMN export_format VARCHAR(10)
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Added column: export_format")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to add column export_format: {e}")
                    conn.rollback()
            
            # Fix approval workflow fields - migrate from old names to new names
            if 'approval_status' in existing_columns and 'status' not in existing_columns:
                try:
                    # Rename approval_status to status
                    alter_query = text("""
                        ALTER TABLE proposals 
                        RENAME COLUMN approval_status TO status
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Renamed column: approval_status -> status")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to rename approval_status: {e}")
                    conn.rollback()
            
            if 'approval_comment' in existing_columns and 'admin_feedback' not in existing_columns:
                try:
                    # Rename approval_comment to admin_feedback
                    alter_query = text("""
                        ALTER TABLE proposals 
                        RENAME COLUMN approval_comment TO admin_feedback
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Renamed column: approval_comment -> admin_feedback")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to rename approval_comment: {e}")
                    conn.rollback()
            
            if 'approval_reviewer_id' in existing_columns and 'reviewed_by' not in existing_columns:
                try:
                    # Rename approval_reviewer_id to reviewed_by
                    alter_query = text("""
                        ALTER TABLE proposals 
                        RENAME COLUMN approval_reviewer_id TO reviewed_by
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Renamed column: approval_reviewer_id -> reviewed_by")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to rename approval_reviewer_id: {e}")
                    conn.rollback()
            
            if 'approval_requested_at' in existing_columns and 'submitted_at' not in existing_columns:
                try:
                    # Rename approval_requested_at to submitted_at
                    alter_query = text("""
                        ALTER TABLE proposals 
                        RENAME COLUMN approval_requested_at TO submitted_at
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Renamed column: approval_requested_at -> submitted_at")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to rename approval_requested_at: {e}")
                    conn.rollback()
            
            if 'approval_decided_at' in existing_columns and 'reviewed_at' not in existing_columns:
                try:
                    # Rename approval_decided_at to reviewed_at
                    alter_query = text("""
                        ALTER TABLE proposals 
                        RENAME COLUMN approval_decided_at TO reviewed_at
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Renamed column: approval_decided_at -> reviewed_at")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to rename approval_decided_at: {e}")
                    conn.rollback()
            
            # Add missing approval workflow fields if they don't exist
            if 'status' not in existing_columns:
                try:
                    alter_query = text("""
                        ALTER TABLE proposals 
                        ADD COLUMN status VARCHAR(50) DEFAULT 'draft'
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Added column: status")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to add column status: {e}")
                    conn.rollback()
            
            if 'submitter_message' not in existing_columns:
                try:
                    alter_query = text("""
                        ALTER TABLE proposals 
                        ADD COLUMN submitter_message TEXT
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Added column: submitter_message")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to add column submitter_message: {e}")
                    conn.rollback()
            
            if 'admin_feedback' not in existing_columns:
                try:
                    alter_query = text("""
                        ALTER TABLE proposals 
                        ADD COLUMN admin_feedback TEXT
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Added column: admin_feedback")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to add column admin_feedback: {e}")
                    conn.rollback()
            
            if 'submitted_at' not in existing_columns:
                try:
                    alter_query = text("""
                        ALTER TABLE proposals 
                        ADD COLUMN submitted_at TIMESTAMP
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Added column: submitted_at")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to add column submitted_at: {e}")
                    conn.rollback()
            
            if 'reviewed_at' not in existing_columns:
                try:
                    alter_query = text("""
                        ALTER TABLE proposals 
                        ADD COLUMN reviewed_at TIMESTAMP
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Added column: reviewed_at")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to add column reviewed_at: {e}")
                    conn.rollback()
            
            if 'reviewed_by' not in existing_columns:
                try:
                    alter_query = text("""
                        ALTER TABLE proposals 
                        ADD COLUMN reviewed_by INTEGER
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    
                    # Add foreign key constraint if it doesn't exist
                    fk_check = text("""
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE table_name = 'proposals' 
                        AND constraint_name = 'proposals_reviewed_by_fkey'
                    """)
                    result = conn.execute(fk_check)
                    if not result.fetchone():
                        fk_query = text("""
                            ALTER TABLE proposals 
                            ADD CONSTRAINT proposals_reviewed_by_fkey 
                            FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
                        """)
                        conn.execute(fk_query)
                        conn.commit()
                        print("✓ Added foreign key constraint: proposals.reviewed_by -> users.id")
                    
                    print("✓ Added column: reviewed_by")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Failed to add column reviewed_by: {e}")
                    conn.rollback()
            
            if added_count > 0:
                print(f"✓ Migration complete: Updated {added_count} column(s) in proposals table")
            else:
                print("✓ All proposals table columns are up to date")
            
    except Exception as e:
        print(f"⚠ Proposals migration error: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise - allow server to start even if migration fails

