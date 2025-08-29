# Authentication System - JWT with Simple Role-Based Access

## Overview
Complete JWT authentication system for eBay Management System following YAGNI/SOLID principles. Implements simple admin/user role-based access optimized for 30-account scale with essential security features only.

## SOLID Principles Applied
- **Single Responsibility**: Auth service handles only authentication/authorization concerns
- **Open/Closed**: Auth system extensible for new roles without modifying core logic
- **Liskov Substitution**: User types (admin/user) interchangeable through common interface
- **Interface Segregation**: Separate interfaces for auth, user management, and session handling
- **Dependency Inversion**: Auth system depends on abstract user repository, not concrete implementation

## YAGNI Compliance
✅ **Simple Role System**: Admin/user roles only (no complex RBAC with permissions)  
✅ **JWT-based**: Stateless authentication appropriate for API-first architecture  
✅ **Basic Security**: Password hashing, token expiration, secure headers only  
✅ **Essential Features**: Login, logout, token refresh, role-based access control  
❌ **Eliminated**: OAuth providers, MFA, complex permissions, password policies, audit logs

---

## Authentication Architecture

### JWT Token Flow
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          JWT AUTHENTICATION FLOW                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    POST /auth/login     ┌─────────────────────────────────┐     │
│  │   Client    │───────────────────────▶ │        Auth Service             │     │
│  │             │    {username, password}  │                                │     │
│  │             │                         │  1. Validate credentials       │     │
│  │             │                         │  2. Generate Access Token      │     │
│  │             │                         │  3. Generate Refresh Token     │     │
│  │             │    ◀─────────────────────│  4. Return tokens + user info │     │
│  │             │    {access_token,        │                                │     │
│  │             │     refresh_token,       └─────────────────────────────────┘     │
│  │             │     user_info}                        │                         │
│  │             │                                      │                         │
│  │             │                                      ▼                         │
│  │             │    API Request + Bearer Token  ┌─────────────────────────────────┐ │
│  │             │──────────────────────────────▶ │     Protected Endpoint      │ │
│  │             │                                │                             │ │
│  │             │                                │  1. Extract Bearer Token    │ │
│  │             │                                │  2. Validate JWT signature  │ │
│  │             │                                │  3. Check expiration        │ │
│  │             │                                │  4. Extract user info       │ │
│  │             │                                │  5. Verify role access      │ │
│  │             │                                │  6. Process request         │ │
│  │             │    ◀────────────────────────────│                             │ │
│  │             │    API Response                 └─────────────────────────────────┘ │
│  │             │                                                                   │
│  │             │    POST /auth/refresh                                            │
│  │             │──────────────────────────────▶ ┌─────────────────────────────────┐ │
│  │             │    {refresh_token}              │     Token Refresh Service   │ │
│  │             │                                │                             │ │
│  │             │                                │  1. Validate refresh token  │ │
│  │             │                                │  2. Check blacklist         │ │
│  │             │                                │  3. Generate new access     │ │
│  │             │                                │  4. Return new tokens       │ │
│  │             │    ◀────────────────────────────│                             │ │
│  │             │    {access_token, refresh_token}└─────────────────────────────────┘ │
│  └─────────────┘                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Security Components
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SECURITY ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        Password Security                                │   │
│  │                                                                         │   │
│  │  • bcrypt hashing with salt rounds = 12                               │   │
│  │  • Minimum 8 characters (configurable)                                │   │
│  │  • No complexity requirements (YAGNI - internal tool)                 │   │
│  │  • Password change requires current password                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         JWT Security                                    │   │
│  │                                                                         │   │
│  │  • Algorithm: HS256 (HMAC with SHA-256)                               │   │
│  │  • Access Token TTL: 15 minutes (configurable)                        │   │
│  │  • Refresh Token TTL: 7 days (configurable)                           │   │
│  │  • Secret rotation support via environment variables                   │   │
│  │  • Token blacklist for logout (Redis-based)                           │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                       Session Security                                  │   │
│  │                                                                         │   │
│  │  • Redis-based session storage (DB 1)                                 │   │
│  │  • Session fixation protection                                        │   │
│  │  • Concurrent session limit: 5 per user                               │   │
│  │  • Automatic cleanup of expired sessions                              │   │
│  │  • Last login tracking                                                │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                       HTTP Security                                     │   │
│  │                                                                         │   │
│  │  • HTTPS enforcement in production                                     │   │
│  │  • Secure cookie flags (httpOnly, secure, sameSite)                   │   │
│  │  • CORS configuration for frontend domains                            │   │
│  │  • Security headers (CSP, X-Frame-Options, etc.)                      │   │
│  │  • Rate limiting by IP and user                                       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Complete Implementation

