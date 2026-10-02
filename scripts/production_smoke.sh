#!/usr/bin/env bash
# scripts/production_smoke.sh — run automated smoke suite against target origin
set -euo pipefail

TARGET_URL="${1:-${SITE_URL:-${PUBLIC_SITE_URL:-http://127.0.0.1:8000}}}"
echo "Running Production Smoke Tests against: $TARGET_URL"

python3 "$(dirname "$0")/production_smoke.py" --base-url "$TARGET_URL"
