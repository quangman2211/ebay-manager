"""
Authentication Utilities
Following SOLID principles - Single Responsibility for auth functions
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("auth")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordManager:
    """
    Password management utilities
    Following SOLID: Single Responsibility for password operations
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """Generate a secure random password"""
        return secrets.token_urlsafe(length)

class JWTManager:
    """
    JWT token management utilities
    Following SOLID: Single Responsibility for JWT operations
    """
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token
        Following SOLID: Single function responsibility
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            logger.info(f"Access token created for user: {data.get('sub')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {str(e)}")
            raise
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token
        Following SOLID: Single function responsibility
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            logger.info(f"Refresh token created for user: {data.get('sub')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create refresh token: {str(e)}")
            raise
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token
        Following SOLID: Single function responsibility
        """
        try:
            # Use the same secret key for both access and refresh tokens (YAGNI principle)
            secret_key = settings.JWT_SECRET_KEY
            
            payload = jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
            
            # Verify token type
            if payload.get("type") != token_type:
                logger.warning(f"Token type mismatch. Expected: {token_type}, Got: {payload.get('type')}")
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                logger.warning("Token has expired")
                return None
                
            return payload
        
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None
    
    @staticmethod
    def extract_user_id(token: str, token_type: str = "access") -> Optional[int]:
        """
        Extract user ID from JWT token
        Following SOLID: Single function responsibility
        """
        payload = JWTManager.verify_token(token, token_type)
        if payload:
            try:
                return int(payload.get("sub"))
            except (ValueError, TypeError):
                logger.error("Invalid user ID in token")
                return None
        return None
    
    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """
        Check if token is blacklisted
        Following SOLID: Single function responsibility
        Note: Implementation depends on Redis integration
        """
        # TODO: Implement Redis-based token blacklist
        # For now, return False (no blacklist)
        return False
    
    @staticmethod
    def blacklist_token(token: str) -> bool:
        """
        Add token to blacklist
        Following SOLID: Single function responsibility  
        Note: Implementation depends on Redis integration
        """
        # TODO: Implement Redis-based token blacklist
        # For now, return True (always successful)
        logger.info(f"Token blacklisted (placeholder implementation)")
        return True

class SessionManager:
    """
    Session management utilities for Redis integration
    Following SOLID: Single Responsibility for session operations
    """
    
    @staticmethod
    def create_session(user_id: int, token: str, expires_in: int = None) -> str:
        """
        Create a user session in Redis
        Following SOLID: Single function responsibility
        """
        session_id = secrets.token_urlsafe(32)
        
        # TODO: Implement Redis session storage
        # session_data = {
        #     "user_id": user_id,
        #     "token": token,
        #     "created_at": datetime.utcnow().isoformat(),
        #     "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        # }
        # redis_client.setex(f"session:{session_id}", expires_in, json.dumps(session_data))
        
        logger.info(f"Session created for user {user_id}: {session_id}")
        return session_id
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data from Redis
        Following SOLID: Single function responsibility
        """
        # TODO: Implement Redis session retrieval
        # session_data = redis_client.get(f"session:{session_id}")
        # if session_data:
        #     return json.loads(session_data)
        return None
    
    @staticmethod
    def delete_session(session_id: str) -> bool:
        """
        Delete a session from Redis
        Following SOLID: Single function responsibility
        """
        # TODO: Implement Redis session deletion
        # return bool(redis_client.delete(f"session:{session_id}"))
        logger.info(f"Session deleted: {session_id}")
        return True
    
    @staticmethod
    def delete_user_sessions(user_id: int) -> int:
        """
        Delete all sessions for a user
        Following SOLID: Single function responsibility
        """
        # TODO: Implement Redis user session cleanup
        # pattern = f"session:*"
        # sessions = redis_client.keys(pattern)
        # deleted = 0
        # for session_key in sessions:
        #     session_data = redis_client.get(session_key)
        #     if session_data:
        #         data = json.loads(session_data)
        #         if data.get("user_id") == user_id:
        #             redis_client.delete(session_key)
        #             deleted += 1
        # return deleted
        logger.info(f"All sessions deleted for user {user_id}")
        return 0  # Placeholder

class SecurityUtils:
    """
    General security utilities
    Following SOLID: Single Responsibility for security functions
    """
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def is_password_strong(password: str) -> bool:
        """
        Check if password meets security requirements
        Following SOLID: Single function responsibility
        """
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        return all([has_upper, has_lower, has_digit, has_special])
    
    @staticmethod
    def get_password_strength_message(password: str) -> str:
        """
        Get password strength feedback message
        Following SOLID: Single function responsibility
        """
        if SecurityUtils.is_password_strong(password):
            return "Password is strong"
        
        issues = []
        if len(password) < 8:
            issues.append("at least 8 characters")
        
        if not any(c.isupper() for c in password):
            issues.append("uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("number")
        
        if not any(not c.isalnum() for c in password):
            issues.append("special character")
        
        return f"Password must contain: {', '.join(issues)}"