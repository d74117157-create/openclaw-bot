#!/bin/bash
# OpenClaw Database & State Backup Script
# Run via cron: 0 3 * * * /app/devops/scripts/backup.sh

set -euo pipefail

BACKUP_DIR="/app/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p "${BACKUP_DIR}"

# Backup PostgreSQL
if command -v pg_dump &> /dev/null; then
    pg_dump -h db -U openclaw openclaw > "${BACKUP_DIR}/db_${TIMESTAMP}.sql"
    gzip "${BACKUP_DIR}/db_${TIMESTAMP}.sql"
    echo "Database backup complete: db_${TIMESTAMP}.sql.gz"
fi

# Backup Redis
if command -v redis-cli &> /dev/null; then
    redis-cli -h redis SAVE
    cp /data/dump.rdb "${BACKUP_DIR}/redis_${TIMESTAMP}.rdb"
    echo "Redis backup complete: redis_${TIMESTAMP}.rdb"
fi

# Backup Guardian state
if [ -f ".guardian_state.json" ]; then
    cp .guardian_state.json "${BACKUP_DIR}/guardian_state_${TIMESTAMP}.json"
fi

# Cleanup old backups
find "${BACKUP_DIR}" -type f -mtime +${RETENTION_DAYS} -delete
echo "Cleanup complete. Retention: ${RETENTION_DAYS} days"