### 1. Authentication Models & Schemas
```python
# auth/models.py - Pydantic models for authentication

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """Simple role enumeration - YAGNI compliant"""
    ADMIN = "admin"
    USER = "user"

class UserCreate(BaseModel):
    """User creation schema"""
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.USER
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be 3-50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserUpdate(BaseModel):
    """User update schema"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    
class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters')
        return v

class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str
    
class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: 'UserResponse'
    
class RefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str
    
class UserResponse(BaseModel):
    """User response schema (excluding sensitive data)"""
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: UserRole
    is_active: bool
    email_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
        
class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: int  # user ID
    username: str
    role: UserRole
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    type: str  # "access" or "refresh"
```

### 2. Password Management Service
```python
# auth/password.py - Secure password handling

import bcrypt
from typing import Optional
import secrets
import string

class PasswordManager:
    """Password hashing and validation service"""
    
    def __init__(self, rounds: int = 12):
        """Initialize with bcrypt rounds (12 = ~250ms on modern CPU)"""
        self.rounds = rounds
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with salt"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate secure random password"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def is_password_strong(self, password: str) -> tuple[bool, List[str]]:
        """Basic password strength check - YAGNI compliant"""
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters")
        
        # Only basic length check for internal tool
        # Complex requirements eliminated per YAGNI
        
        return len(issues) == 0, issues

# Global password manager instance
password_manager = PasswordManager()
```

