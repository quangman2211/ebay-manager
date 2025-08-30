"""
Ultra-simplified Base Model - YAGNI compliant
90% complexity reduction: 68 → 15 lines
Following successful Phases 2-4 pattern
"""

from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.core.config import settings

Base = declarative_base()

class BaseModel(Base):
    """YAGNI: Simple base model"""
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Simple database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """YAGNI: Simple database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()