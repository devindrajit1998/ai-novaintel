"""Check database schema."""
import sys
from sqlalchemy import inspect, text
from db.database import engine

try:
    conn = engine.connect()
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        ORDER BY ordinal_position
    """))
    
    print("Users table columns:")
    for row in result:
        print(f"  - {row[0]} ({row[1]})")
    
    conn.close()
    print("\n✓ Database connection successful")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

