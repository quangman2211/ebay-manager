"""
Base Database Model
Following SOLID principles - Single Responsibility for base database functionality
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, DateTime, func
from app.core.config import settings

# Database metadata
metadata = MetaData()

# Base class for all models
Base = declarative_base(metadata=metadata)

class BaseModel(Base):
    """
    Abstract base model with common fields
    Following SOLID: Single Responsibility for common database patterns
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"

# Database engine configuration
def create_database_engine():
    """
    Create database engine with appropriate configuration
    Following SOLID: Single Responsibility for engine creation
    """
    return create_engine(
        settings.database_url_constructed,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=settings.DEBUG  # Log SQL queries in debug mode
    )

# Create engine instance
engine = create_database_engine()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for FastAPI to get database sessions
def get_db():
    """
    Database session dependency for FastAPI
    Following SOLID: Single Responsibility for session management
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()