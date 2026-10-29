#!/usr/bin/env bash
# ==============================================================================
# Automated PostgreSQL Backup Script for Evocation Platform
# Creates compressed, timestamped database dumps and cleans older backups.
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/evocation}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/evocation_${TIMESTAMP}.sql.gz"

CONTAINER_NAME="${POSTGRES_CONTAINER:-evocation-postgres-prod}"
DB_USER="${POSTGRES_USER:-evocation}"
DB_NAME="${POSTGRES_DB:-evocation}"

mkdir -p "${BACKUP_DIR}"

echo "Starting backup for database '${DB_NAME}' at $(date)..."

# Run pg_dump inside docker container and gzip stream
docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip -9 > "${BACKUP_FILE}"

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "Backup successfully created: ${BACKUP_FILE} (Size: ${BACKUP_SIZE})"

# Enforce retention policy
echo "Removing backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -name "evocation_*.sql.gz" -mtime +"${RETENTION_DAYS}" -delete

echo "Backup routine completed at $(date)."
