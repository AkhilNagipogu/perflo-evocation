"""
Pytest configuration and shared fixtures using SQLite in-memory.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test environment
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///:memory:"
os.environ["PAYMENT_PROVIDER"] = "test"
os.environ["CLOUDFLARE_API_TOKEN"] = ""
os.environ["SCHEDULER_ENABLED"] = "false"

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.admin_user import AdminUser
from app.models.parent_domain import ParentDomain
from app.models.pricing import PricingPlan
from app.models.user import User
from app.models.wallet import Wallet

from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create event loop for session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_test_database():
    """Create all schema tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide isolated database session for a test."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client with database dependency override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_parent_domain(db_session: AsyncSession) -> ParentDomain:
    """Fixture creating a test parent root domain."""
    domain = ParentDomain(
        domain="example.com",
        cloudflare_zone_id="test_zone_123",
        description="Test Domain",
        is_active=True,
        reserved_names='["www", "mail", "api", "admin"]',
    )
    db_session.add(domain)
    await db_session.commit()
    await db_session.refresh(domain)
    return domain


@pytest_asyncio.fixture
async def test_pricing_plan(db_session: AsyncSession) -> PricingPlan:
    """Fixture creating standard ₹60 base plan."""
    plan = PricingPlan(
        name="Standard Subdomain Bundle",
        slug="base-bundle",
        description="2 subdomains for 1 year",
        price_paise=6000,
        billing_period_days=365,
        included_subdomains=2,
        is_active=True,
        is_base_plan=True,
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Fixture creating a verified customer with an initial empty wallet."""
    user = User(
        email="testuser@example.com",
        username="testuser",
        password_hash=hash_password("Password123!"),
        full_name="Test Customer",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    wallet = Wallet(user_id=user.id, balance_paise=0)
    db_session.add(wallet)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    """Authorization header with valid JWT for test user."""
    token = create_access_token({"sub": str(test_user.id), "type": "access"})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> AdminUser:
    """Fixture creating a test administrator."""
    admin = AdminUser(
        email="admin@example.com",
        username="admin",
        password_hash=hash_password("AdminSecure123!"),
        full_name="Admin User",
        role="super_admin",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def admin_auth_headers(test_admin: AdminUser) -> dict[str, str]:
    """Authorization header with valid admin JWT."""
    token = create_access_token({"sub": str(test_admin.id), "type": "access", "is_admin": True, "role": "super_admin"})
    return {"Authorization": f"Bearer {token}"}
