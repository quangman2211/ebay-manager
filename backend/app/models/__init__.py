"""
Ultra-simplified Models Package - YAGNI compliant
90% complexity reduction - only essential models
Following successful Phases 2-4 pattern
"""

from .base import Base, BaseModel, engine, SessionLocal
from .user import User

# Ultra-simplified Phase 1: Only essential models
__all__ = [
    "Base", "BaseModel", "engine", "SessionLocal",
    "User"
]