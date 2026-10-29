# Cloudflare DNS Integration Manual

## 1. Overview & Security Boundaries

Evocation manages DNS records programmatically using the official **Cloudflare API v4**.

### Security Rules
- **Token Isolation**: The Cloudflare API token is held strictly in server-side environment variables (`CLOUDFLARE_API_TOKEN`). It is never passed to frontend client browsers, returned in API payloads, or written into standard application log files.
- **Token Permissions**: The token requires scoped permissions:
  - `Zone.DNS:Edit` for specific managed zones.
  - `Zone.Zone:Read` for verification.

## 2. Zone Mapping Configuration

Multiple parent domains can be managed simultaneously by defining `CLOUDFLARE_ZONE_MAP`:

```json
{
  "zone_id_for_perflo_in": "perflo.in",
  "zone_id_for_evocation_dev": "evocation.dev"
}
```

When a customer creates or updates a DNS record, the platform resolves the parent domain to its corresponding Cloudflare Zone ID automatically.

## 3. Supported Record Types & Validation

The platform enforces RFC syntax and integrity checks before making external Cloudflare API calls:

1. **A Records**:
   - Validated against IPv4 formats (`ipaddress.IPv4Address`).
   - Warns on private/loopback IP assignments.
2. **AAAA Records**:
   - Validated against IPv6 formats (`ipaddress.IPv6Address`).
3. **CNAME Records**:
   - Validated against valid domain name targets.
   - **CNAME Collision Rule**: RFC 1034 prohibits co-existence of CNAME with other records on the same hostname. Evocation blocks adding CNAME if A/AAAA/TXT exist, and blocks adding other records if CNAME exists.
4. **TXT Records**:
   - Validated up to 4096 character lengths.

## 4. Cloudflare Proxying (CDN & DDoS)

For `A`, `AAAA`, and `CNAME` records, customers can enable the `proxied` toggle (Cloudflare Orange Cloud). This passes traffic through Cloudflare's edge proxy network, masking origin server IP addresses and providing automated DDoS mitigation and SSL certificates.
Proxying is automatically disabled for `TXT` records.
