"""
Migration script to create chat-related tables.
Run this after updating models to ensure tables are created.
"""
from sqlalchemy import text
from db.database import engine


def migrate_chat_tables():
    """Create chat tables if they don't exist"""
    try:
        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'conversations'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("[INFO] Chat tables will be created by SQLAlchemy Base.metadata.create_all")
            else:
                print("[OK] Chat tables already exist")
    except Exception as e:
        print(f"[WARNING] Chat tables migration check failed: {e}")
        # Don't raise - let SQLAlchemy handle table creation


if __name__ == "__main__":
    migrate_chat_tables()

