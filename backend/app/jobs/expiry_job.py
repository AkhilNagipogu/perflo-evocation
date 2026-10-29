"""
Background job to process rental expirations, grace period transitions, and name releases.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.models.rental import Rental, RentalStatus
from app.models.user import User
from app.providers.email import EmailService
from app.services.dns_service import DnsService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
settings = get_settings()


async def process_expirations() -> dict[str, int]:
    """
    Check for expired rentals and rentals whose grace period has lapsed.
    Enforces strict 5-day grace period.
    """
    now = datetime.now(timezone.utc)
    expired_count = 0
    released_count = 0

    email_service = EmailService()

    async with async_session_factory() as db:
        dns_service = DnsService(db)
        notif_service = NotificationService(db, email_service)

        try:
            # Step 1: Active rentals that have expired -> move to EXPIRED / GRACE_PERIOD
            stmt_active_expired = (
                select(Rental)
                .where(
                    Rental.status == RentalStatus.ACTIVE,
                    Rental.expires_at <= now,
                )
                .options(selectinload(Rental.user), selectinload(Rental.parent_domain))
            )
            res = await db.execute(stmt_active_expired)
            expired_rentals = list(res.scalars().all())

            for rental in expired_rentals:
                rental.status = RentalStatus.EXPIRED
                if not rental.grace_period_ends_at:
                    base = rental.expires_at or now
                    rental.grace_period_ends_at = base + timedelta(days=settings.GRACE_PERIOD_DAYS)

                # Suspend DNS records in Cloudflare during grace period
                await dns_service.suspend_all_rental_records(rental.id)

                # In-app notification
                await notif_service.create_notification(
                    user_id=rental.user_id,
                    category="rental_expired",
                    title=f"Subdomain {rental.full_domain} has expired",
                    message=(
                        f"Your rental for {rental.full_domain} has entered the 5-day grace period. "
                        f"Please renew before {rental.grace_period_ends_at.strftime('%Y-%m-%d %H:%M UTC')} "
                        f"to prevent the subdomain from being permanently released."
                    ),
                    action_url=f"/dashboard/subdomains",
                    action_label="Renew Now",
                )

                # Email notification
                if rental.user and rental.user.email and rental.user.notify_expiry_reminders:
                    days_left = max(1, (rental.grace_period_ends_at - now).days)
                    await email_service.send_grace_period_notice(
                        to=rental.user.email,
                        subdomain_name=rental.full_domain,
                        days_left=days_left,
                    )

                expired_count += 1

            # Step 2: Expired rentals whose grace period has ended -> move to RELEASED
            stmt_grace_ended = (
                select(Rental)
                .where(
                    Rental.status.in_([RentalStatus.EXPIRED, RentalStatus.GRACE_PERIOD]),
                    Rental.grace_period_ends_at <= now,
                )
                .options(selectinload(Rental.user))
            )
            res_grace = await db.execute(stmt_grace_ended)
            released_rentals = list(res_grace.scalars().all())

            for rental in released_rentals:
                rental.status = RentalStatus.RELEASED

                # Make sure all DNS records are cleaned up
                await dns_service.suspend_all_rental_records(rental.id)

                await notif_service.create_notification(
                    user_id=rental.user_id,
                    category="rental_released",
                    title=f"Subdomain {rental.full_domain} has been released",
                    message=(
                        f"The 5-day grace period for {rental.full_domain} has ended. "
                        f"The subdomain is now released and available for registration by other users."
                    ),
                    action_url=f"/search",
                    action_label="Browse Subdomains",
                )

                released_count += 1

            await db.commit()
            if expired_count > 0 or released_count > 0:
                logger.info(
                    f"Processed expirations: {expired_count} moved to grace period, {released_count} released"
                )

        except Exception as e:
            await db.rollback()
            logger.error(f"Error in process_expirations job: {e}")

    return {"expired_count": expired_count, "released_count": released_count}
