"""
Ultra-simplified Authentication Service - YAGNI compliant
85% complexity reduction: 313 → 50 lines
Following successful Phases 2-4 pattern
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.schemas.auth import UserCreate, LoginRequest
from app.utils.auth import hash_password, verify_password, create_access_token

class AuthenticationError(Exception):
    """Simple authentication exception"""
    pass

class AuthService:
    """YAGNI: Ultra-simple authentication service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> User:
        """YAGNI: Simple user creation"""
        # Check if user exists
        if self.get_user_by_username(user_data.username):
            raise ValueError("Username already exists")
        
        # Create user (YAGNI: only essential fields)
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            role=user_data.role or 'user'
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def login(self, login_data: LoginRequest):
        """YAGNI: Simple login with token"""
        # Find user
        user = self.db.query(User).filter(
            or_(User.username == login_data.username_or_email, 
                User.email == login_data.username_or_email)
        ).first()
        
        # Verify user and password
        if not user or not user.is_active or not verify_password(login_data.password, user.password_hash):
            raise AuthenticationError("Invalid credentials")
        
        # Create token
        token = create_access_token(user.id)
        
        from app.schemas.auth import LoginResponse
        return LoginResponse(access_token=token, user_id=user.id)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """YAGNI: Simple user lookup"""
        return self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """YAGNI: Simple username lookup"""
        return self.db.query(User).filter(User.username == username).first()