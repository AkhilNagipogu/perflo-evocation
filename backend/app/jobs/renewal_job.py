"""
Background job to process auto-renewals for active rentals.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory
from app.models.rental import Rental, RentalStatus
from app.providers.email import EmailService
from app.services.notification_service import NotificationService
from app.services.rental_service import RentalService

logger = logging.getLogger(__name__)


async def process_auto_renewals() -> int:
    """
    Find active rentals configured for auto-renewal expiring within 48 hours.
    Attempt wallet debit and extension.
    """
    now = datetime.now(timezone.utc)
    target_threshold = now + timedelta(days=2)
    renewed_count = 0

    email_service = EmailService()

    async with async_session_factory() as db:
        rental_service = RentalService(db)
        notif_service = NotificationService(db, email_service)

        try:
            stmt = (
                select(Rental)
                .where(
                    Rental.status == RentalStatus.ACTIVE,
                    Rental.auto_renew.is_(True),
                    Rental.expires_at <= target_threshold,
                    Rental.expires_at > now,
                )
                .options(selectinload(Rental.user))
            )
            res = await db.execute(stmt)
            candidates = list(res.scalars().all())

            for rental in candidates:
                try:
                    await rental_service.renew_rental(
                        rental_id=rental.id,
                        user_id=rental.user_id,
                    )
                    await db.commit()
                    renewed_count += 1
                    logger.info(f"Auto-renewed rental {rental.full_domain} successfully")

                    await notif_service.create_notification(
                        user_id=rental.user_id,
                        category="auto_renew_success",
                        title=f"Subdomain {rental.full_domain} auto-renewed",
                        message=f"Your subscription for {rental.full_domain} has been automatically renewed for 1 year.",
                        action_url="/dashboard/subdomains",
                        action_label="View Subdomain",
                    )

                except ValueError as ve:
                    # Likely insufficient balance
                    await db.rollback()
                    logger.warning(
                        f"Auto-renewal failed for {rental.full_domain} (user {rental.user_id}): {ve}"
                    )
                    await notif_service.create_notification(
                        user_id=rental.user_id,
                        category="auto_renew_failed",
                        title=f"Auto-renewal failed for {rental.full_domain}",
                        message=(
                            f"Auto-renewal failed because of insufficient wallet funds. "
                            f"Please top up your wallet before {rental.expires_at.strftime('%Y-%m-%d')} to keep your subdomain."
                        ),
                        action_url="/dashboard/billing",
                        action_label="Top Up Wallet",
                    )

        except Exception as e:
            await db.rollback()
            logger.error(f"Error in process_auto_renewals: {e}")

    return renewed_count
