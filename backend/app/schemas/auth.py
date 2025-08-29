"""
Authentication Schemas
Following SOLID principles - Single Responsibility for auth data validation
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime

class UserBase(BaseModel):
    """
    Base user schema with common fields
    Following SOLID: Single Responsibility for user data structure
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)

class UserCreate(UserBase):
    """
    User creation schema with password
    Following SOLID: Single Responsibility for user creation validation
    """
    password: str = Field(..., min_length=8, max_length=100)
    role: Optional[str] = Field("user", pattern="^(admin|user)$")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and digit characters')
        
        return v

class UserUpdate(BaseModel):
    """
    User update schema
    Following SOLID: Single Responsibility for user updates
    """
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """
    User response schema (excludes sensitive data)
    Following SOLID: Single Responsibility for user data response
    """
    id: int
    role: str
    is_active: bool
    email_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    """
    Login request schema
    Following SOLID: Single Responsibility for login validation
    """
    username_or_email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class LoginResponse(BaseModel):
    """
    Login response schema
    Following SOLID: Single Responsibility for login response structure
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class TokenRefreshRequest(BaseModel):
    """
    Token refresh request schema
    Following SOLID: Single Responsibility for token refresh validation
    """
    refresh_token: str = Field(..., min_length=1)

class TokenRefreshResponse(BaseModel):
    """
    Token refresh response schema
    Following SOLID: Single Responsibility for token refresh response
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class PasswordChangeRequest(BaseModel):
    """
    Password change request schema
    Following SOLID: Single Responsibility for password change validation
    """
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_new_password_strength(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('New password must contain uppercase, lowercase, and digit characters')
        
        return v

class PasswordResetRequest(BaseModel):
    """
    Password reset request schema
    Following SOLID: Single Responsibility for password reset validation
    """
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """
    Password reset confirmation schema
    Following SOLID: Single Responsibility for password reset confirmation
    """
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and digit characters')
        
        return v

class UserProfile(BaseModel):
    """
    User profile schema for profile updates
    Following SOLID: Single Responsibility for profile data
    """
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)

class ApiResponse(BaseModel):
    """
    Generic API response schema
    Following SOLID: Single Responsibility for API response structure
    """
    success: bool
    message: str
    data: Optional[dict] = None

class TokenPayload(BaseModel):
    """
    JWT token payload schema
    Following SOLID: Single Responsibility for token data structure
    """
    sub: int  # user ID
    username: str
    role: str
    type: str  # access or refresh
    exp: datetime