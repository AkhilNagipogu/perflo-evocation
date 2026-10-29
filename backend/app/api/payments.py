"""
Payment gateway and webhook API endpoints.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.providers.email import EmailService
from app.providers.payment import PaymentService, get_payment_provider

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/confirm-test")
async def confirm_test_payment(
    order_id: uuid.UUID = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Development-only endpoint to confirm a test payment and credit wallet.
    HARD BLOCKED in production environment.
    """
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test payment confirmation is disabled in production",
        )

    payment_service = PaymentService(db)
    try:
        order = await payment_service.handle_test_payment_confirmation(order_id)
        await db.commit()

        # Send email confirmation
        email_service = EmailService()
        await email_service.send_wallet_funded(
            to=current_user.email,
            amount_inr=f"₹{order.amount_paise / 100:.2f}",
            new_balance_inr="",
        )

        return {
            "success": True,
            "order_id": str(order.id),
            "amount_paise": order.amount_paise,
            "status": order.status.value,
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Test payment confirmation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Stripe webhook listener.
    Verifies cryptographic signature and credits user wallet idempotently upon checkout.session.completed.
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header",
        )

    provider = get_payment_provider()
    payload = await request.body()

    try:
        event = await provider.verify_webhook(payload, stripe_signature)
    except Exception as e:
        logger.warning(f"Stripe webhook signature verification failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

    event_type = event.get("type")
    if event_type == "checkout.session.completed":
        session = event.get("data", {}).get("object", {})
        metadata = session.get("metadata", {})
        order_id_str = metadata.get("order_id")

        if order_id_str:
            payment_service = PaymentService(db)
            try:
                order_id = uuid.UUID(order_id_str)
                provider_payment_id = session.get("payment_intent") or session.get("id")
                await payment_service.handle_payment_success(
                    order_id=order_id,
                    provider_payment_id=provider_payment_id,
                    webhook_event_id=event.get("id"),
                )
                await db.commit()
                logger.info(f"Successfully processed payment for order {order_id} via Stripe webhook")
            except Exception as e:
                await db.rollback()
                logger.error(f"Error fulfilling Stripe checkout session {order_id_str}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Processing error")

    return {"status": "success"}