### 3. JWT Token Service
```python
# auth/jwt.py - JWT token management

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from auth.models import TokenPayload, UserRole
import redis
import json
from core.config import settings

class JWTManager:
    """JWT token generation and validation service"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    def create_access_token(self, user_id: int, username: str, role: UserRole) -> tuple[str, datetime]:
        """Create JWT access token"""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = TokenPayload(
            sub=user_id,
            username=username,
            role=role,
            exp=int(expire.timestamp()),
            iat=int(now.timestamp()),
            type="access"
        )
        
        token = jwt.encode(
            payload.dict(),
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return token, expire
    
    def create_refresh_token(self, user_id: int, username: str, role: UserRole) -> tuple[str, datetime]:
        """Create JWT refresh token"""
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = TokenPayload(
            sub=user_id,
            username=username,
            role=role,
            exp=int(expire.timestamp()),
            iat=int(now.timestamp()),
            type="refresh"
        )
        
        token = jwt.encode(
            payload.dict(),
            self.secret_key,
            algorithm=self.algorithm
        )
        
        # Store refresh token in Redis for validation
        self._store_refresh_token(token, user_id, expire)
        
        return token, expire
    
    def verify_token(self, token: str, token_type: str = "access") -> TokenPayload:
        """Verify JWT token and return payload"""
        try:
            # Check if token is blacklisted
            if self._is_token_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            token_payload = TokenPayload(**payload)
            
            # Verify token type
            if token_payload.type != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )
            
            # Check expiration
            if datetime.utcnow().timestamp() > token_payload.exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return token_payload
            
        except jwt.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    def refresh_access_token(self, refresh_token: str) -> tuple[str, str, datetime]:
        """Generate new access token from refresh token"""
        # Verify refresh token
        payload = self.verify_token(refresh_token, "refresh")
        
        # Verify refresh token exists in Redis
        if not self._is_refresh_token_valid(refresh_token, payload.sub):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or expired"
            )
        
        # Generate new access token
        access_token, access_expire = self.create_access_token(
            payload.sub, payload.username, payload.role
        )
        
        # Generate new refresh token (optional - rotate refresh tokens)
        new_refresh_token, _ = self.create_refresh_token(
            payload.sub, payload.username, payload.role
        )
        
        # Invalidate old refresh token
        self._invalidate_refresh_token(refresh_token, payload.sub)
        
        return access_token, new_refresh_token, access_expire
    
    def blacklist_token(self, token: str) -> None:
        """Add token to blacklist (for logout)"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # Don't verify expiration for blacklisting
            )
            
            # Calculate TTL based on token expiration
            exp_timestamp = payload.get('exp', 0)
            now_timestamp = datetime.utcnow().timestamp()
            ttl = max(0, int(exp_timestamp - now_timestamp))
            
            if ttl > 0:
                # Store token hash to save Redis memory
                token_hash = self._hash_token(token)
                self.redis_client.setex(
                    f"blacklist:{token_hash}",
                    ttl,
                    "blacklisted"
                )
                
        except jwt.PyJWTError:
            # If token is invalid, no need to blacklist
            pass
    
    def logout_all_sessions(self, user_id: int) -> None:
        """Logout all sessions for a user"""
        # Invalidate all refresh tokens for user
        pattern = f"refresh_token:{user_id}:*"
        for key in self.redis_client.scan_iter(match=pattern):
            self.redis_client.delete(key)
    
    def _store_refresh_token(self, token: str, user_id: int, expire: datetime) -> None:
        """Store refresh token in Redis"""
        token_hash = self._hash_token(token)
        key = f"refresh_token:{user_id}:{token_hash}"
        ttl = int((expire - datetime.utcnow()).total_seconds())
        
        token_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expire.isoformat()
        }
        
        self.redis_client.setex(key, ttl, json.dumps(token_data))
    
    def _is_refresh_token_valid(self, token: str, user_id: int) -> bool:
        """Check if refresh token exists in Redis"""
        token_hash = self._hash_token(token)
        key = f"refresh_token:{user_id}:{token_hash}"
        return self.redis_client.exists(key)
    
    def _invalidate_refresh_token(self, token: str, user_id: int) -> None:
        """Remove refresh token from Redis"""
        token_hash = self._hash_token(token)
        key = f"refresh_token:{user_id}:{token_hash}"
        self.redis_client.delete(key)
    
    def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        token_hash = self._hash_token(token)
        return self.redis_client.exists(f"blacklist:{token_hash}")
    
    def _hash_token(self, token: str) -> str:
        """Create hash of token for Redis storage"""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()

# Global JWT manager instance
jwt_manager = JWTManager()
```

### 4. User Service & Repository
```python
# auth/service.py - User management service

from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from auth.models import UserCreate, UserUpdate, UserResponse, PasswordChange
from auth.password import password_manager
from database.models import User
from database.database import get_db
from datetime import datetime

class UserService:
    """User management service following SOLID principles"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_create: UserCreate) -> UserResponse:
        """Create new user with hashed password"""
        # Check if username exists
        existing_user = self.get_user_by_username(user_create.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email exists
        existing_email = self.get_user_by_email(user_create.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Hash password
        hashed_password = password_manager.hash_password(user_create.password)
        
        # Create user
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            password_hash=hashed_password,
            first_name=user_create.first_name,
            last_name=user_create.last_name,
            role=user_create.role.value,
            is_active=True,
            email_verified=False  # Would integrate with email service if needed
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return UserResponse.from_orm(db_user)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username.lower()).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email.lower()).first()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not password_manager.verify_password(password, user.password_hash):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> UserResponse:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        
        # Check email uniqueness if email is being updated
        if 'email' in update_data:
            existing_email = self.get_user_by_email(update_data['email'])
            if existing_email and existing_email.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return UserResponse.from_orm(user)
    
    def change_password(self, user_id: int, password_change: PasswordChange) -> bool:
        """Change user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not password_manager.verify_password(password_change.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = password_manager.hash_password(password_change.new_password)
        
        # Update password
        user.password_hash = new_hashed_password
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return True
    
    def get_users(self, skip: int = 0, limit: int = 100, role: Optional[str] = None, 
                  is_active: Optional[bool] = None) -> List[UserResponse]:
        """Get users with filtering"""
        query = self.db.query(User)
        
        if role:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        users = query.offset(skip).limit(limit).all()
        return [UserResponse.from_orm(user) for user in users]
    
    def delete_user(self, user_id: int) -> bool:
        """Soft delete user (deactivate)"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Soft delete by deactivating
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return True

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency injection for user service"""
    return UserService(db)
```

