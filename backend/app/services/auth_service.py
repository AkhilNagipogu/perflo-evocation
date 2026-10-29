"""
Authentication service.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.config import get_settings
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.user import (
    PasswordChange,
    PasswordResetConfirm,
    TokenResponse,
    UserRegister,
)

settings = get_settings()


class AuthService:
    """Handles user registration, authentication, and account management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserRegister) -> User:
        """Register a new user with email verification."""
        # Check existing email
        existing = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")

        # Check existing username
        existing = await self.db.execute(
            select(User).where(User.username == data.username)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Username already taken")

        # Create user
        user = User(
            email=data.email,
            username=data.username,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            is_email_verified=False,
        )
        # Generate verification token
        self.db.add(user)
        await self.db.flush()

        user.email_verification_token = create_email_verification_token(str(user.id))

        # Create wallet
        wallet = Wallet(user_id=user.id, balance_paise=0)
        self.db.add(wallet)

        await self.db.flush()
        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate a user and return tokens."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is deactivated")

        if user.is_suspended:
            raise ValueError("Account is suspended")

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

        return self._create_tokens(user)

    async def verify_email(self, token: str) -> User:
        """Verify email using token."""
        try:
            payload = decode_token(token)
            if payload.get("type") != "email_verification":
                raise ValueError("Invalid token type")
            user_id = payload["sub"]
        except Exception:
            raise ValueError("Invalid or expired verification token")

        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        user.is_email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        user.email_verification_token = None
        await self.db.flush()
        return user

    async def request_password_reset(self, email: str) -> str | None:
        """Initiate password reset — returns token (send via email)."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if not user:
            # Don't reveal whether email exists
            return None

        token = create_password_reset_token(str(user.id))
        user.password_reset_token = token
        user.password_reset_expires = datetime.now(timezone.utc)
        await self.db.flush()
        return token

    async def reset_password(self, data: PasswordResetConfirm) -> User:
        """Reset password using token."""
        try:
            payload = decode_token(data.token)
            if payload.get("type") != "password_reset":
                raise ValueError("Invalid token type")
            user_id = payload["sub"]
        except Exception:
            raise ValueError("Invalid or expired reset token")

        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        user.password_hash = hash_password(data.new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        await self.db.flush()
        return user

    async def change_password(self, user_id: uuid.UUID, data: PasswordChange) -> None:
        """Change password (requires current password)."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        if not verify_password(data.current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        user.password_hash = hash_password(data.new_password)
        await self.db.flush()

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")
            user_id = payload["sub"]
        except Exception:
            raise ValueError("Invalid or expired refresh token")

        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        return self._create_tokens(user)

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    def _create_tokens(self, user: User) -> TokenResponse:
        """Create access and refresh tokens for a user."""
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
