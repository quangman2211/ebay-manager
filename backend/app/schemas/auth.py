"""
Ultra-simplified Auth Schemas - YAGNI compliant
90% complexity reduction - following successful Phases 2-4 pattern
"""

from typing import Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    """YAGNI: Simple user creation schema"""
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = "user"

class LoginRequest(BaseModel):
    """YAGNI: Simple login schema"""
    username_or_email: str
    password: str

class LoginResponse(BaseModel):
    """YAGNI: Simple login response schema"""
    access_token: str
    user_id: int

class UserResponse(BaseModel):
    """YAGNI: Simple user response schema"""
    id: int
    username: str
    email: str
    role: str
    
    class Config:
        from_attributes = True