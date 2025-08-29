"""
Authentication Service
Following SOLID principles - Single Responsibility for authentication business logic
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.schemas.auth import UserCreate, LoginRequest, UserResponse, LoginResponse
from app.utils.auth import PasswordManager, JWTManager, SessionManager
from app.core.config import settings
from app.core.logging import get_logger, log_security_event

logger = get_logger("auth_service")

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass

class AuthorizationError(Exception):
    """Custom exception for authorization errors"""
    pass

class AuthService:
    """
    Authentication service class
    Following SOLID: Single Responsibility for authentication operations
    """
    
    def __init__(self, db: Session):
        """
        Initialize auth service with database session
        Following SOLID: Dependency Inversion - depends on session abstraction
        """
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user account
        Following SOLID: Single function responsibility
        """
        try:
            # Check if username or email already exists
            existing_user = self.db.query(User).filter(
                or_(User.username == user_data.username, User.email == user_data.email)
            ).first()
            
            if existing_user:
                if existing_user.username == user_data.username:
                    raise AuthenticationError("Username already exists")
                else:
                    raise AuthenticationError("Email already exists")
            
            # Hash the password
            hashed_password = PasswordManager.hash_password(user_data.password)
            
            # Create user instance
            user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                role=user_data.role or 'user'
            )
            
            # Save to database
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User created successfully: {user.username} (ID: {user.id})")
            log_security_event("user_created", user_id=str(user.id), username=user.username)
            
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create user: {str(e)}")
            raise
    
    def authenticate_user(self, login_data: LoginRequest) -> Optional[User]:
        """
        Authenticate a user with username/email and password
        Following SOLID: Single function responsibility
        """
        try:
            # Find user by username or email
            user = self.db.query(User).filter(
                or_(
                    User.username == login_data.username_or_email,
                    User.email == login_data.username_or_email
                )
            ).first()
            
            if not user:
                log_security_event("login_failed", username=login_data.username_or_email, reason="user_not_found")
                return None
            
            # Check if user is active
            if not user.is_active:
                log_security_event("login_failed", user_id=str(user.id), reason="user_inactive")
                return None
            
            # Verify password
            if not PasswordManager.verify_password(login_data.password, user.password_hash):
                log_security_event("login_failed", user_id=str(user.id), reason="invalid_password")
                return None
            
            # Update last login timestamp
            user.last_login = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"User authenticated successfully: {user.username} (ID: {user.id})")
            log_security_event("login_success", user_id=str(user.id), username=user.username)
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            log_security_event("login_error", username=login_data.username_or_email, error=str(e))
            raise
    
    def create_user_tokens(self, user: User) -> Tuple[str, str]:
        """
        Create access and refresh tokens for a user
        Following SOLID: Single function responsibility
        """
        try:
            # Prepare token data
            token_data = {
                "sub": str(user.id),
                "username": user.username,
                "role": user.role
            }
            
            # Create tokens
            access_token = JWTManager.create_access_token(token_data)
            refresh_token = JWTManager.create_refresh_token(token_data)
            
            # Create session (placeholder for Redis implementation)
            session_id = SessionManager.create_session(
                user.id, 
                access_token, 
                expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
            logger.info(f"Tokens created for user {user.id}: session {session_id}")
            
            return access_token, refresh_token
            
        except Exception as e:
            logger.error(f"Token creation error: {str(e)}")
            raise AuthenticationError("Failed to create tokens")
    
    def login(self, login_data: LoginRequest) -> LoginResponse:
        """
        Complete login process
        Following SOLID: Single function responsibility
        """
        # Authenticate user
        user = self.authenticate_user(login_data)
        if not user:
            raise AuthenticationError("Invalid credentials")
        
        # Create tokens
        access_token, refresh_token = self.create_user_tokens(user)
        
        # Return login response
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
    
    def refresh_token(self, refresh_token: str) -> Tuple[str, int]:
        """
        Refresh access token using refresh token
        Following SOLID: Single function responsibility
        """
        try:
            # Verify refresh token
            payload = JWTManager.verify_token(refresh_token, token_type="refresh")
            if not payload:
                raise AuthenticationError("Invalid refresh token")
            
            # Get user from database
            user_id = int(payload.get("sub"))
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            # Create new access token
            token_data = {
                "sub": str(user.id),
                "username": user.username,
                "role": user.role
            }
            
            new_access_token = JWTManager.create_access_token(token_data)
            expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
            
            logger.info(f"Token refreshed for user {user.id}")
            
            return new_access_token, expires_in
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise AuthenticationError("Failed to refresh token")
    
    def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from access token
        Following SOLID: Single function responsibility
        """
        try:
            # Verify token
            payload = JWTManager.verify_token(token, token_type="access")
            if not payload:
                return None
            
            # Check if token is blacklisted
            if JWTManager.is_token_blacklisted(token):
                log_security_event("token_blacklisted", token_used="blocked")
                return None
            
            # Get user from database
            user_id = int(payload.get("sub"))
            user = self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
            
            return user
            
        except Exception as e:
            logger.error(f"Get current user error: {str(e)}")
            return None
    
    def logout(self, token: str, user: User) -> bool:
        """
        Logout user and blacklist token
        Following SOLID: Single function responsibility
        """
        try:
            # Blacklist the token
            JWTManager.blacklist_token(token)
            
            # Delete user sessions (placeholder for Redis implementation)
            SessionManager.delete_user_sessions(user.id)
            
            logger.info(f"User logged out: {user.username} (ID: {user.id})")
            log_security_event("logout", user_id=str(user.id), username=user.username)
            
            return True
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return False
    
    def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        """
        Change user password
        Following SOLID: Single function responsibility
        """
        try:
            # Verify current password
            if not PasswordManager.verify_password(current_password, user.password_hash):
                log_security_event("password_change_failed", user_id=str(user.id), reason="invalid_current_password")
                raise AuthenticationError("Current password is incorrect")
            
            # Hash new password
            new_password_hash = PasswordManager.hash_password(new_password)
            
            # Update user password
            user.password_hash = new_password_hash
            self.db.commit()
            
            # Delete all user sessions to force re-login
            SessionManager.delete_user_sessions(user.id)
            
            logger.info(f"Password changed for user {user.id}")
            log_security_event("password_changed", user_id=str(user.id), username=user.username)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Password change error: {str(e)}")
            raise
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID
        Following SOLID: Single function responsibility
        """
        return self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username
        Following SOLID: Single function responsibility
        """
        return self.db.query(User).filter(User.username == username, User.is_active == True).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email
        Following SOLID: Single function responsibility
        """
        return self.db.query(User).filter(User.email == email, User.is_active == True).first()