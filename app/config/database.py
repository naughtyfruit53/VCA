"""
Database configuration and connection management.

Sets up SQLAlchemy engine and session for PostgreSQL database.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# Create database engine with production-ready pooling configuration for AI call infrastructure (audio streaming implementation pending)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,      # Verify connections before using
    pool_size=10,            # Connection pool size
    max_overflow=20,         # Max connections beyond pool_size
    pool_recycle=3600,       # Recycle connections after 1 hour
    echo=settings.debug,     # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for all models using SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


def get_db():
    """
    Dependency function to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
