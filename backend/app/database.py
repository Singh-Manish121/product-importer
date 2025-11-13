from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from app.config import get_settings

settings = get_settings()

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # Verify connections before using
    poolclass=NullPool if "sqlite" in settings.database_url else None,  # SQLite doesn't support pooling
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},  # SQLite thread check
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()

# Import models after Base is defined (for lazy loading)
from app.models import Product, Webhook, Job, JobStatus


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
