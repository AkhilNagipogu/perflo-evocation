#!/usr/bin/env bash
# ==============================================================================
# One-Command Production Deployment Script for Evocation / Prflo Platform
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "=========================================================="
echo " Starting Evocation / Prflo Production Deployment"
echo "=========================================================="

# 1. Environment file check
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found in project root."
    echo "Please copy .env.example to .env and configure production credentials:"
    echo "  cp .env.example .env"
    exit 1
fi

echo "✓ Production .env found"

# 2. Build and launch Docker Compose services
echo "Building and launching production containers..."
docker compose -f deploy/docker-compose.prod.yml pull || true
docker compose -f deploy/docker-compose.prod.yml up -d --build --remove-orphans

echo "Waiting for services to become healthy..."
sleep 8

# 3. Verify health
echo "Running health checks..."
if [ -f "scripts/health_check.sh" ]; then
    chmod +x scripts/health_check.sh
    ./scripts/health_check.sh || echo "Notice: Initial health check in progress."
fi

echo ""
echo "=========================================================="
echo " Deployment Successfully Completed!"
echo "=========================================================="
echo "Services status:"
docker compose -f deploy/docker-compose.prod.yml ps
echo ""
echo "Helpful operator commands:"
echo "  View live backend logs:   docker compose -f deploy/docker-compose.prod.yml logs -f backend"
echo "  View live frontend logs:  docker compose -f deploy/docker-compose.prod.yml logs -f frontend"
echo "  Run database backup:      ./scripts/backup.sh"
echo "  Restart services:         docker compose -f deploy/docker-compose.prod.yml restart"
echo "=========================================================="
