"""
Tests for authentication, registration, login, and profile operations.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test standard customer registration."""
    payload = {
        "email": "newcustomer@example.com",
        "username": "newcustomer",
        "password": "StrongPassword123!",
        "full_name": "New Customer",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newcustomer@example.com"
    assert data["username"] == "newcustomer"
    assert data["is_active"] is True
    assert data["is_email_verified"] is False


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    """Registration with existing email must fail."""
    payload = {
        "email": test_user.email,
        "username": "differentusername",
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, test_user):
    """Registration with existing username must fail."""
    payload = {
        "email": "anotheremail@example.com",
        "username": test_user.username,
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already taken" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Registration with weak password without digits/uppercase must fail validation."""
    payload = {
        "email": "weak@example.com",
        "username": "weakuser",
        "password": "password",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Successful login returns access and refresh JWTs."""
    payload = {
        "email": test_user.email,
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_user):
    """Login with invalid password returns 401."""
    payload = {
        "email": test_user.email,
        "password": "WrongPassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers):
    """Protected /auth/me returns current user info."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
