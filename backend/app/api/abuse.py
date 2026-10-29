"""
Public abuse report submission and administrative review API routes.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.core.security import generate_reference_id
from app.models.abuse_report import AbuseCategory, AbuseReport, AbuseReportStatus
from app.models.admin_user import AdminUser
from app.models.rental import Rental
from app.schemas.abuse import (
    AbuseReportCreate,
    AbuseReportDetailResponse,
    AbuseReportResponse,
    AbuseReportReview,
)
from app.services.admin_service import AdminService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Abuse Reports"])


@router.post("/abuse-reports", response_model=AbuseReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_abuse_report(
    data: AbuseReportCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Public endpoint to submit an abuse report against a hosted subdomain."""
    ref_id = generate_reference_id("ABUSE")
    domain_clean = data.reported_domain.strip().lower()

    # Link with rental if it exists in platform
    rental_stmt = select(Rental).where(Rental.full_domain == domain_clean)
    rental_res = await db.execute(rental_stmt)
    rental = rental_res.scalars().first()

    report = AbuseReport(
        reference_id=ref_id,
        reported_domain=domain_clean,
        category=AbuseCategory(data.category),
        description=data.description,
        evidence_urls=json.dumps(data.evidence_urls) if data.evidence_urls else None,
        reporter_email=data.reporter_email,
        reporter_name=data.reporter_name,
        status=AbuseReportStatus.SUBMITTED,
        rental_id=rental.id if rental else None,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return AbuseReportResponse(
        id=report.id,
        reference_id=report.reference_id,
        reported_domain=report.reported_domain,
        category=report.category.value,
        status=report.status.value,
        created_at=report.created_at,
    )


@router.get("/abuse-reports/{reference_id}", response_model=AbuseReportResponse)
async def check_abuse_report_status(
    reference_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Public lookup of an abuse report's review status using its reference ID."""
    stmt = select(AbuseReport).where(AbuseReport.reference_id == reference_id)
    res = await db.execute(stmt)
    report = res.scalars().first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report reference not found")

    return AbuseReportResponse(
        id=report.id,
        reference_id=report.reference_id,
        reported_domain=report.reported_domain,
        category=report.category.value,
        status=report.status.value,
        created_at=report.created_at,
    )


# Admin endpoints
@router.get("/admin/abuse-reports", response_model=list[AbuseReportDetailResponse])
async def list_abuse_reports(
    status_filter: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all abuse reports with administrative details and filtering."""
    stmt = select(AbuseReport)
    if status_filter:
        stmt = stmt.where(AbuseReport.status == AbuseReportStatus(status_filter))

    stmt = stmt.order_by(AbuseReport.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    reports = list(res.scalars().all())

    return [
        AbuseReportDetailResponse(
            id=r.id,
            reference_id=r.reference_id,
            reported_domain=r.reported_domain,
            category=r.category.value,
            status=r.status.value,
            description=r.description,
            evidence_urls=r.evidence_urls,
            reporter_email=r.reporter_email,
            reporter_name=r.reporter_name,
            rental_id=r.rental_id,
            reviewed_by_admin_id=r.reviewed_by_admin_id,
            review_notes=r.review_notes,
            reviewed_at=r.reviewed_at,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in reports
    ]


@router.post("/admin/abuse-reports/{report_id}/review", response_model=AbuseReportDetailResponse)
async def review_abuse_report(
    report_id: uuid.UUID,
    data: AbuseReportReview,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Perform review and optional automated suspension on an abuse report."""
    admin_service = AdminService(db)
    try:
        report = await admin_service.review_abuse_report(
            report_id=report_id,
            status=AbuseReportStatus(data.status),
            admin_id=current_admin.id,
            review_notes=data.review_notes,
            action_type=data.action_type,
            action_description=data.review_notes,
        )
        await db.commit()
        return AbuseReportDetailResponse(
            id=report.id,
            reference_id=report.reference_id,
            reported_domain=report.reported_domain,
            category=report.category.value,
            status=report.status.value,
            description=report.description,
            evidence_urls=report.evidence_urls,
            reporter_email=report.reporter_email,
            reporter_name=report.reporter_name,
            rental_id=report.rental_id,
            reviewed_by_admin_id=report.reviewed_by_admin_id,
            review_notes=report.review_notes,
            reviewed_at=report.reviewed_at,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
