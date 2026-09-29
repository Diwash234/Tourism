#!/bin/bash
# Maintenance script for production deployment
# Usage: ./scripts/maintenance.sh [command]

set -e

COMMAND=${1:-help}

case "$COMMAND" in
    backup)
        echo "Creating database backup..."
        python manage.py backup_database
        echo "Backup complete."
        ;;

    verify)
        echo "Running deployment verification..."
        python manage.py verify_deployment
        ;;

    health)
        echo "Checking data health..."
        python scripts/check_data_health.py
        ;;

    fix)
        echo "Fixing common issues..."
        python scripts/fix_common_issues.py
        ;;

    prepare)
        echo "Preparing deployment..."
        python scripts/prepare_deployment.py
        ;;

    clean)
        echo "Cleaning up old backups..."
        find . -name "*.before-seed-*" -mtime +7 -delete
        find . -name "backup_*.sql" -mtime +30 -delete
        echo "Cleanup complete."
        ;;

    update)
        echo "Updating dependencies..."
        pip install --upgrade pip
        pip install -r Tourism/requirements.txt --upgrade
        echo "Update complete."
        ;;

    test)
        echo "Running tests..."
        cd Tourism
        python manage.py test --verbosity=2
        ;;

    help|*)
        echo "Maintenance commands:"
        echo "  backup   - Create database backup"
        echo "  verify   - Run deployment verification"
        echo "  health   - Check data health"
        echo "  fix      - Fix common data issues"
        echo "  prepare  - Prepare for deployment"
        echo "  clean    - Clean up old backups"
        echo "  update   - Update dependencies"
        echo "  test     - Run tests"
        echo ""
        echo "Usage: ./scripts/maintenance.sh [command]"
        ;;
esac