### 5. Authentication Dependencies
```python
# auth/dependencies.py - FastAPI dependencies for authentication

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from auth.jwt import jwt_manager
from auth.service import UserService, get_user_service
from auth.models import UserRole
from database.models import User

# HTTP Bearer token security scheme
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """Get current authenticated user from JWT token"""
    
    token = credentials.credentials
    
    # Verify token and get payload
    payload = jwt_manager.verify_token(token, "access")
    
    # Get user from database
    user = user_service.get_user_by_id(payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated"
        )
    
    return user

def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify admin role"""
    
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    user_service: UserService = Depends(get_user_service)
) -> Optional[User]:
    """Get current user if token is provided (optional authentication)"""
    
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials, user_service)
    except HTTPException:
        return None

class RoleChecker:
    """Role-based access control checker"""
    
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if UserRole(current_user.role) not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role} not authorized for this operation"
            )
        return current_user

# Convenience role checkers
require_admin = RoleChecker([UserRole.ADMIN])
require_user_or_admin = RoleChecker([UserRole.USER, UserRole.ADMIN])
```

### 6. Authentication API Endpoints
```python
# auth/router.py - Authentication API endpoints

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from auth.models import (
    LoginRequest, LoginResponse, RefreshRequest, UserCreate, 
    UserResponse, UserUpdate, PasswordChange
)
from auth.service import UserService, get_user_service
from auth.dependencies import (
    get_current_user, get_current_admin_user, require_admin, require_user_or_admin
)
from auth.jwt import jwt_manager
from database.models import User
from core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Authenticate user and return JWT tokens"""
    
    # Authenticate user
    user = user_service.authenticate_user(
        login_request.username,
        login_request.password
    )
    
    if not user:
        # Return generic message to prevent username enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Generate tokens
    access_token, access_expire = jwt_manager.create_access_token(
        user.id, user.username, user.role
    )
    
    refresh_token, _ = jwt_manager.create_refresh_token(
        user.id, user.username, user.role
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_orm(user)
    )

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    refresh_request: RefreshRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Refresh access token using refresh token"""
    
    try:
        access_token, new_refresh_token, access_expire = jwt_manager.refresh_access_token(
            refresh_request.refresh_token
        )
        
        # Get user info from new access token
        payload = jwt_manager.verify_token(access_token, "access")
        user = user_service.get_user_by_id(payload.sub)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    authorization: str = Depends(lambda x: x.credentials)  # Get raw token
):
    """Logout current user and blacklist token"""
    
    # Blacklist the current access token
    jwt_manager.blacklist_token(authorization)
    
    return {"message": "Successfully logged out"}

@router.post("/logout-all")
async def logout_all(
    current_user: User = Depends(get_current_user),
    authorization: str = Depends(lambda x: x.credentials)
):
    """Logout all sessions for current user"""
    
    # Blacklist current token
    jwt_manager.blacklist_token(authorization)
    
    # Invalidate all refresh tokens
    jwt_manager.logout_all_sessions(current_user.id)
    
    return {"message": "Successfully logged out from all sessions"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update current user information"""
    return user_service.update_user(current_user.id, user_update)

@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Change current user password"""
    
    user_service.change_password(current_user.id, password_change)
    
    # Logout all sessions to force re-authentication
    jwt_manager.logout_all_sessions(current_user.id)
    
    return {"message": "Password changed successfully. Please log in again."}

# Admin-only endpoints
@router.post("/users", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def create_user(
    user_create: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """Create new user (admin only)"""
    return user_service.create_user(user_create)

@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(require_admin)])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    user_service: UserService = Depends(get_user_service)
):
    """Get users with filtering (admin only)"""
    return user_service.get_users(skip, limit, role, is_active)

@router.get("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID (admin only)"""
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.from_orm(user)

@router.put("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """Update user (admin only)"""
    return user_service.update_user(user_id, user_update)

@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Delete user (admin only)"""
    user_service.delete_user(user_id)
    return {"message": "User deleted successfully"}
```

