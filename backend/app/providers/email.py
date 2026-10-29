"""
Email provider abstraction.

Supports SMTP, SendGrid, and a console provider for development.
All emails are sent server-side. The provider is configured via environment variables.
"""

from __future__ import annotations

import abc
import logging
from typing import Optional

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class EmailProviderBase(abc.ABC):
    """Abstract email provider."""

    @abc.abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> bool:
        """Send an email. Returns True if sent successfully."""
        ...


class ConsoleEmailProvider(EmailProviderBase):
    """Development email provider that logs to console."""

    async def send_email(
        self, to: str, subject: str, html_body: str, text_body: str | None = None
    ) -> bool:
        logger.info(
            f"\n{'='*60}\n"
            f"EMAIL TO: {to}\n"
            f"SUBJECT: {subject}\n"
            f"{'='*60}\n"
            f"{text_body or html_body}\n"
            f"{'='*60}"
        )
        return True


class SmtpEmailProvider(EmailProviderBase):
    """SMTP email provider."""

    async def send_email(
        self, to: str, subject: str, html_body: str, text_body: str | None = None
    ) -> bool:
        try:
            import aiosmtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            msg = MIMEMultipart("alternative")
            msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
            msg["To"] = to
            msg["Subject"] = subject

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS,
            )
            logger.info(f"Email sent to {to}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False


class SendGridEmailProvider(EmailProviderBase):
    """SendGrid email provider."""

    async def send_email(
        self, to: str, subject: str, html_body: str, text_body: str | None = None
    ) -> bool:
        try:
            import httpx

            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            }

            content = [{"type": "text/html", "value": html_body}]
            if text_body:
                content.insert(0, {"type": "text/plain", "value": text_body})

            payload = {
                "personalizations": [{"to": [{"email": to}]}],
                "from": {
                    "email": settings.EMAIL_FROM_ADDRESS,
                    "name": settings.EMAIL_FROM_NAME,
                },
                "subject": subject,
                "content": content,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code in (200, 201, 202):
                    logger.info(f"Email sent via SendGrid to {to}: {subject}")
                    return True
                else:
                    logger.error(
                        f"SendGrid error {response.status_code}: {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to send email via SendGrid to {to}: {e}")
            return False


def get_email_provider() -> EmailProviderBase:
    """Get the configured email provider."""
    if settings.EMAIL_PROVIDER == "console":
        return ConsoleEmailProvider()
    elif settings.EMAIL_PROVIDER == "smtp":
        return SmtpEmailProvider()
    elif settings.EMAIL_PROVIDER == "sendgrid":
        return SendGridEmailProvider()
    else:
        logger.warning(f"Unknown email provider: {settings.EMAIL_PROVIDER}, using console")
        return ConsoleEmailProvider()


class EmailService:
    """High-level email service for sending transactional emails."""

    def __init__(self):
        self.provider = get_email_provider()
        self.site_url = settings.PUBLIC_SITE_URL
        self.from_name = settings.EMAIL_FROM_NAME

    async def send_verification_email(self, to: str, token: str, username: str = "") -> bool:
        verify_url = f"{self.site_url}/verify-email?token={token}"
        subject = f"Verify your {self.from_name} account"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Welcome to {self.from_name}{f', {username}' if username else ''}!</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verify_url}" style="display: inline-block; padding: 12px 24px;
                background: #6366f1; color: white; text-decoration: none; border-radius: 8px;">
                Verify Email</a></p>
            <p>This link expires in 24 hours.</p>
            <p>If you didn't create this account, ignore this email.</p>
        </div>
        """
        text = f"Welcome to {self.from_name}! Verify your email: {verify_url}"
        return await self.provider.send_email(to, subject, html, text)

    async def send_password_reset_email(self, to: str, token: str) -> bool:
        reset_url = f"{self.site_url}/reset-password?token={token}"
        subject = f"Reset your {self.from_name} password"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Password Reset</h2>
            <p>Click below to reset your password:</p>
            <p><a href="{reset_url}" style="display: inline-block; padding: 12px 24px;
                background: #6366f1; color: white; text-decoration: none; border-radius: 8px;">
                Reset Password</a></p>
            <p>This link expires in 1 hour. If you didn't request this, ignore this email.</p>
        </div>
        """
        text = f"Reset your password: {reset_url}"
        return await self.provider.send_email(to, subject, html, text)

    async def send_rental_confirmation(
        self, to: str, subdomain: str, expires_at: str = ""
    ) -> bool:
        subject = f"Your subdomain {subdomain} is active!"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Subdomain Activated</h2>
            <p>Your subdomain <strong>{subdomain}</strong> is now active.</p>
            <p>Expires: {expires_at}</p>
            <p>Manage your subdomains in your <a href="{self.site_url}/dashboard">dashboard</a>.</p>
        </div>
        """
        return await self.provider.send_email(to, subject, html)

    async def send_expiry_reminder(
        self, to: str, subdomain: str, days_remaining: int, expiry_date: str = ""
    ) -> bool:
        subject = f"Your subdomain {subdomain} expires in {days_remaining} days"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Expiry Reminder</h2>
            <p>Your subdomain <strong>{subdomain}</strong> expires in <strong>{days_remaining} days</strong>.</p>
            <p>Renew it in your <a href="{self.site_url}/dashboard/rentals">dashboard</a> to keep it active.</p>
        </div>
        """
        return await self.provider.send_email(to, subject, html)

    async def send_grace_period_notice(self, to: str, subdomain: str, days_left: int) -> bool:
        subject = f"URGENT: {subdomain} has expired — {days_left} days to renew"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Subdomain Expired</h2>
            <p>Your subdomain <strong>{subdomain}</strong> has expired.</p>
            <p>You have <strong>{days_left} days</strong> to renew before it becomes available to others.</p>
            <p><a href="{self.site_url}/dashboard/rentals" style="display: inline-block; padding: 12px 24px;
                background: #ef4444; color: white; text-decoration: none; border-radius: 8px;">
                Renew Now</a></p>
        </div>
        """
        return await self.provider.send_email(to, subject, html)

    async def send_wallet_funded(
        self,
        to: str,
        amount_display: str = "",
        balance_display: str = "",
        amount_inr: str = "",
        new_balance_inr: str = "",
    ) -> bool:
        display_amt = amount_display or amount_inr or "Funds"
        display_bal = balance_display or new_balance_inr
        subject = f"{display_amt} added to your {self.from_name} wallet"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Wallet Funded</h2>
            <p>{display_amt} has been added to your wallet.</p>
            {f'<p>New balance: <strong>{display_bal}</strong></p>' if display_bal else ''}
        </div>
        """
        return await self.provider.send_email(to, subject, html)
        subject = f"{amount_display} added to your {self.from_name} wallet"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Wallet Funded</h2>
            <p>{amount_display} has been added to your wallet.</p>
            <p>New balance: <strong>{balance_display}</strong></p>
        </div>
        """
        return await self.provider.send_email(to, subject, html)


# Singleton
email_service = EmailService()
