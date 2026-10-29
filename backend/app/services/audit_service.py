"""
Audit service — records immutable audit log entries for key security and business events.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for appending and querying immutable audit logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        action: str,
        resource_type: str,
        description: str,
        actor_type: str = "system",
        actor_id: Optional[uuid.UUID] = None,
        actor_email: Optional[str] = None,
        actor_ip: Optional[str] = None,
        resource_id: Optional[str] = None,
        details_before: Optional[dict[str, Any]] = None,
        details_after: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        """Create an immutable audit log entry."""
        log_entry = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_ip=actor_ip,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            description=description,
            details_before=json.dumps(details_before) if details_before else None,
            details_after=json.dumps(details_after) if details_after else None,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        self.db.add(log_entry)
        await self.db.flush()
        return log_entry

    async def list_logs(
        self,
        skip: int = 0,
        limit: int = 50,
        actor_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
    ) -> tuple[list[AuditLog], int]:
        """Query audit logs with filtering and pagination."""
        stmt = select(AuditLog)
        count_stmt = select(func.count(AuditLog.id))

        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
            count_stmt = count_stmt.where(AuditLog.actor_id == actor_id)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
            count_stmt = count_stmt.where(AuditLog.resource_type == resource_type)
        if action:
            stmt = stmt.where(AuditLog.action == action)
            count_stmt = count_stmt.where(AuditLog.action == action)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        logs = list(res.scalars().all())

        return logs, total
