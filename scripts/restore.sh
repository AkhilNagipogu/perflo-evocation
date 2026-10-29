#!/usr/bin/env bash
# ==============================================================================
# PostgreSQL Database Restore Script for Evocation Platform
# Usage: ./scripts/restore.sh /path/to/backup_file.sql.gz
# ==============================================================================

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file '${BACKUP_FILE}' does not exist."
    exit 1
fi

CONTAINER_NAME="${POSTGRES_CONTAINER:-evocation-postgres-prod}"
DB_USER="${POSTGRES_USER:-evocation}"
DB_NAME="${POSTGRES_DB:-evocation}"

echo "======================================================================"
echo "WARNING: You are about to restore database '${DB_NAME}' from:"
echo "${BACKUP_FILE}"
echo "This will OVERWRITE existing database contents."
echo "======================================================================"
read -p "Are you sure you want to proceed? (yes/no): " CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
    echo "Restore aborted by user."
    exit 0
fi

echo "Stopping application backend during restore..."
docker stop evocation-backend-prod || true

echo "Restoring database..."
gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}"

echo "Restarting application backend..."
docker start evocation-backend-prod || true

echo "Database restore completed successfully at $(date)."
