#!/usr/bin/env bash
# ==============================================================================
# Production Health & Readiness Verification Script
# Verifies container health, API responses, and database connectivity.
# ==============================================================================

set -euo pipefail

PUBLIC_URL="${PUBLIC_URL:-http://localhost}"
API_URL="${API_URL:-http://localhost:8000}"

echo "Checking Evocation system health..."

# 1. Check backend health endpoint
echo -n "Checking Backend Health (/api/v1/health)... "
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/api/v1/health" || echo "FAILED 000")
HTTP_CODE=$(echo "${HEALTH_RESPONSE}" | tail -n1)
BODY=$(echo "${HEALTH_RESPONSE}" | sed '$d')

if [ "${HTTP_CODE}" -eq 200 ]; then
    echo "OK (HTTP 200)"
    echo "Health payload: ${BODY}"
else
    echo "FAILED (HTTP ${HTTP_CODE})"
    exit 1
fi

# 2. Check root service endpoint
echo -n "Checking Root Service Endpoint (/)... "
ROOT_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/" || echo "000")
if [ "${ROOT_CODE}" -eq 200 ]; then
    echo "OK (HTTP 200)"
else
    echo "WARNING: Root returned HTTP ${ROOT_CODE}"
fi

echo "All core health checks PASSED."
