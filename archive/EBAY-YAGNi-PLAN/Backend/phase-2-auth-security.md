# Phase 2: Authentication & Security Implementation

## Overview
Implement JWT-based authentication with role-based access control (RBAC) for multi-account eBay management. Ensures secure access with proper user isolation and account-level permissions.

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **AuthService**: Handle only authentication logic
- **PermissionService**: Manage only authorization/permissions  
- **TokenService**: Handle only JWT token operations
- **PasswordService**: Handle only password hashing/validation
- **SessionService**: Manage only user sessions

### Open/Closed Principle (OCP)
- **Authentication Providers**: Extensible for OAuth, LDAP, etc.
- **Permission Strategies**: Add new permission models without changing existing code
- **Token Storage**: Support multiple storage backends (Redis, database, memory)

### Liskov Substitution Principle (LSP)
- **IAuthProvider**: All auth providers must honor the same contract
- **ITokenStorage**: All token storage implementations interchangeable
- **IPermissionChecker**: All permission checkers follow same interface

### Interface Segregation Principle (ISP)
- **Separate Interfaces**: Authentication vs Authorization vs Session management
- **Client-Specific**: Users don't depend on admin-only interfaces
- **Fine-Grained Permissions**: Read/Write/Admin separated

### Dependency Inversion Principle (DIP)
- **Abstract Dependencies**: Services depend on interfaces, not concrete classes
- **Injected Dependencies**: All authentication components injected

## Authentication Architecture

### JWT Token Structure
```python
# app/models/token.py - Single Responsibility: Token data structure
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from uuid import UUID

class TokenPayload(BaseModel):
    """JWT token payload structure"""
    user_id: UUID
    email: str
    role: str
    account_permissions: List[dict]  # [{"account_id": "...", "permissions": ["read", "write"]}]
    exp: datetime
    iat: datetime
    
class AccessToken(BaseModel):
    """Access token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    
class RefreshToken(BaseModel):
    """Refresh token data"""
    refresh_token: str
    user_id: UUID
    expires_at: datetime
    is_active: bool = True
```

### Authentication Service Interface
```python
# app/services/interfaces/auth_interface.py - Interface Segregation
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from app.models.token import AccessToken, TokenPayload
from app.models.user import User

class IAuthenticator(ABC):
    """Interface for authentication operations"""
    
    @abstractmethod
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email/password"""
        pass
    
    @abstractmethod
    async def create_access_token(self, user: User) -> AccessToken:
        """Create JWT access token for user"""
        pass

class ITokenValidator(ABC):
    """Interface for token validation operations"""
    
    @abstractmethod
    async def validate_token(self, token: str) -> Optional[TokenPayload]:
        """Validate and decode JWT token"""
        pass
    
    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke/blacklist token"""
        pass

class IPermissionChecker(ABC):
    """Interface for permission checking operations"""
    
    @abstractmethod
    async def has_account_access(self, user_id: UUID, account_id: UUID) -> bool:
        """Check if user has access to account"""
        pass
    
    @abstractmethod
    async def has_permission(self, user_id: UUID, account_id: UUID, permission: str) -> bool:
        """Check specific permission for user on account"""
        pass
```

