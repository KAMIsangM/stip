"""Authentication API — user registration and login."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies.auth import get_current_user
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class LoginRequest(BaseModel):
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserInfoResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: str


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register
# ---------------------------------------------------------------------------


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    # Check duplicate username
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已被注册",
        )

    # Check duplicate email
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="邮箱已被注册",
        )

    # Create user
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("User registered: id=%d, username=%s, email=%s", user.id, user.username, user.email)

    # Generate token
    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
    )


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password, return JWT token."""
    # Find user by email
    user = db.query(User).filter(User.email == body.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    # Verify password
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    logger.info("User logged in: id=%d, username=%s", user.id, user.username)

    # Generate token
    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
    )


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me — current user info
# ---------------------------------------------------------------------------


@router.get("/auth/me", response_model=UserInfoResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user's info."""
    return UserInfoResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at.isoformat() if current_user.created_at else "",
    )
