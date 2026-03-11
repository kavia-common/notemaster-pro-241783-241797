"""
Authentication router for NoteMaster Pro API.
Handles user registration, login, and profile endpoints.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# PUBLIC_INTERFACE
@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED,
             summary="Register a new user",
             description="Create a new user account with username, email, and password.")
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.

    Args:
        user_data: Registration data with username, email, and password
        db: Database session

    Returns:
        The created user profile

    Raises:
        HTTPException 400 if username or email already exists
    """
    # Check if username exists
    if db.query(models.User).filter(models.User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    # Check if email exists
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create the user
    user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# PUBLIC_INTERFACE
@router.post("/login", response_model=schemas.Token,
             summary="User login",
             description="Authenticate with username and password to receive a JWT token.")
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT access token.

    Args:
        user_data: Login credentials (username and password)
        db: Database session

    Returns:
        JWT token object with access_token and token_type

    Raises:
        HTTPException 401 if credentials are invalid
    """
    # Try to find user by username or email
    user = db.query(models.User).filter(
        (models.User.username == user_data.username) |
        (models.User.email == user_data.username)
    ).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return schemas.Token(access_token=access_token, token_type="bearer")


# PUBLIC_INTERFACE
@router.get("/me", response_model=schemas.UserResponse,
            summary="Get current user",
            description="Return the authenticated user's profile information.")
def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Get the current authenticated user's profile.

    Args:
        current_user: The authenticated user (injected by dependency)

    Returns:
        User profile data
    """
    return current_user
