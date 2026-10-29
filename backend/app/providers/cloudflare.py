"""
Cloudflare DNS provider — real API integration.

Uses Cloudflare API v4. Requires a scoped API token with:
- Zone:DNS:Edit permission for the managed zones.

Never exposes the API token to browsers.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CloudflareError(Exception):
    """Cloudflare API error."""
    def __init__(self, message: str, errors: list | None = None, status_code: int = 0):
        super().__init__(message)
        self.errors = errors or []
        self.status_code = status_code


class CloudflareProvider:
    """
    Cloudflare DNS API integration.

    All operations are performed server-side. The API token is never
    sent to the frontend or logged.
    """

    def __init__(self):
        self.base_url = settings.CLOUDFLARE_API_BASE_URL
        self.token = settings.CLOUDFLARE_API_TOKEN
        self.zone_map = settings.cloudflare_zone_map  # {zone_id: domain}
        self.domain_zone_map = settings.domain_zone_map  # {domain: zone_id}

    @property
    def is_configured(self) -> bool:
        """Check if Cloudflare credentials are configured."""
        return bool(self.token and self.zone_map)

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _get_zone_id(self, domain: str) -> str:
        """Get zone ID for a parent domain."""
        zone_id = self.domain_zone_map.get(domain)
        if not zone_id:
            raise CloudflareError(f"No Cloudflare zone configured for domain: {domain}")
        return zone_id

    async def create_dns_record(
        self,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        ttl: int = 3600,
        proxied: bool = False,
    ) -> dict[str, Any]:
        """
        Create a DNS record in Cloudflare.
        Returns the created record including the Cloudflare record ID.
        """
        if not self.is_configured:
            raise CloudflareError("Cloudflare is not configured")

        # Validate record type
        allowed_types = {"A", "AAAA", "CNAME", "TXT"}
        if record_type not in allowed_types:
            raise CloudflareError(f"Record type {record_type} is not allowed")

        url = f"{self.base_url}/zones/{zone_id}/dns_records"
        payload = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": ttl,
            "proxied": proxied if record_type in ("A", "AAAA", "CNAME") else False,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    url, json=payload, headers=self._get_headers()
                )
                data = response.json()

                if not data.get("success"):
                    errors = data.get("errors", [])
                    error_msg = "; ".join(
                        e.get("message", "Unknown error") for e in errors
                    )
                    raise CloudflareError(
                        f"Failed to create DNS record: {error_msg}",
                        errors=errors,
                        status_code=response.status_code,
                    )

                logger.info(
                    f"Created DNS record: {record_type} {name} -> {content} "
                    f"(ID: {data['result']['id']})"
                )
                return data["result"]

            except httpx.HTTPError as e:
                logger.error(f"Cloudflare API error: {e}")
                raise CloudflareError(f"Cloudflare API connection error: {e}")

    async def get_dns_record(
        self, zone_id: str, record_id: str
    ) -> dict[str, Any] | None:
        """Get a specific DNS record by ID."""
        if not self.is_configured:
            raise CloudflareError("Cloudflare is not configured")

        url = f"{self.base_url}/zones/{zone_id}/dns_records/{record_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                if response.status_code == 404:
                    return None
                data = response.json()
                if not data.get("success"):
                    return None
                return data["result"]
            except httpx.HTTPError as e:
                logger.error(f"Cloudflare API error: {e}")
                raise CloudflareError(f"Cloudflare API connection error: {e}")

    async def update_dns_record(
        self,
        zone_id: str,
        record_id: str,
        record_type: str,
        name: str,
        content: str,
        ttl: int = 3600,
        proxied: bool = False,
    ) -> dict[str, Any]:
        """Update an existing DNS record."""
        if not self.is_configured:
            raise CloudflareError("Cloudflare is not configured")

        url = f"{self.base_url}/zones/{zone_id}/dns_records/{record_id}"
        payload = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": ttl,
            "proxied": proxied if record_type in ("A", "AAAA", "CNAME") else False,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.put(
                    url, json=payload, headers=self._get_headers()
                )
                data = response.json()
                if not data.get("success"):
                    errors = data.get("errors", [])
                    error_msg = "; ".join(
                        e.get("message", "Unknown error") for e in errors
                    )
                    raise CloudflareError(
                        f"Failed to update DNS record: {error_msg}",
                        errors=errors,
                        status_code=response.status_code,
                    )
                logger.info(f"Updated DNS record {record_id}: {name} -> {content}")
                return data["result"]
            except httpx.HTTPError as e:
                logger.error(f"Cloudflare API error: {e}")
                raise CloudflareError(f"Cloudflare API connection error: {e}")

    async def delete_dns_record(
        self, zone_id: str, record_id: str
    ) -> bool:
        """Delete a DNS record."""
        if not self.is_configured:
            raise CloudflareError("Cloudflare is not configured")

        url = f"{self.base_url}/zones/{zone_id}/dns_records/{record_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.delete(url, headers=self._get_headers())
                data = response.json()
                if not data.get("success"):
                    if response.status_code == 404:
                        logger.warning(f"DNS record {record_id} already deleted")
                        return True
                    errors = data.get("errors", [])
                    error_msg = "; ".join(
                        e.get("message", "Unknown error") for e in errors
                    )
                    raise CloudflareError(
                        f"Failed to delete DNS record: {error_msg}",
                        errors=errors,
                        status_code=response.status_code,
                    )
                logger.info(f"Deleted DNS record {record_id}")
                return True
            except httpx.HTTPError as e:
                logger.error(f"Cloudflare API error: {e}")
                raise CloudflareError(f"Cloudflare API connection error: {e}")

    async def list_dns_records(
        self,
        zone_id: str,
        name: str | None = None,
        record_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """List DNS records, optionally filtered by name and type."""
        if not self.is_configured:
            raise CloudflareError("Cloudflare is not configured")

        url = f"{self.base_url}/zones/{zone_id}/dns_records"
        params: dict[str, str] = {"per_page": "100"}
        if name:
            params["name"] = name
        if record_type:
            params["type"] = record_type

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    url, params=params, headers=self._get_headers()
                )
                data = response.json()
                if not data.get("success"):
                    return []
                return data.get("result", [])
            except httpx.HTTPError as e:
                logger.error(f"Cloudflare API error: {e}")
                raise CloudflareError(f"Cloudflare API connection error: {e}")

    async def verify_token(self) -> bool:
        """Verify that the API token is valid."""
        if not self.token:
            return False

        url = f"{self.base_url}/user/tokens/verify"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                data = response.json()
                return data.get("success", False)
            except httpx.HTTPError:
                return False


# Singleton instance
cloudflare_provider = CloudflareProvider()
