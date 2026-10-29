"""
Tests for administrator authentication, role isolation, and administrative controls.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_login_success(client: AsyncClient, test_admin):
    """Admin login with valid credentials succeeds."""
    payload = {
        "email": test_admin.email,
        "password": "AdminSecure123!",
    }
    response = await client.post("/api/v1/admin/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_customer_cannot_access_admin_routes(client: AsyncClient, auth_headers):
    """Regular customer access token must be rejected with 403 on admin routes."""
    response = await client.get("/api/v1/admin/stats", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_get_stats(client: AsyncClient, admin_auth_headers):
    """Admin can fetch aggregate dashboard stats."""
    response = await client.get("/api/v1/admin/stats", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_rentals" in data
    assert "total_wallet_balance_paise" in data


@pytest.mark.asyncio
async def test_admin_user_suspend(client: AsyncClient, admin_auth_headers, test_user):
    """Admin can suspend a customer account."""
    payload = {
        "action": "suspend",
        "reason": "Violation of terms",
    }
    response = await client.post(
        f"/api/v1/admin/users/{test_user.id}/manage",
        headers=admin_auth_headers,
        json=payload,
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_admin_wallet_adjustment(client: AsyncClient, admin_auth_headers, test_user):
    """Admin can adjust user wallet with an audit reason."""
    payload = {
        "amount_paise": 5000,
        "reason": "Promotional bonus credit",
    }
    response = await client.post(
        f"/api/v1/admin/users/{test_user.id}/wallet-adjust",
        headers=admin_auth_headers,
        json=payload,
    )
    assert response.status_code == 200
    assert response.json()["amount_paise"] == 5000
    assert response.json()["balance_after_paise"] == 5000
