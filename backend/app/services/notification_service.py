"""
Notification service — manages in-app notifications and coordinates with email service.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.providers.email import EmailService

logger = logging.getLogger(__name__)


class NotificationService:
    """Manages notifications for users."""

    def __init__(self, db: AsyncSession, email_service: Optional[EmailService] = None):
        self.db = db
        self.email_service = email_service or EmailService()

    async def create_notification(
        self,
        user_id: uuid.UUID,
        category: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
    ) -> Notification:
        """Create an in-app notification for a user."""
        notification = Notification(
            user_id=user_id,
            category=category,
            title=title,
            message=message,
            action_url=action_url,
            action_label=action_label,
            is_read=False,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_user_notifications(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
    ) -> tuple[list[Notification], int]:
        """Fetch paginated notifications for a user."""
        stmt = select(Notification).where(Notification.user_id == user_id)
        count_stmt = select(func.count(Notification.id)).where(Notification.user_id == user_id)

        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
            count_stmt = count_stmt.where(Notification.is_read.is_(False))

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        notifications = list(res.scalars().all())

        return notifications, total

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Get count of unread notifications for a user."""
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one()

    async def mark_as_read(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Notification]:
        """Mark a single notification as read."""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        res = await self.db.execute(stmt)
        notif = res.scalars().first()
        if not notif:
            return None

        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        await self.db.flush()
        return notif

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """Mark all unread notifications for a user as read."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=now)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount
