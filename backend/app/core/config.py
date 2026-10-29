"""
Core configuration module.

All application settings are loaded from environment variables.
No secrets or business rules are hardcoded.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ──────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "CHANGE-ME-in-production"
    APP_DEBUG: bool = True

    PUBLIC_SITE_URL: str = "http://localhost:3000"
    ADMIN_SITE_URL: str = "http://localhost:3001"
    API_BASE_URL: str = "http://localhost:8000"

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://evocation:evocation_dev@localhost:5432/evocation"
    DATABASE_URL_SYNC: str = "postgresql://evocation:evocation_dev@localhost:5432/evocation"

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Authentication ───────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE-ME-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SESSION_COOKIE_DOMAIN: str = "localhost"
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"

    PASSWORD_HASH_ROUNDS: int = 12

    # ── Cloudflare ───────────────────────────────────────────────────────
    CLOUDFLARE_API_TOKEN: str = ""
    CLOUDFLARE_ZONES: str = ""  # "zone_id:domain,zone_id2:domain2"
    CLOUDFLARE_API_BASE_URL: str = "https://api.cloudflare.com/client/v4"

    @property
    def cloudflare_zone_map(self) -> dict[str, str]:
        """Parse CLOUDFLARE_ZONES into {zone_id: domain} mapping."""
        if not self.CLOUDFLARE_ZONES:
            return {}
        result = {}
        for pair in self.CLOUDFLARE_ZONES.split(","):
            pair = pair.strip()
            if ":" in pair:
                zone_id, domain = pair.split(":", 1)
                result[zone_id.strip()] = domain.strip()
        return result

    @property
    def domain_zone_map(self) -> dict[str, str]:
        """Reverse mapping: {domain: zone_id}."""
        return {v: k for k, v in self.cloudflare_zone_map.items()}

    # ── Stripe ───────────────────────────────────────────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_CURRENCY: str = "inr"

    PAYMENT_PROVIDER: str = "test"  # "stripe" or "test"

    # ── Email ────────────────────────────────────────────────────────────
    EMAIL_PROVIDER: str = "console"
    EMAIL_FROM_ADDRESS: str = "noreply@example.com"
    EMAIL_FROM_NAME: str = "Evocation"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True

    SENDGRID_API_KEY: str = ""

    # ── Wallet ───────────────────────────────────────────────────────────
    WALLET_MIN_TOPUP_PAISE: int = 6000  # ₹60
    WALLET_MAX_TOPUP_PAISE: int = 100000  # ₹1000
    WALLET_FIRST_FUNDING_MIN_PAISE: int = 6000  # ₹60

    # ── Subscription ─────────────────────────────────────────────────────
    GRACE_PERIOD_DAYS: int = 5
    RENAME_COOLDOWN_HOURS: int = 24
    CHECKOUT_RESERVATION_MINUTES: int = 15

    # ── Background Jobs ──────────────────────────────────────────────────
    SCHEDULER_ENABLED: bool = True
    EXPIRY_CHECK_INTERVAL_MINUTES: int = 60
    RENEWAL_CHECK_INTERVAL_MINUTES: int = 60

    # ── Logging ──────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ── Rate Limiting ────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5

    # ── Admin ────────────────────────────────────────────────────────────
    ADMIN_INITIAL_EMAIL: str = "admin@example.com"
    ADMIN_INITIAL_PASSWORD: str = ""

    # ── Backup ───────────────────────────────────────────────────────────
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_ENCRYPTION_KEY: str = ""

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def ENVIRONMENT(self) -> str:
        return self.APP_ENV

    @property
    def APP_URL(self) -> str:
        return self.PUBLIC_SITE_URL

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
