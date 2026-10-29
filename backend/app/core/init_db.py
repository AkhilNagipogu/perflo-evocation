"""
Database initialization and automatic seed routine.
Ensures all tables and baseline records exist at application boot.
"""

from __future__ import annotations

import json
import logging
import os

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import Base, async_session_factory, engine
from app.core.security import hash_password
import app.models  # ensure all models are registered
from app.models.admin_user import AdminUser
from app.models.coupon import Coupon
from app.models.parent_domain import ParentDomain
from app.models.pricing import PricingPlan

logger = logging.getLogger("evocation.init_db")
settings = get_settings()


async def init_db() -> None:
    """Ensure tables exist and baseline seed data is populated."""
    logger.info("Verifying database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # 1. Administrator Account
        admin_email = settings.ADMIN_INITIAL_EMAIL or "admin@example.com"
        admin_pass = settings.ADMIN_INITIAL_PASSWORD or "AdminSecure123!"

        stmt = select(AdminUser).where(AdminUser.email == admin_email)
        existing_admin = (await db.execute(stmt)).scalars().first()
        if not existing_admin:
            admin = AdminUser(
                email=admin_email,
                username="admin",
                password_hash=hash_password(admin_pass),
                full_name="Platform Administrator",
                role="super_admin",
                is_active=True,
            )
            db.add(admin)
            logger.info(f"Initialized admin user: {admin_email}")

        # 2. Parent Root Domain (e.g., perflo.in)
        primary_domain = os.getenv("PRIMARY_DOMAIN", "perflo.in")
        stmt_domain = select(ParentDomain).where(ParentDomain.domain == primary_domain)
        existing_domain = (await db.execute(stmt_domain)).scalars().first()
        if not existing_domain:
            domain = ParentDomain(
                domain=primary_domain,
                description="Primary subdomain rental root zone",
                is_active=True,
                reserved_names=json.dumps([
                    "www", "mail", "api", "admin", "app", "dashboard",
                    "status", "billing", "portal", "support", "help",
                ]),
                cloudflare_zone_id=os.getenv("CLOUDFLARE_PRIMARY_ZONE_ID", ""),
            )
            db.add(domain)
            logger.info(f"Initialized parent domain: {primary_domain}")

        # 3. Base Pricing Plan (₹60 / year for 2 subdomains bundle)
        base_slug = "base-bundle"
        stmt_plan = select(PricingPlan).where(PricingPlan.slug == base_slug)
        existing_plan = (await db.execute(stmt_plan)).scalars().first()
        if not existing_plan:
            plan = PricingPlan(
                name="Standard Subdomain Bundle",
                slug=base_slug,
                description="Rent 2 custom subdomains for a full year with Cloudflare DNS management.",
                price_paise=6000,  # ₹60.00
                billing_period_days=365,
                included_subdomains=2,
                is_active=True,
                is_base_plan=True,
            )
            db.add(plan)
            logger.info("Initialized base pricing plan: ₹60/year for 2 subdomains")

        # 4. Default Promotional Coupon
        coupon_code = "WELCOME10"
        stmt_coupon = select(Coupon).where(Coupon.code == coupon_code)
        existing_coupon = (await db.execute(stmt_coupon)).scalars().first()
        if not existing_coupon:
            coupon = Coupon(
                code=coupon_code,
                description="Welcome discount: 10% off your subscription",
                discount_type="percentage",
                discount_value=10,
                is_active=True,
                max_uses_per_user=1,
                min_purchase_paise=6000,
            )
            db.add(coupon)
            logger.info(f"Initialized promo coupon: {coupon_code}")

        await db.commit()
    logger.info("Database schema and baseline seed ready.")
