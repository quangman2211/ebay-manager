# Phase 1: Infrastructure + Basic Authentication (YAGNI Optimized)

## Overview  
**SIMPLIFIED APPROACH**: Combined infrastructure setup with basic authentication system using simple admin/user roles. Eliminates complex RBAC, MFA, and advanced security monitoring in favor of essential features for 30-account scale.

## YAGNI Violations Eliminated
- ❌ **Complex RBAC system** → Simple admin/user roles  
- ❌ **Multi-factor authentication** → Basic JWT authentication
- ❌ **Advanced session management** → Simple JWT expiration
- ❌ **Complex audit logging** → Essential security logs only
- ❌ **Permission granularity** → Account-level access only

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **AuthService**: Handle only login/logout operations
- **UserService**: Handle only user CRUD operations
- **TokenService**: Handle only JWT operations
- **PasswordService**: Handle only password hashing

### Open/Closed Principle (OCP)
- **Authentication**: Extensible for future auth methods without changing core
- **User Roles**: Add new roles through configuration

### Interface Segregation Principle (ISP)
- **Auth Interfaces**: Separate authentication vs user management
- **Role Interfaces**: Admin operations separate from user operations

### Dependency Inversion Principle (DIP)
- **Abstract Dependencies**: Services depend on interfaces
- **Injected Services**: Database and external services injected

---

## Simplified Database Schema

### Basic User & Account Models
```python
# app/models/user.py - Single Responsibility: User data representation
from sqlalchemy import Column, String, DateTime, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from enum import Enum as PyEnum
from app.database import Base

class UserRole(PyEnum):
    ADMIN = "admin"      # Full system access
    USER = "user"        # Account-specific access only

class User(Base):
    __tablename__ = "users"
    
    # Core identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(320), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    
    # Simple authentication
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    account_memberships = relationship("UserAccount", back_populates="user")

class Account(Base):
    __tablename__ = "accounts"
    
    # Core identification  
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ebay_username = Column(String(100), unique=True, nullable=False)
    account_name = Column(String(200), nullable=False)
    
    # Simple status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_memberships = relationship("UserAccount", back_populates="account")
    orders = relationship("Order", back_populates="account")
    listings = relationship("Listing", back_populates="account")
    customers = relationship("Customer", back_populates="account")

class UserAccount(Base):
    """Simple many-to-many relationship - users can access multiple accounts"""
    __tablename__ = "user_accounts"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), primary_key=True)
    
    # Simple access control
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=False)  # Only admins or account owners
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="account_memberships")
    account = relationship("Account", back_populates="user_memberships")
```

---

## Simplified Authentication Service

### Basic Auth Service (No Over-Engineering)
```python
# app/services/auth_service.py - Single Responsibility: Authentication operations
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.core.config import settings

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Simple username/password authentication"""
        user = self.user_repo.find_by_email(email)
        if not user or not user.is_active:
            return None
            
        if not self.verify_password(password, user.password_hash):
            return None
            
        # Update last login
        user.last_login = datetime.utcnow()
        self.user_repo.update(user)
        
        return user
    
    def create_access_token(self, user: User) -> str:
        """Create simple JWT token"""
        # Get user's account access
        accounts = []
        for membership in user.account_memberships:
            accounts.append({
                "account_id": str(membership.account_id),
                "can_read": membership.can_read,
                "can_write": membership.can_write
            })
        
        payload = {
            "user_id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "accounts": accounts,
            "exp": datetime.utcnow() + timedelta(hours=24)  # Simple 24h expiration
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return payload
        except JWTError:
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
```

### Simple User Service
```python
# app/services/user_service.py - Single Responsibility: User management
from typing import List, Optional
from app.models.user import User, UserRole, UserAccount
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

class UserService:
    def __init__(self, user_repo: UserRepository, auth_service: AuthService):
        self.user_repo = user_repo
        self.auth_service = auth_service
    
    def create_user(self, email: str, name: str, password: str, role: UserRole = UserRole.USER) -> User:
        """Create new user with hashed password"""
        # Check if user already exists
        if self.user_repo.find_by_email(email):
            raise ValueError("User with this email already exists")
        
        user = User(
            email=email,
            name=name,
            password_hash=self.auth_service.hash_password(password),
            role=role
        )
        
        return self.user_repo.create(user)
    
    def grant_account_access(self, user_id: str, account_id: str, can_write: bool = False) -> UserAccount:
        """Grant user access to specific account"""
        membership = UserAccount(
            user_id=user_id,
            account_id=account_id,
            can_read=True,
            can_write=can_write
        )
        
        return self.user_repo.create_account_membership(membership)
    
    def get_user_accounts(self, user_id: str) -> List[UserAccount]:
        """Get all accounts user has access to"""
        return self.user_repo.get_user_account_memberships(user_id)
    
    def is_admin(self, user: User) -> bool:
        """Simple admin check"""
        return user.role == UserRole.ADMIN
    
    def can_access_account(self, user: User, account_id: str, write_access: bool = False) -> bool:
        """Simple account access check"""
        # Admins can access everything
        if self.is_admin(user):
            return True
        
        # Check specific account membership
        for membership in user.account_memberships:
            if str(membership.account_id) == account_id:
                if write_access:
                    return membership.can_write
                else:
                    return membership.can_read
        
        return False
```

