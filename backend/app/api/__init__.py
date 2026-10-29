"""
API router assembly — mounts all individual route modules.
"""

from fastapi import APIRouter

from app.api.abuse import router as abuse_router
from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.coupons import router as coupons_router
from app.api.dns import router as dns_router
from app.api.health import router as health_router
from app.api.notifications import router as notifications_router
from app.api.payments import router as payments_router
from app.api.pricing import router as pricing_router
from app.api.rentals import router as rentals_router
from app.api.wallet import router as wallet_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(rentals_router)
api_router.include_router(wallet_router)
api_router.include_router(dns_router)
api_router.include_router(payments_router)
api_router.include_router(coupons_router)
api_router.include_router(abuse_router)
api_router.include_router(notifications_router)
api_router.include_router(pricing_router)
api_router.include_router(admin_router)

__all__ = ["api_router"]
