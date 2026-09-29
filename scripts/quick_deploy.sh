#!/bin/bash
# Quick deployment script for Render
# Usage: ./scripts/quick_deploy.sh

set -e

echo "=========================================="
echo "  Nepal Yatra - Quick Deploy"
echo "=========================================="

# Check if we're in a git repo
if [ ! -d .git ]; then
    echo "Error: Not a git repository"
    exit 1
fi

# Get current branch
BRANCH=$(git branch --show-current)
echo "Current branch: $BRANCH"

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Warning: You have uncommitted changes"
    read -p "Commit and push? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
        git commit -m "Deploy: $(date +%Y-%m-%d_%H:%M:%S)"
    else
        echo "Deploy cancelled"
        exit 1
    fi
fi

# Push to remote
echo "Pushing to origin/$BRANCH..."
git push origin "$BRANCH"

echo ""
echo "=========================================="
echo "  Deploy Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Check Render dashboard for build status"
echo "  2. Verify deployment: curl https://your-app.onrender.com/health/"
echo "  3. Check logs: render logs --service your-service-name"
echo ""
