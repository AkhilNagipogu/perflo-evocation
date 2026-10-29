"""Models package — imports all models to ensure they're registered with SQLAlchemy."""

from app.models.user import User, AdminUser
from app.models.parent_domain import ParentDomain
from app.models.pricing import PricingPlan, PricingTier
from app.models.wallet import Wallet, WalletTransaction
from app.models.rental import Rental, RentalNameHistory
from app.models.dns_record import DnsRecord
from app.models.payment import PaymentOrder
from app.models.subscription import Subscription
from app.models.coupon import Coupon, CouponRedemption
from app.models.notification import Notification
from app.models.abuse_report import AbuseReport, AbuseAction
from app.models.audit_log import AuditLog
from app.models.system_config import SystemConfig
from app.models.reservation import NameReservation

__all__ = [
    "User",
    "AdminUser",
    "ParentDomain",
    "PricingPlan",
    "PricingTier",
    "Wallet",
    "WalletTransaction",
    "Rental",
    "RentalNameHistory",
    "DnsRecord",
    "PaymentOrder",
    "Subscription",
    "Coupon",
    "CouponRedemption",
    "Notification",
    "AbuseReport",
    "AbuseAction",
    "AuditLog",
    "SystemConfig",
    "NameReservation",
]
