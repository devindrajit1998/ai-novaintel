#!/usr/bin/env python3
"""
Run full database migration.
This script reads the migration SQL file and executes it against the database
configured in the DATABASE_URL environment variable.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from utils.config import settings

def run_migration():
    """Execute the full migration SQL file."""
    
    # Get migration SQL file path
    migration_file = Path(__file__).parent / "full_migration.sql"
    
    if not migration_file.exists():
        print(f"Error: Migration file not found: {migration_file}")
        sys.exit(1)
    
    # Read SQL file
    print(f"Reading migration file: {migration_file}")
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Check DATABASE_URL
    if not settings.DATABASE_URL:
        print("Error: DATABASE_URL is not set in environment variables")
        print("   Please set DATABASE_URL in your .env file")
        sys.exit(1)
    
    # Mask password in URL for display
    db_url_display = settings.DATABASE_URL
    if '@' in db_url_display:
        parts = db_url_display.split('@')
        if ':' in parts[0]:
            protocol_user = parts[0].split('://')[0] + '://'
            user_pass = parts[0].split('://')[1]
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                db_url_display = f"{protocol_user}{user}:***@{parts[1]}"
    
    print(f"Connecting to database: {db_url_display}")
    
    try:
        # Create database engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"Connected to PostgreSQL: {version.split(',')[0]}")
        
        # Execute migration
        print("\nRunning migration...")
        with engine.begin() as conn:
            # Split SQL by semicolon and execute each statement
            # This is needed because some statements might fail with "already exists"
            statements = []
            current_statement = ""
            
            for line in sql_content.split('\n'):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('--'):
                    continue
                
                current_statement += line + '\n'
                
                # Check if line ends statement
                if line.endswith(';'):
                    statements.append(current_statement.strip())
                    current_statement = ""
            
            # Add any remaining statement
            if current_statement.strip():
                statements.append(current_statement.strip())
            
            # Execute statements
            success_count = 0
            error_count = 0
            
            for i, statement in enumerate(statements, 1):
                if not statement:
                    continue
                    
                try:
                    conn.execute(text(statement))
                    success_count += 1
                    if i % 10 == 0:
                        print(f"  Progress: {i}/{len(statements)} statements executed...")
                except Exception as e:
                    error_msg = str(e)
                    # Ignore "already exists" errors for tables, indexes, triggers, etc.
                    if 'already exists' in error_msg.lower() or 'does not exist' in error_msg.lower():
                        success_count += 1
                        continue
                    # Ignore constraint errors that might occur if FK already exists
                    if 'constraint' in error_msg.lower() and 'already exists' in error_msg.lower():
                        success_count += 1
                        continue
                    else:
                        print(f"  Warning at statement {i}: {error_msg}")
                        error_count += 1
        
        print(f"\nMigration completed!")
        print(f"   Successfully executed: {success_count} statements")
        if error_count > 0:
            print(f"   Warnings: {error_count} statements")
        
        # Verify tables
        print("\nVerifying tables...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'users', 'projects', 'rfp_documents', 'insights',
                'proposals', 'case_studies', 'case_study_documents',
                'notifications', 'conversations', 'conversation_participants', 'messages'
            ]
            
            print(f"   Found {len(tables)} tables:")
            for table in tables:
                status = "[OK]" if table in expected_tables else "[?]"
                print(f"   {status} {table}")
            
            missing = [t for t in expected_tables if t not in tables]
            if missing:
                print(f"\n   Warning: Missing tables: {', '.join(missing)}")
            else:
                print(f"\n   All expected tables created successfully!")
        
    except Exception as e:
        print(f"\nMigration failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("NovaIntel Database Migration")
    print("=" * 60)
    run_migration()
    print("=" * 60)