### Authentication Service Implementation
```python
# app/services/auth_service.py - Single Responsibility: Authentication logic
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import bcrypt
import jwt
from app.services.interfaces.auth_interface import IAuthenticator, ITokenValidator
from app.repositories.user import UserRepository
from app.models.user import User
from app.models.token import AccessToken, TokenPayload
from app.config import get_settings

class AuthService(IAuthenticator, ITokenValidator):
    """Handles user authentication and token management"""
    
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo
        self._settings = get_settings()
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password"""
        user = await self._user_repo.get_by_email(email)
        
        if not user or not user.is_active:
            return None
            
        if not self._verify_password(password, user.password):
            return None
            
        return user
    
    async def create_access_token(self, user: User) -> AccessToken:
        """Create JWT access token with user permissions"""
        # Get user's account permissions
        account_permissions = await self._get_user_account_permissions(user.id)
        
        # Create token payload
        expires_at = datetime.utcnow() + timedelta(
            minutes=self._settings.security.access_token_expire_minutes
        )
        
        payload = TokenPayload(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            account_permissions=account_permissions,
            exp=expires_at,
            iat=datetime.utcnow()
        )
        
        # Generate JWT token
        token = jwt.encode(
            payload.dict(),
            self._settings.security.secret_key,
            algorithm=self._settings.security.algorithm
        )
        
        return AccessToken(
            access_token=token,
            expires_in=self._settings.security.access_token_expire_minutes * 60
        )
    
    async def validate_token(self, token: str) -> Optional[TokenPayload]:
        """Validate and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self._settings.security.secret_key,
                algorithms=[self._settings.security.algorithm]
            )
            
            # Verify token hasn't expired
            exp = datetime.fromtimestamp(payload["exp"])
            if exp < datetime.utcnow():
                return None
                
            return TokenPayload(**payload)
            
        except jwt.InvalidTokenError:
            return None
    
    async def revoke_token(self, token: str) -> bool:
        """Add token to blacklist (implement with Redis)"""
        # This would use Redis to store blacklisted tokens
        # Implementation depends on token storage strategy
        return True
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    async def _get_user_account_permissions(self, user_id: UUID) -> List[dict]:
        """Get user's permissions for all accessible accounts"""
        user_accounts = await self._user_repo.get_user_accounts(user_id)
        
        permissions = []
        for ua in user_accounts:
            perms = []
            if ua.can_read:
                perms.append("read")
            if ua.can_write:
                perms.append("write")
            if ua.can_admin:
                perms.append("admin")
                
            permissions.append({
                "account_id": str(ua.account_id),
                "permissions": perms
            })
        
        return permissions
```

### Password Service
```python
# app/services/password_service.py - Single Responsibility: Password operations
import bcrypt
from typing import str

class PasswordService:
    """Handles password hashing and validation"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    @staticmethod
    def is_strong_password(password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return all([has_upper, has_lower, has_digit, has_special])
```

### Permission Service Implementation
```python
# app/services/permission_service.py - Single Responsibility: Authorization logic
from typing import List, Optional
from uuid import UUID
from app.services.interfaces.auth_interface import IPermissionChecker
from app.repositories.user import UserRepository
from app.models.user import UserRole

class PermissionService(IPermissionChecker):
    """Handles authorization and permission checking"""
    
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo
    
    async def has_account_access(self, user_id: UUID, account_id: UUID) -> bool:
        """Check if user has any access to account"""
        user_account = await self._user_repo.get_user_account(user_id, account_id)
        return user_account is not None
    
    async def has_permission(self, user_id: UUID, account_id: UUID, permission: str) -> bool:
        """Check specific permission for user on account"""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return False
            
        # Admin users have all permissions
        if user.role == UserRole.ADMIN:
            return True
            
        user_account = await self._user_repo.get_user_account(user_id, account_id)
        if not user_account:
            return False
        
        # Check specific permissions
        permission_mapping = {
            "read": user_account.can_read,
            "write": user_account.can_write,
            "admin": user_account.can_admin
        }
        
        return permission_mapping.get(permission, False)
    
    async def get_user_permissions(self, user_id: UUID, account_id: UUID) -> List[str]:
        """Get all permissions for user on specific account"""
        permissions = []
        
        if await self.has_permission(user_id, account_id, "read"):
            permissions.append("read")
        if await self.has_permission(user_id, account_id, "write"):
            permissions.append("write")
        if await self.has_permission(user_id, account_id, "admin"):
            permissions.append("admin")
            
        return permissions
    
    async def can_manage_users(self, user_id: UUID) -> bool:
        """Check if user can manage other users"""
        user = await self._user_repo.get_by_id(user_id)
        return user and user.role in [UserRole.ADMIN, UserRole.MANAGER]
```

