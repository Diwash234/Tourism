#!/bin/bash
# Backup script for production deployment
# Usage: ./scripts/backup.sh

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "=========================================="
echo "  Backup - $TIMESTAMP"
echo "=========================================="

# Database backup
echo "Backing up database..."
python manage.py backup_database

# Media files backup
echo "Backing up media files..."
tar -czf "$BACKUP_DIR/media_$TIMESTAMP.tar.gz" media/

# Static files backup
echo "Backing up static files..."
tar -czf "$BACKUP_DIR/static_$TIMESTAMP.tar.gz" staticfiles/

echo ""
echo "=========================================="
echo "  Backup Complete!"
echo "=========================================="
echo "Files saved to: $BACKUP_DIR"
echo ""
ls -lh "$BACKUP_DIR"
