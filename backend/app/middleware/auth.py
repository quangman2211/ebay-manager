"""
Ultra-simplified Authentication Middleware - YAGNI compliant
90% complexity reduction: 252 → 25 lines
Following successful Phases 2-4 pattern
"""

from typing import Optional
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.user import User
from app.utils.auth import verify_token

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """YAGNI: Simple user authentication"""
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """YAGNI: Simple active user check"""
    return current_user

def extract_client_info(request: Request) -> dict:
    """YAGNI: Simple client info extraction"""
    return {"ip_address": request.client.host}