## FastAPI Security Implementation

### Authentication Dependencies
```python
# app/dependencies/auth.py - Dependency Inversion Principle
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from uuid import UUID
from app.services.auth_service import AuthService
from app.services.permission_service import PermissionService
from app.models.token import TokenPayload
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenPayload:
    """Get current authenticated user from JWT token"""
    token_payload = await auth_service.validate_token(credentials.credentials)
    
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_payload

async def require_permission(permission: str, account_id: UUID):
    """Dependency factory for permission checking"""
    async def permission_checker(
        current_user: TokenPayload = Depends(get_current_user),
        permission_service: PermissionService = Depends(get_permission_service)
    ) -> TokenPayload:
        has_permission = await permission_service.has_permission(
            current_user.user_id, account_id, permission
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}",
            )
        
        return current_user
    
    return permission_checker

async def require_admin(
    current_user: TokenPayload = Depends(get_current_user)
) -> TokenPayload:
    """Require admin role"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
```

### Authentication Endpoints
```python
# app/routers/auth.py - Single Responsibility: Authentication endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.services.auth_service import AuthService
from app.services.password_service import PasswordService
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from app.models.token import AccessToken

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    """Authenticate user and return access token"""
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = await auth_service.create_access_token(user)
    
    return LoginResponse(
        access_token=access_token.access_token,
        token_type=access_token.token_type,
        expires_in=access_token.expires_in,
        user=UserResponse.from_orm(user)
    )

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: RegisterRequest,
    user_service: UserService = Depends(get_user_service),
    password_service: PasswordService = Depends()
) -> UserResponse:
    """Register new user account"""
    # Validate password strength
    if not password_service.is_strong_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet strength requirements"
        )
    
    # Hash password
    hashed_password = password_service.hash_password(user_data.password)
    
    # Create user
    user = await user_service.create_user(user_data, hashed_password)
    
    return UserResponse.from_orm(user)

@router.post("/logout")
async def logout(
    current_user: TokenPayload = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user and revoke token"""
    # In a real implementation, you would extract the token from the request
    # and add it to a blacklist
    return {"message": "Successfully logged out"}
```

## Role-Based Access Control (RBAC)

### Permission Decorators
```python
# app/decorators/permissions.py - Open/Closed Principle for extending permissions
from functools import wraps
from typing import Callable, List
from fastapi import HTTPException, status
from app.models.user import UserRole

def require_roles(allowed_roles: List[UserRole]):
    """Decorator to require specific user roles"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs (injected by dependency)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = UserRole(current_user.role)
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required roles: {[role.value for role in allowed_roles]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_account_permission(permission: str):
    """Decorator to require specific account permission"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            account_id = kwargs.get('account_id')
            
            if not current_user or not account_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User and account context required"
                )
            
            # Check permission in user's token payload
            user_permissions = current_user.account_permissions
            account_perms = next(
                (ap for ap in user_permissions if ap["account_id"] == str(account_id)), 
                None
            )
            
            if not account_perms or permission not in account_perms["permissions"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### Account-Level Security Middleware
```python
# app/middleware/account_security.py - Single Responsibility: Account isolation
from fastapi import Request, HTTPException, status
from typing import Optional
from uuid import UUID
import logging

class AccountSecurityMiddleware:
    """Ensures proper account-level data isolation"""
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Extract account_id from path parameters
        account_id = self._extract_account_id(request)
        
        if account_id:
            # Verify user has access to this account
            await self._verify_account_access(request, account_id)
        
        await self.app(scope, receive, send)
    
    def _extract_account_id(self, request: Request) -> Optional[UUID]:
        """Extract account_id from URL path parameters"""
        path_params = request.path_params
        account_id_str = path_params.get("account_id")
        
        if account_id_str:
            try:
                return UUID(account_id_str)
            except ValueError:
                self.logger.warning(f"Invalid account_id format: {account_id_str}")
                return None
        
        return None
    
    async def _verify_account_access(self, request: Request, account_id: UUID):
        """Verify current user has access to specified account"""
        # Extract user from JWT token
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for account access"
            )
        
        # This would integrate with your auth service to validate token
        # and check account permissions
        # For brevity, showing the concept
        self.logger.info(f"Verified access to account {account_id}")
