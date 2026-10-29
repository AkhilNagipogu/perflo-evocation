"""
APScheduler configuration for background cron tasks.
"""

from __future__ import annotations

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.jobs.expiry_job import process_expirations
from app.jobs.reminder_job import send_expiry_reminders
from app.jobs.renewal_job import process_auto_renewals
from app.jobs.reservation_cleanup import cleanup_expired_reservations

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler() -> AsyncIOScheduler:
    """Register and start all background jobs."""
    if scheduler.running:
        return scheduler

    # Check for expired rentals and grace period expiry every 10 minutes
    scheduler.add_job(
        process_expirations,
        trigger=IntervalTrigger(minutes=10),
        id="process_expirations",
        name="Process Rental Expirations & Grace Periods",
        replace_existing=True,
    )

    # Clean up temporary checkout reservations every 5 minutes
    scheduler.add_job(
        cleanup_expired_reservations,
        trigger=IntervalTrigger(minutes=5),
        id="cleanup_reservations",
        name="Cleanup Expired Reservations",
        replace_existing=True,
    )

    # Process auto-renewals every 1 hour
    scheduler.add_job(
        process_auto_renewals,
        trigger=IntervalTrigger(hours=1),
        id="process_auto_renewals",
        name="Process Auto-Renewals",
        replace_existing=True,
    )

    # Send upcoming expiration reminders every 6 hours
    scheduler.add_job(
        send_expiry_reminders,
        trigger=IntervalTrigger(hours=6),
        id="send_expiry_reminders",
        name="Send Expiry Reminders",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("APScheduler background jobs started successfully")
    return scheduler


def shutdown_scheduler() -> None:
    """Gracefully terminate background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
