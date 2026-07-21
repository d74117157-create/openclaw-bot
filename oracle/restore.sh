#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.sql>"
    exit 1
fi

BACKUP_FILE="$1"

echo "🔄 Restoring OpenClaw database..."

# Stop app
docker-compose -f /home/opc/openclaw/docker-compose.yml stop app

# Restore database
docker exec -i openclaw_db_1 psql -U openclaw openclaw < "$BACKUP_FILE"

# Restart
docker-compose -f /home/opc/openclaw/docker-compose.yml start app

echo "✅ Restore complete!"