```

## Session Management

### Redis Session Store
```python
# app/services/session_service.py - Single Responsibility: Session management
import json
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

class SessionService:
    """Handles user session storage in Redis"""
    
    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
        self._session_prefix = "session:"
        self._session_timeout = timedelta(hours=24)
    
    async def create_session(self, user_id: UUID, session_data: Dict[str, Any]) -> str:
        """Create new user session"""
        session_id = str(uuid4())
        session_key = f"{self._session_prefix}{session_id}"
        
        session_info = {
            "user_id": str(user_id),
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            **session_data
        }
        
        await self._redis.setex(
            session_key,
            self._session_timeout,
            json.dumps(session_info)
        )
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session_key = f"{self._session_prefix}{session_id}"
        session_data = await self._redis.get(session_key)
        
        if session_data:
            return json.loads(session_data)
        
        return None
    
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.update(data)
        session["last_activity"] = datetime.utcnow().isoformat()
        
        session_key = f"{self._session_prefix}{session_id}"
        await self._redis.setex(
            session_key,
            self._session_timeout,
            json.dumps(session)
        )
        
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        session_key = f"{self._session_prefix}{session_id}"
        deleted = await self._redis.delete(session_key)
        return deleted > 0
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions (scheduled task)"""
        # Redis handles TTL automatically, but this could be used
        # for additional cleanup logic if needed
        pass
```

## Implementation Tasks

### Task 1: Authentication Service Setup
1. **Implement JWT Authentication**
   - Create AuthService with login/logout
   - Implement token generation and validation
   - Add password hashing with bcrypt

2. **Setup Permission System**
   - Create PermissionService for RBAC
   - Implement account-level permissions
   - Add role-based access control

3. **Test Authentication Flow**
   - Unit tests for authentication service
   - Integration tests with database
   - JWT token validation tests

### Task 2: FastAPI Security Integration
1. **Create Security Dependencies**
   - JWT token validation dependency
   - Permission checking dependencies
   - Role-based access dependencies

2. **Implement Auth Endpoints**
   - Login/logout endpoints
   - User registration endpoint
   - Token refresh endpoint

3. **Add Security Middleware**
   - Account isolation middleware
   - Rate limiting middleware
   - CORS configuration

### Task 3: Session Management
1. **Redis Session Store**
   - Implement session creation/retrieval
   - Add session cleanup mechanisms
   - Configure session timeouts

2. **Session Security**
   - Implement session hijacking protection
   - Add concurrent session limits
   - Configure secure session cookies

### Task 4: Testing & Validation
1. **Security Testing**
   - Authentication bypass tests
   - Permission escalation tests
   - Session security tests

2. **Integration Testing**
   - End-to-end auth flow tests
   - Multi-account access tests
   - Performance tests under load

## Quality Gates

### Security Checklist
- [ ] Passwords properly hashed with bcrypt
- [ ] JWT tokens include expiration times
- [ ] Account-level data isolation enforced
- [ ] No hardcoded secrets in code
- [ ] HTTPS enforced in production
- [ ] Rate limiting implemented
- [ ] Session timeout configured
- [ ] CORS properly configured

### Performance Requirements
- [ ] Authentication response time <100ms
- [ ] Token validation time <50ms
- [ ] Session lookup time <10ms
- [ ] Support 1000+ concurrent sessions

### SOLID Compliance
- [ ] Each service has single responsibility
- [ ] Authentication providers are interchangeable
- [ ] Permission system is extensible
- [ ] No tight coupling between auth components
- [ ] All dependencies properly injected

---
**Next Phase**: CSV Data Processing Engine implementation with secure file handling and account-isolated data processing.