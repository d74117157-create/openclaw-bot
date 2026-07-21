#!/bin/bash
set -euo pipefail

BACKUP_DIR="/home/opc/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

echo "💾 Backing up OpenClaw..."

# Database backup
docker exec openclaw_db_1 pg_dump -U openclaw openclaw > "$BACKUP_DIR/db_$TIMESTAMP.sql"

# App data backup
tar czf "$BACKUP_DIR/app_data_$TIMESTAMP.tar.gz" /home/opc/openclaw/data/

# Clean old backups (keep 7 days)
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup complete: $BACKUP_DIR/db_$TIMESTAMP.sql"
