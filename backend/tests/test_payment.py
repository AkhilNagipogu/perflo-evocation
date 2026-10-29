"""
Tests for payment provider isolation, test provider blocking, and webhook handling.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.wallet import Wallet
from app.providers.payment import get_payment_provider
from app.services.wallet_service import WalletService


def test_test_provider_blocked_in_production(monkeypatch):
    """The test payment provider MUST throw an error if attempted in production."""
    settings = get_settings()
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "PAYMENT_PROVIDER", "test")

    with pytest.raises(RuntimeError, match="production"):
        get_payment_provider()


@pytest.mark.asyncio
async def test_confirm_test_payment_flow(
    client: AsyncClient, db_session: AsyncSession, test_user, auth_headers
):
    """In development/test environment, confirm-test creates wallet balance."""
    # 1. Initiate top-up for ₹100 (10000 paise)
    topup_res = await client.post(
        "/api/v1/wallet/topup",
        headers=auth_headers,
        json={"amount_paise": 10000},
    )
    assert topup_res.status_code == 200
    order_id = topup_res.json()["order_id"]

    # 2. Confirm test payment
    confirm_res = await client.post(
        "/api/v1/payments/confirm-test",
        headers=auth_headers,
        json={"order_id": order_id},
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "completed"

    # 3. Check wallet balance
    wallet_res = await client.get("/api/v1/wallet", headers=auth_headers)
    assert wallet_res.status_code == 200
    assert wallet_res.json()["balance_paise"] == 10000
