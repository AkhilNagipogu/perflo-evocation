"""
Tests for wallet balance, funding bounds, first-funding minimum, and ledger idempotency.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import TransactionType
from app.services.wallet_service import WalletService


@pytest.mark.asyncio
async def test_get_wallet_initial(client: AsyncClient, auth_headers):
    """Initial wallet should have 0 balance and has_been_funded False."""
    response = await client.get("/api/v1/wallet", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["balance_paise"] == 0
    assert data["has_been_funded"] is False


@pytest.mark.asyncio
async def test_first_funding_minimum_enforcement(client: AsyncClient, auth_headers):
    """First-time wallet funding must be at least ₹60 (6000 paise). Below ₹60 must fail."""
    # Attempting ₹30 (3000 paise)
    response = await client.post(
        "/api/v1/wallet/topup",
        headers=auth_headers,
        json={"amount_paise": 3000},
    )
    assert response.status_code == 400
    assert "minimum first-time" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_max_funding_enforcement(client: AsyncClient, auth_headers):
    """Funding above maximum limit of ₹1000 (100000 paise) must fail."""
    response = await client.post(
        "/api/v1/wallet/topup",
        headers=auth_headers,
        json={"amount_paise": 200000},
    )
    assert response.status_code == 400
    assert "maximum" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_wallet_credit_and_debit(db_session: AsyncSession, test_user):
    """Test credit, debit, and balance integrity using WalletService."""
    service = WalletService(db_session)

    # 1. Credit ₹100 (10000 paise)
    tx_credit = await service.credit_wallet(
        user_id=test_user.id,
        amount_paise=10000,
        transaction_type=TransactionType.WALLET_FUNDING,
        idempotency_key="tx_credit_1",
        description="Test credit",
    )
    assert tx_credit.balance_after_paise == 10000

    wallet = await service.get_wallet(test_user.id)
    assert wallet.balance_paise == 10000
    assert wallet.has_been_funded is True

    # 2. Debit ₹60 (6000 paise)
    tx_debit = await service.debit_wallet(
        user_id=test_user.id,
        amount_paise=6000,
        transaction_type=TransactionType.RENTAL_PURCHASE,
        idempotency_key="tx_debit_1",
        description="Test debit",
    )
    assert tx_debit.balance_after_paise == 4000

    wallet = await service.get_wallet(test_user.id)
    assert wallet.balance_paise == 4000


@pytest.mark.asyncio
async def test_wallet_debit_insufficient_funds(db_session: AsyncSession, test_user):
    """Debit exceeding balance must raise ValueError."""
    service = WalletService(db_session)
    with pytest.raises(ValueError, match="Insufficient"):
        await service.debit_wallet(
            user_id=test_user.id,
            amount_paise=5000,
            transaction_type=TransactionType.RENTAL_PURCHASE,
            description="Insufficient funds debit test",
            idempotency_key="insufficient_debit",
        )


@pytest.mark.asyncio
async def test_wallet_credit_idempotency(db_session: AsyncSession, test_user):
    """Repeated calls with the same idempotency key must return the existing transaction without double-crediting."""
    service = WalletService(db_session)

    tx1 = await service.credit_wallet(
        user_id=test_user.id,
        amount_paise=6000,
        transaction_type=TransactionType.WALLET_FUNDING,
        description="Idempotent test credit",
        idempotency_key="idempotent_test_key",
    )
    tx2 = await service.credit_wallet(
        user_id=test_user.id,
        amount_paise=6000,
        transaction_type=TransactionType.WALLET_FUNDING,
        description="Idempotent test credit",
        idempotency_key="idempotent_test_key",
    )

    assert tx1.id == tx2.id
    wallet = await service.get_wallet(test_user.id)
    assert wallet.balance_paise == 6000  # NOT 12000!
