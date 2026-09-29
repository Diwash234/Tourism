#!/bin/bash
# Restore script for production deployment
# Usage: ./scripts/restore.sh <backup_file>

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/restore.sh <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/ 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "=========================================="
echo "  Restore from: $BACKUP_FILE"
echo "=========================================="

read -p "This will overwrite current data. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 1
fi

# Restore database
echo "Restoring database..."
python manage.py restore_database "$BACKUP_FILE"

echo ""
echo "=========================================="
echo "  Restore Complete!"
echo "=========================================="
