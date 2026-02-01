"""
User service for CRUD operations
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash, verify_password


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email address"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """Get a user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: Optional[str] = None,
) -> User:
    """
    Create a new user
    
    Args:
        db: Database session
        email: User's email address
        password: Plain text password (will be hashed)
        full_name: Optional full name
        
    Returns:
        Created user object
    """
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password
    
    Args:
        db: Database session
        email: User's email
        password: Plain text password
        
    Returns:
        User if credentials are valid, None otherwise
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_user(
    db: Session,
    user: User,
    full_name: Optional[str] = None,
    kindle_email: Optional[str] = None,
) -> User:
    """Update user profile"""
    if full_name is not None:
        user.full_name = full_name
    if kindle_email is not None:
        user.kindle_email = kindle_email
    db.commit()
    db.refresh(user)
    return user


def update_password(db: Session, user: User, new_password: str) -> User:
    """Update user's password"""
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user
