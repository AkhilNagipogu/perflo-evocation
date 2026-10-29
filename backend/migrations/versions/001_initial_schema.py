"""Initial schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('suspension_reason', sa.Text(), nullable=True),
        sa.Column('email_verification_token', sa.String(length=512), nullable=True),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token', sa.String(length=512), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notify_expiry_reminders', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('notify_wallet_events', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('notify_low_balance', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # 2. admin_users
    op.create_table(
        'admin_users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=32), nullable=False, server_default='admin'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('mfa_secret', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_admin_users_email', 'admin_users', ['email'], unique=True)
    op.create_index('ix_admin_users_username', 'admin_users', ['username'], unique=True)

    # 3. parent_domains
    op.create_table(
        'parent_domains',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('cloudflare_zone_id', sa.String(length=64), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('reserved_names', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_parent_domains_domain', 'parent_domains', ['domain'], unique=True)

    # 4. pricing_plans
    op.create_table(
        'pricing_plans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_paise', sa.Integer(), nullable=False),
        sa.Column('billing_period_days', sa.Integer(), nullable=False, server_default='365'),
        sa.Column('included_subdomains', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_base_plan', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pricing_plans_slug', 'pricing_plans', ['slug'], unique=True)

    # 5. pricing_tiers
    op.create_table(
        'pricing_tiers',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('plan_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('min_subdomains', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_subdomains', sa.Integer(), nullable=True),
        sa.Column('price_per_subdomain_paise', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['pricing_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. wallets
    op.create_table(
        'wallets',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('balance_paise', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('has_been_funded', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_wallets_user_id', 'wallets', ['user_id'], unique=True)

    # 7. subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('pricing_plan_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('grace_period_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_subdomains', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('used_subdomains', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('price_paid_paise', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('renewal_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_renewal_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['pricing_plan_id'], ['pricing_plans.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_subscriptions_user_status', 'subscriptions', ['user_id', 'status'])

    # 8. rentals
    op.create_table(
        'rentals',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('parent_domain_id', sa.Uuid(), nullable=False),
        sa.Column('pricing_plan_id', sa.Uuid(), nullable=True),
        sa.Column('subdomain_name', sa.String(length=63), nullable=False),
        sa.Column('full_domain', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='reserved'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('grace_period_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('price_paid_paise', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('last_renewal_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('renewal_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_renamed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rename_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cloudflare_record_ids', sa.Text(), nullable=True),
        sa.Column('subscription_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['parent_domain_id'], ['parent_domains.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['pricing_plan_id'], ['pricing_plans.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    # Partial unique index: only non-released/non-cancelled names are unique
    op.create_index(
        'uq_active_rental_per_subdomain',
        'rentals',
        ['parent_domain_id', 'subdomain_name'],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('released', 'cancelled')"),
    )
    op.create_index('ix_rentals_user_status', 'rentals', ['user_id', 'status'])
    op.create_index('ix_rentals_expires_at', 'rentals', ['expires_at'])

    # 9. rental_name_history
    op.create_table(
        'rental_name_history',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('rental_id', sa.Uuid(), nullable=False),
        sa.Column('old_subdomain_name', sa.String(length=63), nullable=False),
        sa.Column('new_subdomain_name', sa.String(length=63), nullable=False),
        sa.Column('old_full_domain', sa.String(length=255), nullable=False),
        sa.Column('new_full_domain', sa.String(length=255), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('changed_by_user_id', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['changed_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rental_id'], ['rentals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. dns_records
    op.create_table(
        'dns_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('rental_id', sa.Uuid(), nullable=False),
        sa.Column('record_type', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('content', sa.String(length=4096), nullable=False),
        sa.Column('ttl', sa.Integer(), nullable=False, server_default='3600'),
        sa.Column('proxied', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('cloudflare_record_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['rental_id'], ['rentals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dns_records_rental_type', 'dns_records', ['rental_id', 'record_type'])

    # 11. payment_orders
    op.create_table(
        'payment_orders',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('wallet_id', sa.Uuid(), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('amount_paise', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='created'),
        sa.Column('provider_order_id', sa.String(length=128), nullable=True),
        sa.Column('provider_payment_id', sa.String(length=128), nullable=True),
        sa.Column('webhook_received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('webhook_event_id', sa.String(length=128), nullable=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payment_orders_idempotency', 'payment_orders', ['idempotency_key'], unique=True)

    # 12. wallet_transactions
    op.create_table(
        'wallet_transactions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('wallet_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('reference_id', sa.String(length=64), nullable=False),
        sa.Column('transaction_type', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='settled'),
        sa.Column('amount_paise', sa.Integer(), nullable=False),
        sa.Column('balance_after_paise', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('rental_id', sa.Uuid(), nullable=True),
        sa.Column('payment_order_id', sa.Uuid(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['payment_order_id'], ['payment_orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rental_id'], ['rentals.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_wallet_transactions_idempotency', 'wallet_transactions', ['idempotency_key'], unique=True)
    op.create_index('ix_wallet_transactions_user', 'wallet_transactions', ['user_id', 'created_at'])

    # 13. coupons
    op.create_table(
        'coupons',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('discount_type', sa.String(length=16), nullable=False),
        sa.Column('discount_value', sa.Integer(), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('max_uses_per_user', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_uses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('min_purchase_paise', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('eligible_plans', sa.Text(), nullable=True),
        sa.Column('created_by_admin_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_admin_id'], ['admin_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_coupons_code', 'coupons', ['code'], unique=True)

    # 14. coupon_redemptions
    op.create_table(
        'coupon_redemptions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('coupon_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('rental_id', sa.Uuid(), nullable=True),
        sa.Column('subscription_id', sa.Uuid(), nullable=True),
        sa.Column('discount_amount_paise', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['coupon_id'], ['coupons.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['rental_id'], ['rentals.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_coupon_redemptions_coupon_user', 'coupon_redemptions', ['coupon_id', 'user_id'])

    # 15. notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('action_url', sa.String(length=512), nullable=True),
        sa.Column('action_label', sa.String(length=64), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'is_read'])

    # 16. abuse_reports
    op.create_table(
        'abuse_reports',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('reference_id', sa.String(length=64), nullable=False),
        sa.Column('reported_domain', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_urls', sa.Text(), nullable=True),
        sa.Column('reporter_email', sa.String(length=255), nullable=True),
        sa.Column('reporter_name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='submitted'),
        sa.Column('rental_id', sa.Uuid(), nullable=True),
        sa.Column('reviewed_by_admin_id', sa.Uuid(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['rental_id'], ['rentals.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewed_by_admin_id'], ['admin_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_abuse_reports_ref', 'abuse_reports', ['reference_id'], unique=True)
    op.create_index('ix_abuse_reports_status', 'abuse_reports', ['status'])

    # 17. abuse_actions
    op.create_table(
        'abuse_actions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('abuse_report_id', sa.Uuid(), nullable=False),
        sa.Column('admin_user_id', sa.Uuid(), nullable=False),
        sa.Column('action_type', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('state_before', sa.Text(), nullable=True),
        sa.Column('state_after', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['abuse_report_id'], ['abuse_reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['admin_user_id'], ['admin_users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )

    # 18. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('actor_type', sa.String(length=16), nullable=False),
        sa.Column('actor_id', sa.Uuid(), nullable=True),
        sa.Column('actor_email', sa.String(length=255), nullable=True),
        sa.Column('actor_ip', sa.String(length=45), nullable=True),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('details_before', sa.Text(), nullable=True),
        sa.Column('details_after', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_actor', 'audit_logs', ['actor_type', 'actor_id'])
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_audit_logs_created', 'audit_logs', ['created_at'])

    # 19. system_config
    op.create_table(
        'system_config',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('key', sa.String(length=128), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('value_type', sa.String(length=16), nullable=False, server_default='string'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_by_admin_id', sa.Uuid(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_system_config_key', 'system_config', ['key'], unique=True)

    # 20. name_reservations
    op.create_table(
        'name_reservations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('subdomain_name', sa.String(length=63), nullable=False),
        sa.Column('parent_domain_id', sa.Uuid(), nullable=False),
        sa.Column('full_domain', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('session_id', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['parent_domain_id'], ['parent_domains.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_name_reservations_subdomain', 'name_reservations', ['parent_domain_id', 'subdomain_name'], unique=True)


def downgrade() -> None:
    op.drop_table('name_reservations')
    op.drop_table('system_config')
    op.drop_table('audit_logs')
    op.drop_table('abuse_actions')
    op.drop_table('abuse_reports')
    op.drop_table('notifications')
    op.drop_table('coupon_redemptions')
    op.drop_table('coupons')
    op.drop_table('wallet_transactions')
    op.drop_table('payment_orders')
    op.drop_table('dns_records')
    op.drop_table('rental_name_history')
    op.drop_table('rentals')
    op.drop_table('subscriptions')
    op.drop_table('wallets')
    op.drop_table('pricing_tiers')
    op.drop_table('pricing_plans')
    op.drop_table('parent_domains')
    op.drop_table('admin_users')
    op.drop_table('users')
