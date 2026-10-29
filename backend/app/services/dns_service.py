"""
DNS service — orchestrates DNS records between database and Cloudflare.
"""

from __future__ import annotations

import ipaddress
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.dns_record import DnsRecord, DnsRecordStatus, DnsRecordType
from app.models.parent_domain import ParentDomain
from app.models.rental import Rental, RentalStatus
from app.providers.cloudflare import CloudflareError, CloudflareProvider
from app.schemas.rental import DnsRecordCreate, DnsRecordUpdate

logger = logging.getLogger(__name__)
settings = get_settings()


class DnsValidationError(Exception):
    """Raised when DNS record content or name fails validation."""
    pass


class DnsService:
    """Manages DNS records for subdomain rentals."""

    def __init__(self, db: AsyncSession, cf_provider: Optional[CloudflareProvider] = None):
        self.db = db
        self.cf = cf_provider or CloudflareProvider()

    def validate_content(self, record_type: DnsRecordType, content: str) -> None:
        """Validate DNS record content based on record type."""
        content = content.strip()
        if record_type == DnsRecordType.A:
            try:
                ip = ipaddress.IPv4Address(content)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    logger.warning(f"DNS A record targets non-public IP: {content}")
            except ValueError:
                raise DnsValidationError(f"Invalid IPv4 address for A record: '{content}'")

        elif record_type == DnsRecordType.AAAA:
            try:
                ipaddress.IPv6Address(content)
            except ValueError:
                raise DnsValidationError(f"Invalid IPv6 address for AAAA record: '{content}'")

        elif record_type == DnsRecordType.CNAME:
            # Check domain format
            cname_pattern = r"^([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}$"
            if not re.match(cname_pattern, content.lower()) and not content.endswith("."):
                raise DnsValidationError(f"Invalid domain target for CNAME: '{content}'")

        elif record_type == DnsRecordType.TXT:
            if len(content) > 4096:
                raise DnsValidationError("TXT record content exceeds maximum length of 4096 characters")

    async def _get_parent_domain_zone_id(self, parent_domain_id: uuid.UUID) -> str:
        """Fetch the Cloudflare zone ID for the given parent domain."""
        stmt = select(ParentDomain).where(ParentDomain.id == parent_domain_id)
        result = await self.db.execute(stmt)
        parent = result.scalars().first()
        if not parent:
            raise ValueError("Parent domain not found")
        if parent.cloudflare_zone_id:
            return parent.cloudflare_zone_id
        # Fallback to config zone map
        return self.cf._get_zone_id(parent.domain)

    async def get_rental_records(self, rental_id: uuid.UUID) -> list[DnsRecord]:
        """Fetch all active/pending DNS records for a rental."""
        stmt = (
            select(DnsRecord)
            .where(
                DnsRecord.rental_id == rental_id,
                DnsRecord.status != DnsRecordStatus.DELETED,
            )
            .order_by(DnsRecord.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_record_by_id(self, record_id: uuid.UUID) -> Optional[DnsRecord]:
        """Fetch a specific DNS record by ID."""
        stmt = select(DnsRecord).where(DnsRecord.id == record_id).options(selectinload(DnsRecord.rental))
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_record(
        self,
        rental: Rental,
        data: DnsRecordCreate,
    ) -> DnsRecord:
        """
        Create a new DNS record for a rental, syncing to Cloudflare.
        """
        if rental.status != RentalStatus.ACTIVE:
            raise ValueError(f"Cannot manage DNS records when rental status is '{rental.status.value}'")

        rec_type = DnsRecordType(data.record_type.upper())
        self.validate_content(rec_type, data.content)

        # Full record name is the rental's full_domain
        record_name = rental.full_domain
        zone_id = await self._get_parent_domain_zone_id(rental.parent_domain_id)

        # Check for CNAME collision
        existing_records = await self.get_rental_records(rental.id)
        if rec_type == DnsRecordType.CNAME and existing_records:
            raise DnsValidationError("Cannot create a CNAME record when other records exist for this domain")
        if any(r.record_type == DnsRecordType.CNAME for r in existing_records):
            raise DnsValidationError("Cannot add additional records when a CNAME record exists")

        # Create record in DB
        db_record = DnsRecord(
            rental_id=rental.id,
            record_type=rec_type,
            name=record_name,
            content=data.content.strip(),
            ttl=data.ttl,
            proxied=data.proxied if rec_type in (DnsRecordType.A, DnsRecordType.AAAA, DnsRecordType.CNAME) else False,
            status=DnsRecordStatus.PENDING,
        )
        self.db.add(db_record)
        await self.db.flush()

        # Sync with Cloudflare if configured
        if self.cf.is_configured:
            try:
                cf_result = await self.cf.create_dns_record(
                    zone_id=zone_id,
                    record_type=rec_type.value,
                    name=record_name,
                    content=db_record.content,
                    ttl=db_record.ttl,
                    proxied=db_record.proxied,
                )
                db_record.cloudflare_record_id = cf_result["id"]
                db_record.status = DnsRecordStatus.ACTIVE
                db_record.last_synced_at = datetime.now(timezone.utc)
                db_record.last_error = None
            except CloudflareError as e:
                logger.error(f"Failed to create Cloudflare DNS record: {e}")
                db_record.status = DnsRecordStatus.FAILED
                db_record.last_error = str(e)
                db_record.retry_count += 1
        else:
            # Dev / test environment without Cloudflare
            logger.info("Cloudflare not configured — recording DNS record in simulated active state")
            db_record.status = DnsRecordStatus.ACTIVE
            db_record.cloudflare_record_id = f"sim_{uuid.uuid4().hex[:16]}"
            db_record.last_synced_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(db_record)
        return db_record

    async def update_record(
        self,
        record: DnsRecord,
        data: DnsRecordUpdate,
    ) -> DnsRecord:
        """Update an existing DNS record."""
        rental = record.rental
        if not rental:
            stmt = select(Rental).where(Rental.id == record.rental_id)
            res = await self.db.execute(stmt)
            rental = res.scalar_one()

        if rental.status != RentalStatus.ACTIVE:
            raise ValueError(f"Cannot manage DNS records when rental status is '{rental.status.value}'")

        new_content = data.content.strip() if data.content is not None else record.content
        new_ttl = data.ttl if data.ttl is not None else record.ttl
        new_proxied = data.proxied if data.proxied is not None else record.proxied

        if data.content is not None:
            self.validate_content(record.record_type, new_content)

        record.content = new_content
        record.ttl = new_ttl
        record.proxied = new_proxied if record.record_type in (DnsRecordType.A, DnsRecordType.AAAA, DnsRecordType.CNAME) else False

        if self.cf.is_configured and record.cloudflare_record_id and not record.cloudflare_record_id.startswith("sim_"):
            zone_id = await self._get_parent_domain_zone_id(rental.parent_domain_id)
            try:
                await self.cf.update_dns_record(
                    zone_id=zone_id,
                    record_id=record.cloudflare_record_id,
                    record_type=record.record_type.value,
                    name=record.name,
                    content=record.content,
                    ttl=record.ttl,
                    proxied=record.proxied,
                )
                record.status = DnsRecordStatus.ACTIVE
                record.last_synced_at = datetime.now(timezone.utc)
                record.last_error = None
            except CloudflareError as e:
                logger.error(f"Failed to update Cloudflare DNS record: {e}")
                record.status = DnsRecordStatus.FAILED
                record.last_error = str(e)
                record.retry_count += 1
        else:
            record.status = DnsRecordStatus.ACTIVE
            record.last_synced_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def delete_record(self, record: DnsRecord) -> None:
        """Delete a DNS record from Cloudflare and DB."""
        rental = record.rental
        if not rental:
            stmt = select(Rental).where(Rental.id == record.rental_id)
            res = await self.db.execute(stmt)
            rental = res.scalar_one()

        if self.cf.is_configured and record.cloudflare_record_id and not record.cloudflare_record_id.startswith("sim_"):
            zone_id = await self._get_parent_domain_zone_id(rental.parent_domain_id)
            try:
                await self.cf.delete_dns_record(
                    zone_id=zone_id,
                    record_id=record.cloudflare_record_id,
                )
            except CloudflareError as e:
                logger.error(f"Failed to delete Cloudflare DNS record: {e}")

        record.status = DnsRecordStatus.DELETED
        await self.db.delete(record)
        await self.db.flush()

    async def suspend_all_rental_records(self, rental_id: uuid.UUID) -> None:
        """
        Remove or suspend all DNS records in Cloudflare for a rental
        (called when rental expires or is suspended).
        """
        records = await self.get_rental_records(rental_id)
        if not records:
            return

        stmt = select(Rental).where(Rental.id == rental_id)
        res = await self.db.execute(stmt)
        rental = res.scalars().first()
        if not rental:
            return

        zone_id = await self._get_parent_domain_zone_id(rental.parent_domain_id)

        for rec in records:
            if self.cf.is_configured and rec.cloudflare_record_id and not rec.cloudflare_record_id.startswith("sim_"):
                try:
                    await self.cf.delete_dns_record(zone_id, rec.cloudflare_record_id)
                except Exception as e:
                    logger.warning(f"Could not remove CF record {rec.cloudflare_record_id} on suspension: {e}")
            rec.status = DnsRecordStatus.SUSPENDED

        await self.db.flush()

    async def restore_all_rental_records(self, rental_id: uuid.UUID) -> None:
        """
        Restore suspended DNS records in Cloudflare
        (called after successful renewal or unsuspension).
        """
        stmt = (
            select(DnsRecord)
            .where(
                DnsRecord.rental_id == rental_id,
                DnsRecord.status == DnsRecordStatus.SUSPENDED,
            )
        )
        res = await self.db.execute(stmt)
        records = list(res.scalars().all())

        if not records:
            return

        rental_stmt = select(Rental).where(Rental.id == rental_id)
        rental_res = await self.db.execute(rental_stmt)
        rental = rental_res.scalar_one()

        zone_id = await self._get_parent_domain_zone_id(rental.parent_domain_id)

        for rec in records:
            if self.cf.is_configured:
                try:
                    cf_result = await self.cf.create_dns_record(
                        zone_id=zone_id,
                        record_type=rec.record_type.value,
                        name=rec.name,
                        content=rec.content,
                        ttl=rec.ttl,
                        proxied=rec.proxied,
                    )
                    rec.cloudflare_record_id = cf_result["id"]
                    rec.status = DnsRecordStatus.ACTIVE
                    rec.last_synced_at = datetime.now(timezone.utc)
                except Exception as e:
                    logger.error(f"Failed to restore record {rec.id} in Cloudflare: {e}")
                    rec.status = DnsRecordStatus.FAILED
                    rec.last_error = str(e)
            else:
                rec.status = DnsRecordStatus.ACTIVE
                rec.last_synced_at = datetime.now(timezone.utc)

        await self.db.flush()