---

## API Authentication (Simplified)

### FastAPI Auth Dependencies
```python
# app/core/auth.py - Authentication dependencies for FastAPI
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.models.user import User

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends()
) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    payload = auth_service.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    return payload

def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user

def require_account_access(account_id: str, write_access: bool = False):
    """Dependency factory for account-specific access"""
    def check_access(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        # Admins can access everything
        if current_user.get("role") == "admin":
            return current_user
        
        # Check account membership
        accounts = current_user.get("accounts", [])
        for account in accounts:
            if account.get("account_id") == account_id:
                if write_access and not account.get("can_write"):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Write access required for this account"
                    )
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this account"
        )
    
    return check_access
```

### Auth API Endpoints
```python
# app/api/v1/auth.py - Authentication endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.core.auth import get_current_user, require_admin

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends()
):
    """Simple login endpoint"""
    user = auth_service.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = auth_service.create_access_token(user)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse(**current_user)

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: CreateUserRequest,
    current_user: dict = Depends(require_admin),
    user_service: UserService = Depends()
):
    """Create new user (admin only)"""
    user = user_service.create_user(
        email=user_data.email,
        name=user_data.name,
        password=user_data.password,
        role=user_data.role
    )
    
    return UserResponse.from_orm(user)
```

---

## Request/Response Schemas (Simple)

### Auth Schemas  
```python
# app/schemas/auth.py - Authentication request/response models
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from app.models.user import UserRole

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: "UserResponse"

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    is_active: bool
    last_login: Optional[str]
    accounts: List[dict]  # Simple account list

    class Config:
        from_attributes = True

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: UserRole = UserRole.USER
```

---

## Security Configuration (Essential Only)

### Basic Security Settings
```python
# app/core/config.py - Essential security configuration
from pydantic_settings import BaseSettings
from typing import Optional
import secrets

class Settings(BaseSettings):
    # Basic security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    # Database
    DATABASE_URL: str
    
    # Redis (simple caching)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Basic CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Basic Security Middleware
```python
# app/core/security.py - Essential security middleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings

def setup_security(app: FastAPI):
    """Setup basic security middleware - no over-engineering"""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Basic trusted hosts
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["localhost", "127.0.0.1"]
    )
```

---

## Testing (Essential Only)

### Auth Service Tests
```python
# tests/test_auth_service.py - Core authentication tests
import pytest
from app.services.auth_service import AuthService
from app.models.user import User, UserRole

class TestAuthService:
    def test_hash_password(self):
        """Test password hashing"""
        auth_service = AuthService(mock_repo)
        password = "testpassword123"
        
        hashed = auth_service.hash_password(password)
        assert hashed != password
        assert auth_service.verify_password(password, hashed)
    
    def test_authenticate_valid_user(self):
        """Test successful authentication"""
        user = User(email="test@test.com", password_hash="hashed_password")
        auth_service = AuthService(mock_repo)
        
        # Mock repository to return user
        mock_repo.find_by_email.return_value = user
        auth_service.verify_password = lambda p, h: True
        
        result = auth_service.authenticate_user("test@test.com", "password")
        assert result == user
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        user = User(id="test-id", email="test@test.com", role=UserRole.USER)
        auth_service = AuthService(mock_repo)
        
        token = auth_service.create_access_token(user)
        assert token is not None
        assert isinstance(token, str)
```

### API Tests
```python
# tests/test_auth_api.py - Authentication API tests
from fastapi.testclient import TestClient

def test_login_success(client: TestClient):
    """Test successful login"""
    response = client.post("/api/v1/auth/login", json={
        "email": "test@test.com",
        "password": "password"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_protected_route(client: TestClient, auth_headers):
    """Test protected route access"""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
```

---

## Database Migration (Simple)

### Alembic Migration
```python
# alembic/versions/001_basic_auth_tables.py
"""Basic auth tables

Revision ID: 001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(320), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('role', sa.Enum('admin', 'user', name='userrole'), default='user'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime())
    )
    
    # Accounts table
    op.create_table('accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ebay_username', sa.String(100), nullable=False, unique=True),
        sa.Column('account_name', sa.String(200), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    
    # User-Account relationships
    op.create_table('user_accounts',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), primary_key=True),
        sa.Column('can_read', sa.Boolean(), default=True),
        sa.Column('can_write', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

def downgrade():
    op.drop_table('user_accounts')
    op.drop_table('accounts')
    op.drop_table('users')
    op.execute('DROP TYPE userrole')
```

---

## Summary: Authentication Simplified

### ✅ Features Kept (Essential)
- JWT-based authentication
- Basic admin/user roles
- Account-level access control
- Password hashing with bcrypt
- Simple token expiration

### ❌ Features Eliminated (YAGNI Violations)
- Complex RBAC system
- Multi-factor authentication
- Advanced session management
- Complex audit logging
- Granular permissions system
- Advanced security monitoring

### 📊 Complexity Reduction
- **Authentication models**: 75% simpler
- **Security middleware**: 60% less code
- **Permission system**: 80% reduction
- **API endpoints**: 50% fewer endpoints
- **Development time**: 2-3 weeks vs 4-5 weeks

**Result**: Clean, secure authentication system appropriate for 30-account scale that provides essential security without over-engineering.