"""
DNS record management API routes.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_verified_user
from app.models.dns_record import DnsRecord
from app.models.rental import Rental
from app.models.user import User
from app.schemas.rental import (
    DnsRecordCreate,
    DnsRecordResponse,
    DnsRecordUpdate,
)
from app.services.dns_service import DnsService, DnsValidationError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["DNS"])


def _to_dns_response(r: DnsRecord) -> DnsRecordResponse:
    return DnsRecordResponse(
        id=r.id,
        record_type=r.record_type.value,
        name=r.name,
        content=r.content,
        ttl=r.ttl,
        proxied=r.proxied,
        status=r.status.value,
        last_synced_at=r.last_synced_at,
    )


@router.get("/rentals/{rental_id}/dns", response_model=list[DnsRecordResponse])
async def list_dns_records(
    rental_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve all DNS records configured for a subdomain rental."""
    # Verify rental ownership
    rental_res = await db.execute(
        select(Rental).where(Rental.id == rental_id, Rental.user_id == current_user.id)
    )
    rental = rental_res.scalar_one_or_none()
    if not rental:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found")

    dns_service = DnsService(db)
    records = await dns_service.get_rental_records(rental_id)
    return [_to_dns_response(r) for r in records]


@router.post("/rentals/{rental_id}/dns", response_model=DnsRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_dns_record(
    rental_id: uuid.UUID,
    data: DnsRecordCreate,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new DNS record (A, AAAA, CNAME, TXT) synced to Cloudflare.
    Validates RFC syntax and verifies no CNAME collisions.
    """
    rental_res = await db.execute(
        select(Rental).where(Rental.id == rental_id, Rental.user_id == current_user.id)
    )
    rental = rental_res.scalar_one_or_none()
    if not rental:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found")

    dns_service = DnsService(db)
    try:
        record = await dns_service.create_record(rental, data)
        await db.commit()
        await db.refresh(record)
        return _to_dns_response(record)
    except DnsValidationError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating DNS record: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/dns/{record_id}", response_model=DnsRecordResponse)
async def update_dns_record(
    record_id: uuid.UUID,
    data: DnsRecordUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update content, TTL, or proxy status for an existing DNS record."""
    dns_service = DnsService(db)
    record = await dns_service.get_record_by_id(record_id)
    if not record or not record.rental or record.rental.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS record not found")

    try:
        updated = await dns_service.update_record(record, data)
        await db.commit()
        await db.refresh(updated)
        return _to_dns_response(updated)
    except DnsValidationError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/dns/{record_id}")
async def delete_dns_record(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete a DNS record from both Cloudflare and the platform database."""
    dns_service = DnsService(db)
    record = await dns_service.get_record_by_id(record_id)
    if not record or not record.rental or record.rental.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS record not found")

    try:
        await dns_service.delete_record(record)
        await db.commit()
        return {"message": "DNS record deleted successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting DNS record: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
