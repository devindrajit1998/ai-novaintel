#!/usr/bin/env python3
"""Verify all tables were created successfully."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from utils.config import settings

engine = create_engine(settings.DATABASE_URL)
expected_tables = [
    'users', 'projects', 'rfp_documents', 'insights',
    'proposals', 'case_studies', 'case_study_documents',
    'notifications', 'conversations', 'conversation_participants', 'messages'
]

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """))
    tables = [r[0] for r in result]

print(f"Found {len(tables)} tables in database:")
for table in tables:
    status = "[OK]" if table in expected_tables else "[EXTRA]"
    print(f"  {status} {table}")

missing = [t for t in expected_tables if t not in tables]
if missing:
    print(f"\nMissing tables: {', '.join(missing)}")
    sys.exit(1)
else:
    print(f"\nAll {len(expected_tables)} expected tables are present!")

