"""
Authentication and account management API routes.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.providers.email import EmailService
from app.schemas.user import (
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Register a new customer account and create their wallet."""
    auth_service = AuthService(db)
    try:
        user = await auth_service.register(data)
        await db.commit()
        await db.refresh(user)

        # Trigger verification email
        email_service = EmailService()
        if user.email_verification_token:
            await email_service.send_verification_email(user.email, user.email_verification_token)

        return user
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Authenticate customer and return access and refresh JWTs."""
    auth_service = AuthService(db)
    try:
        tokens = await auth_service.login(data.email, data.password)
        await db.commit()
        return tokens
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/verify-email")
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Verify customer email using token from email link."""
    auth_service = AuthService(db)
    try:
        await auth_service.verify_email(token)
        await db.commit()
        return {"message": "Email verified successfully"}
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/request-password-reset")
async def request_password_reset(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Request a password reset link sent via email."""
    auth_service = AuthService(db)
    try:
        user, token = await auth_service.request_password_reset(data.email)
        await db.commit()
        email_service = EmailService()
        await email_service.send_password_reset_email(user.email, token)
    except Exception:
        # Avoid user enumeration by returning success regardless
        pass
    return {"message": "If this email exists in our system, password reset instructions have been sent."}


@router.post("/reset-password")
async def reset_password(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Reset password using token from reset email."""
    auth_service = AuthService(db)
    try:
        await auth_service.reset_password(data.token, data.new_password)
        await db.commit()
        return {"message": "Password has been successfully reset. Please log in with your new password."}
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Obtain a new access and refresh token pair using an unexpired refresh token."""
    auth_service = AuthService(db)
    try:
        tokens = await auth_service.refresh_tokens(data.refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get profile of current authenticated customer."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update profile and notification preferences for current customer."""
    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(current_user, field, val)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Change current customer password."""
    auth_service = AuthService(db)
    try:
        await auth_service.change_password(current_user.id, data)
        await db.commit()
        return {"message": "Password changed successfully"}
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
