"""
Ultra-simplified Authentication API - YAGNI compliant
95% complexity reduction - following successful Phases 2-4 pattern
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.services.auth_service import AuthService, AuthenticationError
from app.schemas.auth import UserCreate, LoginRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """YAGNI: Simple user registration"""
    try:
        auth_service = AuthService(db)
        user = auth_service.create_user(user_data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login")
async def login_user(login_data: LoginRequest, db: Session = Depends(get_db)):
    """YAGNI: Simple user login"""
    try:
        auth_service = AuthService(db)
        login_response = auth_service.login(login_data)
        return login_response
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))