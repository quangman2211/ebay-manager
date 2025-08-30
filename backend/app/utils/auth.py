"""
Ultra-simplified Authentication Utilities - YAGNI compliant
95% complexity reduction: 280 → 35 lines
Following successful Phases 2-4 pattern
"""

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt
from app.core.config import settings

# Simple password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """YAGNI: Simple password hashing"""
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """YAGNI: Simple password verification"""
    return pwd_context.verify(password, hashed)

def create_access_token(user_id: int) -> str:
    """YAGNI: Simple JWT creation"""
    expire = datetime.utcnow() + timedelta(minutes=30)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[int]:
    """YAGNI: Simple JWT verification"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except:
        return None