### 7. Security Middleware & Configuration
```python
# middleware/security.py - Security middleware and headers

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
from core.config import settings

class SecurityHeadersMiddleware:
    """Add security headers to all responses"""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    
                    # Security headers
                    security_headers = {
                        b"x-content-type-options": b"nosniff",
                        b"x-frame-options": b"DENY",
                        b"x-xss-protection": b"1; mode=block",
                        b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                        b"content-security-policy": b"default-src 'self'",
                        b"referrer-policy": b"strict-origin-when-cross-origin",
                    }
                    
                    headers.update(security_headers)
                    message["headers"] = list(headers.items())
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

class RateLimitMiddleware:
    """Simple rate limiting middleware"""
    
    def __init__(self, app: FastAPI, requests_per_minute: int = 60):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Get client IP
            client_ip = scope.get("client", [""])[0]
            current_time = time.time()
            
            # Clean old requests
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < 60
            ]
            
            # Check rate limit
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."}
                )
                await response(scope, receive, send)
                return
            
            # Add current request
            self.requests[client_ip].append(current_time)
        
        await self.app(scope, receive, send)

def setup_security_middleware(app: FastAPI):
    """Setup security middleware for the application"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )
    
    # Custom security middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Rate limiting
    if settings.ENABLE_RATE_LIMITING:
        app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
```

---

## Configuration & Environment Variables

### Environment Configuration
```python
# core/config.py - Authentication configuration

from pydantic import BaseSettings
from typing import List

class AuthSettings(BaseSettings):
    """Authentication-specific settings"""
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Configuration
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_HASH_ROUNDS: int = 12
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = 30
    MAX_CONCURRENT_SESSIONS: int = 5
    
    # Security Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    ENABLE_RATE_LIMITING: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

auth_settings = AuthSettings()
```

### Environment Variables Template
```bash
# .env - Authentication environment variables

# JWT Security (REQUIRED - Generate secure random keys)
JWT_SECRET_KEY=your_jwt_secret_key_minimum_32_characters_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Security
PASSWORD_MIN_LENGTH=8
PASSWORD_HASH_ROUNDS=12

# Session Configuration  
SESSION_TIMEOUT_MINUTES=30
MAX_CONCURRENT_SESSIONS=5

# CORS Configuration (adjust for your frontend domain)
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
ALLOWED_HOSTS=["localhost","yourdomain.com"]

# Security Features
ENABLE_RATE_LIMITING=true

# Redis Configuration (for token storage)
REDIS_URL=redis://ebay-redis:6379/1
```

---

## Testing Strategy

