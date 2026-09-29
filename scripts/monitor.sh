#!/bin/bash
# Monitor script for production deployment
# Usage: ./scripts/monitor.sh

set -e

echo "=========================================="
echo "  System Monitor"
echo "=========================================="
echo ""

# Check disk space
echo "Disk Space:"
df -h | grep -E '(Filesystem|/dev/)'
echo ""

# Check memory
echo "Memory:"
free -h 2>/dev/null || vm_stat 2>/dev/null || echo "  Memory info not available"
echo ""

# Check database connection
echo "Database:"
python -c "
import os, sys
sys.path.insert(0, 'Tourism')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
import django; django.setup()
from django.db import connection
try:
    with connection.cursor() as cur:
        cur.execute('SELECT 1')
        print(f'  ✓ Connected ({connection.vendor})')
except Exception as e:
    print(f'  ✗ Error: {e}')
"
echo ""

# Check API health
echo "API Health:"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/ 2>/dev/null || echo "000")
if [ "$HEALTH" = "200" ]; then
    echo "  ✓ API is responding"
else
    echo "  ✗ API is not responding (HTTP $HEALTH)"
fi
echo ""

# Check static files
echo "Static Files:"
if [ -d "staticfiles" ]; then
    COUNT=$(find staticfiles -type f | wc -l)
    echo "  ✓ $COUNT files"
else
    echo "  ✗ staticfiles directory not found"
fi
echo ""

# Check media files
echo "Media Files:"
if [ -d "media" ]; then
    COUNT=$(find media -type f | wc -l)
    echo "  ✓ $COUNT files"
else
    echo "  ✗ media directory not found"
fi
echo ""

echo "=========================================="
echo "  Monitor Complete"
echo "=========================================="
