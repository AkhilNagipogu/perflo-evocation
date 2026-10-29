"""
Customer wallet balance and transaction ledger API routes.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.providers.payment import PaymentService
from app.schemas.wallet import (
    TransactionListResponse,
    TransactionResponse,
    WalletResponse,
    WalletSummaryResponse,
    WalletTopUpRequest,
)
from app.services.wallet_service import WalletService

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("", response_model=WalletResponse)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve customer wallet balance and funding status."""
    service = WalletService(db)
    wallet = await service.get_wallet(current_user.id)
    return WalletResponse(
        id=wallet.id,
        balance_paise=wallet.balance_paise,
        balance_display=f"₹{wallet.balance_paise / 100:.2f}",
        has_been_funded=wallet.has_been_funded,
        created_at=wallet.created_at,
    )


@router.post("/topup")
async def topup_wallet(
    data: WalletTopUpRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Initiate a wallet funding session.
    Validates minimum first-time funding (₹60) and bounds, then creates payment order.
    """
    payment_service = PaymentService(db)
    success_url = f"{settings.APP_URL}/dashboard/billing?payment=success&order_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.APP_URL}/dashboard/billing?payment=cancelled"

    try:
        session_data = await payment_service.create_topup_order(
            user_id=current_user.id,
            amount_paise=data.amount_paise,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        await db.commit()
        return session_data
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating top-up order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve immutable transaction ledger entries for current customer."""
    service = WalletService(db)
    skip = (page - 1) * page_size
    transactions, total = await service.get_transactions(
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
    )
    items = [
        TransactionResponse(
            id=tx.id,
            reference_id=tx.reference_id,
            transaction_type=tx.transaction_type.value,
            status=tx.status.value,
            amount_paise=tx.amount_paise,
            balance_after_paise=tx.balance_after_paise,
            description=tx.description,
            rental_id=tx.rental_id,
            payment_order_id=tx.payment_order_id,
            created_at=tx.created_at,
        )
        for tx in transactions
    ]
    return TransactionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/summary", response_model=WalletSummaryResponse)
async def get_wallet_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve monthly wallet metrics (spending, funding) and recent transactions."""
    service = WalletService(db)
    summary = await service.get_monthly_summary(current_user.id)
    recent = [
        TransactionResponse(
            id=tx.id,
            reference_id=tx.reference_id,
            transaction_type=tx.transaction_type.value,
            status=tx.status.value,
            amount_paise=tx.amount_paise,
            balance_after_paise=tx.balance_after_paise,
            description=tx.description,
            rental_id=tx.rental_id,
            payment_order_id=tx.payment_order_id,
            created_at=tx.created_at,
        )
        for tx in summary["recent_transactions"]
    ]
    return WalletSummaryResponse(
        balance_paise=summary["balance_paise"],
        balance_display=f"₹{summary['balance_paise'] / 100:.2f}",
        month_spending_paise=summary["month_spending_paise"],
        month_funding_paise=summary["month_funding_paise"],
        recent_transactions=recent,
    )
