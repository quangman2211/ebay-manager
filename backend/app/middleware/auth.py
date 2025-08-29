"""
Authentication Middleware
Following SOLID principles - Single Responsibility for auth middleware
"""

from typing import Optional
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.logging import get_logger, log_security_event

logger = get_logger("auth_middleware")

# HTTP Bearer token scheme
security = HTTPBearer()

def get_db() -> Session:
    """
    Database dependency injection
    Following SOLID: Dependency Inversion for database access
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    Following SOLID: Single Responsibility for user authentication
    """
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Create auth service instance
        auth_service = AuthService(db)
        
        # Get user from token
        user = auth_service.get_current_user(token)
        
        if user is None:
            log_security_event("unauthorized_access", token_used="invalid")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Authentication middleware error: {str(e)}")
        log_security_event("auth_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (additional check for user status)
    Following SOLID: Single Responsibility for active user verification
    """
    if not current_user.is_active:
        log_security_event("inactive_user_access", user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    return current_user

def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require admin role for endpoint access
    Following SOLID: Single Responsibility for admin authorization
    """
    if current_user.role != 'admin':
        log_security_event("admin_access_denied", user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user

def optional_auth(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication for endpoints that work with or without auth
    Following SOLID: Single Responsibility for optional authentication
    """
    try:
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        # Extract token
        token = auth_header.split(" ")[1]
        
        # Create auth service instance
        auth_service = AuthService(db)
        
        # Get user from token (returns None if invalid)
        return auth_service.get_current_user(token)
        
    except Exception as e:
        logger.warning(f"Optional auth error: {str(e)}")
        return None

class RoleChecker:
    """
    Role-based authorization checker
    Following SOLID: Single Responsibility for role checking
    """
    
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """
        Check if user has required role
        Following SOLID: Single function responsibility
        """
        if current_user.role not in self.allowed_roles:
            log_security_event(
                "role_access_denied", 
                user_id=str(current_user.id),
                required_roles=",".join(self.allowed_roles),
                user_role=current_user.role
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(self.allowed_roles)}"
            )
        
        return current_user

# Convenience role checkers
require_admin_role = RoleChecker(["admin"])
allow_admin_and_user = RoleChecker(["admin", "user"])

def require_role(role: str):
    """
    Require specific role for endpoint access
    Following SOLID: Single Responsibility for role requirement
    """
    return RoleChecker([role])

def get_user_accounts_filter(
    current_user: User = Depends(get_current_active_user)
) -> Optional[int]:
    """
    Get account filter for current user (admin sees all, user sees only their accounts)
    Following SOLID: Single Responsibility for account filtering
    """
    if current_user.role == 'admin':
        return None  # Admin can see all accounts
    else:
        return current_user.id  # User can only see their own accounts

class IPWhitelist:
    """
    IP address whitelist middleware
    Following SOLID: Single Responsibility for IP filtering
    """
    
    def __init__(self, allowed_ips: list[str]):
        self.allowed_ips = allowed_ips
    
    def __call__(self, request: Request) -> bool:
        """
        Check if client IP is whitelisted
        Following SOLID: Single function responsibility
        """
        client_ip = request.client.host
        
        if self.allowed_ips and client_ip not in self.allowed_ips:
            log_security_event("ip_blocked", ip_address=client_ip)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied from this IP address"
            )
        
        return True

class RateLimit:
    """
    Rate limiting middleware (placeholder for Redis implementation)
    Following SOLID: Single Responsibility for rate limiting
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
    
    def __call__(self, request: Request) -> bool:
        """
        Check rate limit for client
        Following SOLID: Single function responsibility
        """
        # TODO: Implement Redis-based rate limiting
        # For now, always allow
        client_ip = request.client.host
        
        # Placeholder logic
        # redis_key = f"rate_limit:{client_ip}"
        # current_count = redis_client.incr(redis_key)
        # if current_count == 1:
        #     redis_client.expire(redis_key, 60)  # 1 minute
        # if current_count > self.requests_per_minute:
        #     log_security_event("rate_limit_exceeded", ip_address=client_ip)
        #     raise HTTPException(
        #         status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        #         detail="Too many requests"
        #     )
        
        return True

# Default rate limiter
default_rate_limit = RateLimit(requests_per_minute=60)

def extract_client_info(request: Request) -> dict:
    """
    Extract client information for logging
    Following SOLID: Single Responsibility for client info extraction
    """
    return {
        "ip_address": request.client.host,
        "user_agent": request.headers.get("User-Agent", "Unknown"),
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers)
    }