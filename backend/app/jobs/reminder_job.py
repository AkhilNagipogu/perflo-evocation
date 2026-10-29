"""
Background job to send upcoming expiration reminders (7 days, 3 days, 1 day).
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

logger = logging.getLogger(__name__)


async def send_expiry_reminders() -> int:
    """
    Scan for active rentals expiring in approximately 7 days, 3 days, or 1 day.
    Dispatch email and in-app reminders.
    """
    now = datetime.now(timezone.utc)
    reminders_sent = 0
    email_service = EmailService()

    # Intervals: (days, lower_bound_hours, upper_bound_hours)
    intervals = [
        (7, 24 * 7 - 12, 24 * 7 + 12),
        (3, 24 * 3 - 12, 24 * 3 + 12),
        (1, 24 * 1 - 12, 24 * 1 + 12),
    ]

    async with async_session_factory() as db:
        notif_service = NotificationService(db, email_service)

        try:
            for days, lower_h, upper_h in intervals:
                window_start = now + timedelta(hours=lower_h)
                window_end = now + timedelta(hours=upper_h)

                stmt = (
                    select(Rental)
                    .where(
                        Rental.status == RentalStatus.ACTIVE,
                        Rental.expires_at >= window_start,
                        Rental.expires_at <= window_end,
                    )
                    .options(selectinload(Rental.user))
                )
                res = await db.execute(stmt)
                rentals = list(res.scalars().all())

                for rental in rentals:
                    user = rental.user
                    if not user or not user.notify_expiry_reminders:
                        continue

                    # Send in-app notification
                    await notif_service.create_notification(
                        user_id=user.id,
                        category="expiry_reminder",
                        title=f"{rental.full_domain} expires in {days} day{'s' if days > 1 else ''}",
                        message=(
                            f"Your subdomain {rental.full_domain} is scheduled to expire on "
                            f"{rental.expires_at.strftime('%Y-%m-%d')}. Ensure your wallet is funded or renew now."
                        ),
                        action_url="/dashboard/subdomains",
                        action_label="Renew Now",
                    )

                    # Send email
                    if user.email:
                        await email_service.send_expiry_reminder(
                            to=user.email,
                            subdomain_name=rental.full_domain,
                            expiry_date=rental.expires_at.strftime("%B %d, %Y"),
                            days_remaining=days,
                        )

                    reminders_sent += 1

            await db.commit()
            if reminders_sent > 0:
                logger.info(f"Dispatched {reminders_sent} expiration reminder notification(s)")

        except Exception as e:
            await db.rollback()
            logger.error(f"Error in send_expiry_reminders job: {e}")

    return reminders_sent
