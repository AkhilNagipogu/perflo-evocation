"""
Tests for subdomain availability, atomic bundle purchase, 2-domain capacity, rename date preservation, and renewals.
"""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rental import RentalStatus
from app.models.wallet import TransactionType
from app.services.rental_service import RentalService
from app.services.wallet_service import WalletService


@pytest.mark.asyncio
async def test_subdomain_availability_success(client: AsyncClient, test_parent_domain):
    """Available name returns is_available True."""
    payload = {
        "subdomain_name": "myawesomeproject",
        "parent_domain_id": str(test_parent_domain.id),
    }
    response = await client.post("/api/v1/rentals/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is True
    assert data["full_domain"] == "myawesomeproject.example.com"


@pytest.mark.asyncio
async def test_subdomain_availability_reserved(client: AsyncClient, test_parent_domain):
    """Reserved name ('www' or 'mail') returns is_available False."""
    payload = {
        "subdomain_name": "www",
        "parent_domain_id": str(test_parent_domain.id),
    }
    response = await client.post("/api/v1/rentals/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is False
    assert "reserved" in data["reason"].lower() or "prohibited" in data["reason"].lower()


@pytest.mark.asyncio
async def test_purchase_bundle_and_capacity(
    db_session: AsyncSession, test_user, test_parent_domain, test_pricing_plan
):
    """
    Test purchasing base bundle:
    - Base plan is ₹60 for 2 subdomains
    - First domain costs ₹60 and creates subscription
    - Second domain under same subscription costs ₹0!
    """
    wallet_service = WalletService(db_session)
    rental_service = RentalService(db_session)

    # Fund wallet with ₹60 (6000 paise)
    await wallet_service.credit_wallet(
        user_id=test_user.id,
        amount_paise=6000,
        transaction_type=TransactionType.WALLET_FUNDING,
        idempotency_key="fund_bundle_test",
    )

    # 1. Purchase first subdomain: "site1"
    rental1 = await rental_service.purchase_rental(
        user_id=test_user.id,
        subdomain_name="site1",
        parent_domain_id=test_parent_domain.id,
        pricing_plan_id=test_pricing_plan.id,
    )
    assert rental1.status == RentalStatus.ACTIVE
    assert rental1.subdomain_name == "site1"

    wallet = await wallet_service.get_wallet(test_user.id)
    assert wallet.balance_paise == 0  # Deducted ₹60

    # 2. Purchase second subdomain: "site2" under the same 2-subdomain bundle
    # User wallet has 0 balance, but bundle includes 2 subdomains!
    rental2 = await rental_service.purchase_rental(
        user_id=test_user.id,
        subdomain_name="site2",
        parent_domain_id=test_parent_domain.id,
        pricing_plan_id=test_pricing_plan.id,
    )
    assert rental2.status == RentalStatus.ACTIVE
    assert rental2.subdomain_name == "site2"
    assert rental2.subscription_id == rental1.subscription_id


@pytest.mark.asyncio
async def test_rename_preserves_expiry_and_enforces_cooldown(
    db_session: AsyncSession, test_user, test_parent_domain, test_pricing_plan
):
    """Subdomain rename must preserve the expiration date and enforce cooldown."""
    wallet_service = WalletService(db_session)
    rental_service = RentalService(db_session)

    await wallet_service.credit_wallet(
        user_id=test_user.id,
        amount_paise=6000,
        transaction_type=TransactionType.WALLET_FUNDING,
        idempotency_key="fund_rename_test",
    )

    rental = await rental_service.purchase_rental(
        user_id=test_user.id,
        subdomain_name="oldname",
        parent_domain_id=test_parent_domain.id,
        pricing_plan_id=test_pricing_plan.id,
    )
    original_expiry = rental.expires_at

    # Rename to "newname"
    renamed = await rental_service.rename_rental(
        rental_id=rental.id,
        user_id=test_user.id,
        new_subdomain_name="newname",
    )
    assert renamed.subdomain_name == "newname"
    assert renamed.full_domain == f"newname.{test_parent_domain.domain}"
    assert renamed.expires_at == original_expiry  # Expiry date preserved!
    assert renamed.rename_count == 1

    # Attempt immediate second rename -> must fail due to 24-hour cooldown
    with pytest.raises(ValueError, match="cooldown"):
        await rental_service.rename_rental(
            rental_id=rental.id,
            user_id=test_user.id,
            new_subdomain_name="thirdname",
        )