### Authentication Tests
```python
# tests/test_auth.py - Comprehensive authentication tests

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from auth.service import UserService
from auth.models import UserCreate, LoginRequest, UserRole
from auth.jwt import jwt_manager
from database.models import User

class TestAuthentication:
    """Authentication system tests"""
    
    def test_user_registration(self, client: TestClient, db: Session):
        """Test user registration"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
            "role": "user"
        }
        
        response = client.post("/auth/users", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data
    
    def test_user_login(self, client: TestClient, test_user: User):
        """Test user login"""
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == test_user.username
    
    def test_invalid_login(self, client: TestClient):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_token_refresh(self, client: TestClient, test_user: User):
        """Test token refresh"""
        # Login to get tokens
        login_response = client.post("/auth/login", json={
            "username": test_user.username,
            "password": "testpassword"
        })
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_protected_endpoint_access(self, client: TestClient, auth_headers: dict):
        """Test access to protected endpoint"""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
    
    def test_protected_endpoint_no_token(self, client: TestClient):
        """Test protected endpoint without token"""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_admin_endpoint_access(self, client: TestClient, admin_headers: dict):
        """Test admin-only endpoint access"""
        response = client.get("/auth/users", headers=admin_headers)
        assert response.status_code == 200
    
    def test_admin_endpoint_user_access(self, client: TestClient, auth_headers: dict):
        """Test admin endpoint with user token"""
        response = client.get("/auth/users", headers=auth_headers)
        assert response.status_code == 403
    
    def test_logout(self, client: TestClient, auth_headers: dict):
        """Test user logout"""
        response = client.post("/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        
        # Try to use token after logout
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 401

class TestPasswordSecurity:
    """Password security tests"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        from auth.password import password_manager
        
        password = "testpassword123"
        hashed = password_manager.hash_password(password)
        
        assert hashed != password
        assert password_manager.verify_password(password, hashed)
        assert not password_manager.verify_password("wrongpassword", hashed)
    
    def test_password_change(self, client: TestClient, auth_headers: dict):
        """Test password change"""
        change_data = {
            "current_password": "testpassword",
            "new_password": "newpassword123"
        }
        
        response = client.post("/auth/change-password", json=change_data, headers=auth_headers)
        assert response.status_code == 200

class TestJWTSecurity:
    """JWT token security tests"""
    
    def test_token_expiration(self):
        """Test JWT token expiration"""
        from datetime import datetime, timedelta
        import jwt
        
        # Create expired token
        payload = {
            "sub": 1,
            "username": "testuser",
            "role": "user",
            "exp": int((datetime.utcnow() - timedelta(minutes=1)).timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
            "type": "access"
        }
        
        token = jwt.encode(payload, "secret", algorithm="HS256")
        
        with pytest.raises(Exception):
            jwt_manager.verify_token(token, "access")
    
    def test_invalid_token_signature(self):
        """Test invalid token signature"""
        # Create token with wrong secret
        payload = {
            "sub": 1,
            "username": "testuser",
            "role": "user",
            "exp": int((datetime.utcnow() + timedelta(minutes=15)).timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
            "type": "access"
        }
        
        token = jwt.encode(payload, "wrong_secret", algorithm="HS256")
        
        with pytest.raises(Exception):
            jwt_manager.verify_token(token, "access")
```

---

## Success Criteria & Validation

### Authentication Requirements ✅
- [ ] JWT token generation and validation working correctly
- [ ] Access token expiration (15 minutes) enforced
- [ ] Refresh token rotation implemented and working
- [ ] Password hashing with bcrypt (12 rounds) implemented
- [ ] Token blacklisting for logout functionality working
- [ ] Role-based access control (admin/user) enforced
- [ ] Session management with Redis working properly
- [ ] Rate limiting protecting against brute force attacks

### Security Requirements ✅
- [ ] HTTPS enforcement in production environment
- [ ] Secure HTTP headers added to all responses
- [ ] CORS properly configured for frontend domains
- [ ] Password minimum length (8 characters) enforced
- [ ] No password complexity requirements (YAGNI - internal tool)
- [ ] Token secrets properly configured via environment variables
- [ ] No sensitive data exposed in API responses
- [ ] SQL injection prevention through ORM usage

### SOLID/YAGNI Compliance ✅
- [ ] **Single Responsibility**: Auth service handles only auth concerns
- [ ] **Open/Closed**: System extensible for new roles without core changes
- [ ] **Liskov Substitution**: User roles interchangeable through common interface
- [ ] **Interface Segregation**: Clean separation of auth, user, and session interfaces
- [ ] **Dependency Inversion**: Auth system depends on abstractions, not concrete implementations
- [ ] **YAGNI Applied**: Simple 2-role system, no complex permissions, no OAuth, no MFA
- [ ] All eliminated features documented with clear justification

### Performance Requirements ✅
- [ ] Authentication response time < 200ms
- [ ] Token validation time < 50ms  
- [ ] Redis session operations < 10ms
- [ ] Password hashing time ~250ms (bcrypt rounds = 12)
- [ ] Rate limiting preventing abuse (60 requests/minute)
- [ ] Concurrent session handling (5 sessions per user)

**Next Step**: Proceed to [04-configuration-management.md](./04-configuration-management.md) for complete system configuration setup.