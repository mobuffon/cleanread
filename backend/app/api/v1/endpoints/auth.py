"""
Authentication endpoints
- Register new users
- Login (get access token)
- Get current user profile
- Update profile
"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.services import user_service


router = APIRouter()


# ============ Schemas ============

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    email: str
    full_name: Optional[str] = None
    kindle_email: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = None
    kindle_email: Optional[str] = None


class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"


class TokenWithUser(Token):
    """Token response with user info"""
    user: UserResponse


# ============ Endpoints ============

@router.post("/register", response_model=TokenWithUser, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.
    
    Returns access token and user info on successful registration.
    """
    # Check if user already exists
    existing_user = user_service.get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    
    # Validate password
    if len(user_in.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    
    # Create user
    user = user_service.create_user(
        db=db,
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
    )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    return TokenWithUser(
        access_token=access_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            kindle_email=user.kindle_email,
            is_active=user.is_active,
        ),
    )


@router.post("/login", response_model=TokenWithUser)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2 compatible token login.
    
    Get an access token for future requests.
    Use email as username.
    """
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    return TokenWithUser(
        access_token=access_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            kindle_email=user.kindle_email,
            is_active=user.is_active,
        ),
    )


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current user profile.
    
    Requires authentication.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        kindle_email=current_user.kindle_email,
        is_active=current_user.is_active,
    )


@router.patch("/me", response_model=UserResponse)
def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update current user profile.
    
    Requires authentication.
    """
    updated_user = user_service.update_user(
        db=db,
        user=current_user,
        full_name=user_update.full_name,
        kindle_email=user_update.kindle_email,
    )
    
    return UserResponse(
        id=str(updated_user.id),
        email=updated_user.email,
        full_name=updated_user.full_name,
        kindle_email=updated_user.kindle_email,
        is_active=updated_user.is_active,
    )


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Change current user's password.
    
    Requires authentication and current password verification.
    """
    from app.core.security import verify_password
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )
    
    # Validate new password
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )
    
    user_service.update_password(db, current_user, password_data.new_password)
    
    return {"status": "success", "message": "Password updated successfully"}
