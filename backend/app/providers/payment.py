"""
Payment provider abstraction and Stripe implementation.

Separates payment processing from wallet crediting.
Never credits a wallet based on browser redirects alone.
"""

from __future__ import annotations

import abc
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import generate_reference_id, generate_secure_token
from app.models.payment import PaymentOrder, PaymentStatus
from app.models.wallet import TransactionType
from app.services.wallet_service import WalletService

settings = get_settings()
logger = logging.getLogger(__name__)


class PaymentProviderBase(abc.ABC):
    """Abstract payment provider interface."""

    @abc.abstractmethod
    async def create_checkout_session(
        self,
        amount_paise: int,
        currency: str,
        user_id: str,
        order_id: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a checkout session. Returns provider-specific data."""
        ...

    @abc.abstractmethod
    async def verify_webhook(
        self, payload: bytes, signature: str
    ) -> dict[str, Any]:
        """Verify and parse a webhook event."""
        ...

    @abc.abstractmethod
    async def get_payment_status(self, provider_id: str) -> str:
        """Check payment status with provider."""
        ...


class StripeProvider(PaymentProviderBase):
    """
    Real Stripe integration.
    Requires STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET.
    """

    def __init__(self):
        self.secret_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self._stripe = None

    @property
    def is_configured(self) -> bool:
        return bool(self.secret_key and self.secret_key.startswith("sk_"))

    def _get_stripe(self):
        if self._stripe is None:
            import stripe
            stripe.api_key = self.secret_key
            self._stripe = stripe
        return self._stripe

    async def create_checkout_session(
        self,
        amount_paise: int,
        currency: str,
        user_id: str,
        order_id: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        stripe = self._get_stripe()
        meta = {
            "user_id": user_id,
            "order_id": order_id,
            **(metadata or {}),
        }

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {
                        "name": "Evocation Wallet Top-Up",
                        "description": f"Add ₹{amount_paise // 100} to your wallet",
                    },
                    "unit_amount": amount_paise,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=meta,
            idempotency_key=order_id,
        )

        return {
            "session_id": session.id,
            "url": session.url,
            "provider_order_id": session.id,
        }

    async def verify_webhook(
        self, payload: bytes, signature: str
    ) -> dict[str, Any]:
        stripe = self._get_stripe()
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return {
                "event_id": event.id,
                "event_type": event.type,
                "data": event.data.object,
            }
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid webhook signature")

    async def get_payment_status(self, provider_id: str) -> str:
        stripe = self._get_stripe()
        session = stripe.checkout.Session.retrieve(provider_id)
        return session.payment_status


class TestProvider(PaymentProviderBase):
    """
    Test payment provider for development.
    Clearly identified — never used in production.
    """

    async def create_checkout_session(
        self,
        amount_paise: int,
        currency: str,
        user_id: str,
        order_id: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        test_session_id = f"test_session_{generate_secure_token(16)}"
        logger.warning(
            f"TEST PAYMENT: Creating test checkout for ₹{amount_paise // 100} "
            f"(order: {order_id}). This is NOT a real payment."
        )
        return {
            "session_id": test_session_id,
            "url": f"{success_url}?session_id={test_session_id}",
            "provider_order_id": test_session_id,
            "is_test": True,
        }

    async def verify_webhook(
        self, payload: bytes, signature: str
    ) -> dict[str, Any]:
        import json
        data = json.loads(payload)
        return {
            "event_id": f"test_evt_{generate_secure_token(8)}",
            "event_type": data.get("type", "checkout.session.completed"),
            "data": data.get("data", {}),
        }

    async def get_payment_status(self, provider_id: str) -> str:
        return "paid"


def get_payment_provider() -> PaymentProviderBase:
    """Get the configured payment provider."""
    if settings.PAYMENT_PROVIDER == "stripe":
        provider = StripeProvider()
        if not provider.is_configured:
            logger.error(
                "Stripe is selected but not configured. "
                "Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET."
            )
            raise RuntimeError("Stripe payment provider is not configured")
        return provider
    elif settings.PAYMENT_PROVIDER == "test":
        if settings.is_production:
            raise RuntimeError(
                "Test payment provider cannot be used in production"
            )
        logger.warning("Using TEST payment provider. Not for production use.")
        return TestProvider()
    else:
        raise RuntimeError(f"Unknown payment provider: {settings.PAYMENT_PROVIDER}")


class PaymentService:
    """Orchestrates payment orders and wallet crediting."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = get_payment_provider()
        self.wallet_service = WalletService(db)

    async def create_topup_order(
        self,
        user_id: uuid.UUID,
        amount_paise: int,
        success_url: str,
        cancel_url: str,
    ) -> dict[str, Any]:
        """Create a payment order for wallet top-up."""
        # Validate amount
        wallet = await self.wallet_service.get_wallet(user_id)
        await self.wallet_service.validate_topup_amount(amount_paise, wallet)

        # Create payment order record
        idempotency_key = generate_reference_id("PAY")
        order = PaymentOrder(
            user_id=user_id,
            wallet_id=wallet.id,
            provider=settings.PAYMENT_PROVIDER,
            amount_paise=amount_paise,
            currency=settings.STRIPE_CURRENCY,
            status=PaymentStatus.CREATED,
            idempotency_key=idempotency_key,
            description=f"Wallet top-up: ₹{amount_paise // 100}",
        )
        self.db.add(order)
        await self.db.flush()

        # Create checkout with provider
        try:
            result = await self.provider.create_checkout_session(
                amount_paise=amount_paise,
                currency=settings.STRIPE_CURRENCY,
                user_id=str(user_id),
                order_id=str(order.id),
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"wallet_id": str(wallet.id)},
            )

            order.provider_order_id = result.get("provider_order_id")
            order.status = PaymentStatus.PENDING
            await self.db.flush()

            return {
                "order_id": str(order.id),
                "checkout_url": result.get("url"),
                "session_id": result.get("session_id"),
                "is_test": result.get("is_test", False),
            }

        except Exception as e:
            order.status = PaymentStatus.FAILED
            await self.db.flush()
            raise

    async def handle_payment_success(
        self,
        order_id: uuid.UUID,
        provider_payment_id: str | None = None,
        webhook_event_id: str | None = None,
    ) -> PaymentOrder:
        """
        Handle successful payment — credit wallet.
        Called from webhook handler, NOT from success redirect.
        Uses idempotency to prevent double-crediting.
        """
        result = await self.db.execute(
            select(PaymentOrder).where(PaymentOrder.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError("Payment order not found")

        # Idempotency — already completed
        if order.status == PaymentStatus.COMPLETED:
            logger.info(f"Payment order {order_id} already completed (idempotent)")
            return order

        if order.status not in (PaymentStatus.CREATED, PaymentStatus.PENDING):
            raise ValueError(f"Payment order in unexpected state: {order.status}")

        # Update order
        order.status = PaymentStatus.COMPLETED
        order.provider_payment_id = provider_payment_id
        order.webhook_received_at = datetime.now(timezone.utc)
        order.webhook_event_id = webhook_event_id

        # Credit wallet
        await self.wallet_service.credit_wallet(
            user_id=order.user_id,
            amount_paise=order.amount_paise,
            transaction_type=TransactionType.WALLET_FUNDING,
            description=f"Wallet top-up: ₹{order.amount_paise // 100}",
            payment_order_id=order.id,
            idempotency_key=f"wallet-credit-{order.id}",
        )

        await self.db.flush()
        return order

    async def handle_test_payment_confirmation(
        self,
        order_id: uuid.UUID,
    ) -> PaymentOrder:
        """
        Confirm a test payment (development only).
        Never available in production.
        """
        if settings.is_production:
            raise RuntimeError("Test payment confirmation not available in production")

        return await self.handle_payment_success(
            order_id=order_id,
            provider_payment_id=f"test_pi_{generate_secure_token(8)}",
            webhook_event_id=f"test_evt_{generate_secure_token(8)}",
        )
