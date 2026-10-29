"""
Tests for DNS record validation, CNAME collisions, and authorization boundaries.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rental import Rental, RentalStatus
from app.schemas.rental import DnsRecordCreate
from app.services.dns_service import DnsService, DnsValidationError


@pytest.mark.asyncio
async def test_dns_a_record_validation():
    """Valid IPv4 passes; invalid IP raises DnsValidationError."""
    service = DnsService(None)
    # Valid IP
    service.validate_content("A", "93.184.216.34")

    # Invalid IP
    with pytest.raises(DnsValidationError, match="IPv4"):
        service.validate_content("A", "not-an-ip")


@pytest.mark.asyncio
async def test_dns_cname_collision(
    db_session: AsyncSession, test_user, test_parent_domain
):
    """Adding a CNAME when other records exist must fail."""
    rental = Rental(
        user_id=test_user.id,
        parent_domain_id=test_parent_domain.id,
        subdomain_name="collisiontest",
        full_domain="collisiontest.example.com",
        status=RentalStatus.ACTIVE,
    )
    db_session.add(rental)
    await db_session.flush()

    dns_service = DnsService(db_session)

    # 1. Add an A record
    await dns_service.create_record(
        rental,
        DnsRecordCreate(record_type="A", content="93.184.216.34", ttl=3600),
    )

    # 2. Attempt to add a CNAME record to the same host -> must raise DnsValidationError
    with pytest.raises(DnsValidationError, match="CNAME"):
        await dns_service.create_record(
            rental,
            DnsRecordCreate(record_type="CNAME", content="target.domain.com", ttl=3600),
        )


@pytest.mark.asyncio
async def test_dns_unauthorized_access(
    client: AsyncClient, db_session: AsyncSession, test_user, test_parent_domain
):
    """A user cannot access DNS records for a rental they do not own."""
    # Rental owned by different UUID
    import uuid
    other_rental = Rental(
        user_id=uuid.uuid4(),
        parent_domain_id=test_parent_domain.id,
        subdomain_name="otherdomain",
        full_domain="otherdomain.example.com",
        status=RentalStatus.ACTIVE,
    )
    db_session.add(other_rental)
    await db_session.commit()

    # Log in as test_user
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(test_user.id), "type": "access"})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(f"/api/v1/rentals/{other_rental.id}/dns", headers=headers)
    assert response.status_code == 404
