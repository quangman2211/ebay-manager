"""
Authentication API Endpoints
Following SOLID principles - Single Responsibility for auth API routes
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.middleware.auth import get_db, get_current_active_user, extract_client_info
from app.services.auth_service import AuthService, AuthenticationError
from app.schemas.auth import (
    UserCreate, UserResponse, LoginRequest, LoginResponse, 
    TokenRefreshRequest, TokenRefreshResponse, PasswordChangeRequest,
    ApiResponse, UserProfile
)
from app.models.user import User
from app.core.logging import get_logger, log_security_event

logger = get_logger("auth_api")

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user account
    Following SOLID: Single Responsibility for user registration endpoint
    """
    try:
        client_info = extract_client_info(request)
        
        # Create auth service instance
        auth_service = AuthService(db)
        
        # Create user
        user = auth_service.create_user(user_data)
        
        logger.info(f"User registered successfully: {user.username}")
        log_security_event(
            "user_registered", 
            user_id=str(user.id), 
            username=user.username,
            ip_address=client_info.get("ip_address")
        )
        
        return UserResponse.from_orm(user)
        
    except AuthenticationError as e:
        logger.warning(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    User login endpoint
    Following SOLID: Single Responsibility for login endpoint
    """
    try:
        client_info = extract_client_info(request)
        
        # Create auth service instance
        auth_service = AuthService(db)
        
        # Perform login
        login_response = auth_service.login(login_data)
        
        logger.info(f"User logged in successfully: {login_response.user.username}")
        log_security_event(
            "login_success",
            user_id=str(login_response.user.id),
            username=login_response.user.username,
            ip_address=client_info.get("ip_address")
        )
        
        return login_response
        
    except AuthenticationError as e:
        logger.warning(f"Login failed: {str(e)}")
        log_security_event(
            "login_failed",
            username=login_data.username_or_email,
            ip_address=client_info.get("ip_address"),
            reason=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_access_token(
    refresh_data: TokenRefreshRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token
    Following SOLID: Single Responsibility for token refresh endpoint
    """
    try:
        client_info = extract_client_info(request)
        
        # Create auth service instance
        auth_service = AuthService(db)
        
        # Refresh token
        new_access_token, expires_in = auth_service.refresh_token(refresh_data.refresh_token)
        
        logger.info("Access token refreshed successfully")
        
        return TokenRefreshResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=expires_in
        )
        
    except AuthenticationError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        log_security_event(
            "token_refresh_failed",
            ip_address=client_info.get("ip_address"),
            reason=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout", response_model=ApiResponse)
async def logout_user(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    User logout endpoint
    Following SOLID: Single Responsibility for logout endpoint
    """
    try:
        client_info = extract_client_info(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
        
        # Create auth service instance
        auth_service = AuthService(db)
        
        # Perform logout
        success = auth_service.logout(token, current_user)
        
        if success:
            logger.info(f"User logged out successfully: {current_user.username}")
            log_security_event(
                "logout_success",
                user_id=str(current_user.id),
                username=current_user.username,
                ip_address=client_info.get("ip_address")
            )
            
            return ApiResponse(
                success=True,
                message="Logged out successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )
            
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information
    Following SOLID: Single Responsibility for user info endpoint
    """
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserProfile,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update user profile information
    Following SOLID: Single Responsibility for profile update endpoint
    """
    try:
        # Update user profile fields
        if profile_data.first_name is not None:
            current_user.first_name = profile_data.first_name
        
        if profile_data.last_name is not None:
            current_user.last_name = profile_data.last_name
        
        # Save changes
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Profile updated for user: {current_user.username}")
        
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@router.post("/change-password", response_model=ApiResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Change user password
    Following SOLID: Single Responsibility for password change endpoint
    """
    try:
        client_info = extract_client_info(request)
        
        # Create auth service instance
        auth_service = AuthService(db)
        
        # Change password
        success = auth_service.change_password(
            current_user,
            password_data.current_password,
            password_data.new_password
        )
        
        if success:
            logger.info(f"Password changed for user: {current_user.username}")
            log_security_event(
                "password_changed",
                user_id=str(current_user.id),
                username=current_user.username,
                ip_address=client_info.get("ip_address")
            )
            
            return ApiResponse(
                success=True,
                message="Password changed successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password change failed"
            )
            
    except AuthenticationError as e:
        logger.warning(f"Password change failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.get("/verify-token", response_model=ApiResponse)
async def verify_token(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Verify if current token is valid
    Following SOLID: Single Responsibility for token verification endpoint
    """
    return ApiResponse(
        success=True,
        message="Token is valid",
        data={
            "user_id": current_user.id,
            "username": current_user.username,
            "role": current_user.role
        }
    )