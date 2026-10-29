"""
Background job to clean up expired temporary checkout reservations.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.reservation import NameReservation

logger = logging.getLogger(__name__)


async def cleanup_expired_reservations() -> int:
    """Delete reservations where expires_at has passed."""
    now = datetime.now(timezone.utc)
    async with async_session_factory() as db:
        try:
            stmt = delete(NameReservation).where(NameReservation.expires_at <= now)
            result = await db.execute(stmt)
            await db.commit()
            count = result.rowcount
            if count > 0:
                logger.info(f"Cleaned up {count} expired name reservation(s)")
            return count
        except Exception as e:
            await db.rollback()
            logger.error(f"Error cleaning up expired reservations: {e}")
            return 0
