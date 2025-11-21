from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from utils.config import settings

# Create database engine
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in environment variables")

# Build engine kwargs based on environment-driven pool settings
engine_kwargs = {
    "pool_pre_ping": True,
    "connect_args": {"connect_timeout": settings.DB_CONNECT_TIMEOUT},
}

if settings.DB_USE_NULLPOOL:
    # Delegate pooling entirely to PgBouncer (recommended with PgBouncer)
    engine_kwargs["poolclass"] = NullPool
else:
    # Use a conservative client-side pool to avoid PgBouncer MaxClients
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
    })

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

