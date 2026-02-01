"""
API Dependencies
Common dependencies used across API endpoints
"""
from typing import Generator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.services import user_service


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,  # Don't auto-error, allows optional auth
)


class TokenPayload(BaseModel):
    """Token payload schema"""
    sub: Optional[str] = None


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[User]:
    """
    Get the current authenticated user from JWT token.
    Returns None if no token or invalid token.
    
    Usage:
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            if not current_user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            ...
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    user = user_service.get_user_by_id(db, UUID(user_id))
    if user is None or not user.is_active:
        return None
    
    return user


def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """
    Get current user, raising 401 if not authenticated.
    Use this for endpoints that REQUIRE authentication.
    
    Usage:
        @router.get("/me")
        def get_me(current_user: User = Depends(get_current_active_user)):
            return current_user
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current user, raising 403 if not a superuser.
    Use this for admin-only endpoints.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
