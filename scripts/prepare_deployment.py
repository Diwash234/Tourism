#!/usr/bin/env python3
"""Prepare the project for Render deployment.

This script:
1. Exports database data to load.json
2. Verifies the frontend build exists
3. Checks all required files are present
4. Runs Django system checks
5. Creates a deployment summary

Usage:
    python scripts/prepare_deployment.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

# Add the project to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Tourism"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django
django.setup()

from django.conf import settings
from django.core.management import call_command


def run_command(cmd, description):
    """Run a shell command and report the result."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  ✓ Success")
        if result.stdout:
            print(f"  {result.stdout[:500]}")
    else:
        print(f"  ✗ Failed")
        print(f"  Error: {result.stderr[:500]}")
    return result.returncode == 0


def check_file(path, description):
    """Check if a file exists."""
    if path.exists():
        size = path.stat().st_size
        print(f"  ✓ {description}: {path.name} ({size:,} bytes)")
        return True
    else:
        print(f"  ✗ {description}: {path.name} MISSING")
        return False


def main():
    print("=" * 60)
    print("  RENDER DEPLOYMENT PREPARATION")
    print("=" * 60)

    all_ok = True

    # 1. Check required files
    print("\n[1/6] Checking required files...")
    required_files = [
        (PROJECT_ROOT / "Dockerfile", "Dockerfile"),
        (PROJECT_ROOT / "render.yaml", "Render config"),
        (PROJECT_ROOT / "docker" / "entrypoint.sh", "Entrypoint script"),
        (PROJECT_ROOT / "Tourism" / "requirements.txt", "Python dependencies"),
        (PROJECT_ROOT / "downloads" / "nepal-tourism-seed.sqlite3.gz", "Seed database"),
    ]
    for path, desc in required_files:
        if not check_file(path, desc):
            all_ok = False

    # 2. Check frontend build
    print("\n[2/6] Checking frontend build...")
    frontend_dist = settings.FRONTEND_DIST_DIR
    index_html = frontend_dist / "index.html"
    if check_file(index_html, "Frontend build"):
        # Check for assets
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            asset_count = len(list(assets_dir.rglob("*")))
            print(f"  ✓ Assets: {asset_count} files")
        else:
            print(f"  ⚠ No assets directory found")
    else:
        all_ok = False
        print("  Run: cd frontend/Tourism && npm run build")

    # 3. Export database data
    print("\n[3/6] Exporting database data...")
    load_json = PROJECT_ROOT / "Tourism" / "load.json"
    try:
        with load_json.open("w", encoding="utf-8") as stream:
            call_command(
                "dumpdata",
                "--exclude", "contenttypes",
                "--exclude", "auth.permission",
                "--exclude", "admin.logentry",
                "--exclude", "sessions",
                "--exclude", "token_blacklist",
                "--natural-foreign",
                "--natural-primary",
                "--indent", "2",
                stdout=stream,
            )
        size_mb = load_json.stat().st_size / (1024 * 1024)
        print(f"  ✓ Exported to load.json ({size_mb:.1f} MB)")
    except Exception as exc:
        print(f"  ✗ Export failed: {exc}")
        all_ok = False

    # 4. Run Django checks
    print("\n[4/6] Running Django system checks...")
    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy"],
        cwd=PROJECT_ROOT / "Tourism",
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"  ✓ Django checks passed")
    else:
        print(f"  ⚠ Django checks found issues:")
        print(f"  {result.stdout[:1000]}")

    # 5. Verify database
    print("\n[5/6] Verifying database...")
    try:
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM tourist_destination")
            dest_count = cur.fetchone()[0]
            print(f"  ✓ Destinations: {dest_count}")

            cur.execute("SELECT COUNT(*) FROM tourist_destinationimage")
            img_count = cur.fetchone()[0]
            print(f"  ✓ Images: {img_count}")

            cur.execute("SELECT COUNT(*) FROM tourist_hotel")
            hotel_count = cur.fetchone()[0]
            print(f"  ✓ Hotels: {hotel_count}")
    except Exception as exc:
        print(f"  ✗ Database error: {exc}")
        all_ok = False

    # 6. Create deployment summary
    print("\n[6/6] Creating deployment summary...")
    summary = {
        "project": "Nepal Yatra Tourism Portal",
        "timestamp": str(Path(PROJECT_ROOT).stat().st_mtime),
        "database": {
            "vendor": connection.vendor,
            "destinations": dest_count,
            "images": img_count,
            "hotels": hotel_count,
        },
        "frontend": {
            "build_present": index_html.is_file(),
            "assets_count": len(list((frontend_dist / "assets").rglob("*"))) if (frontend_dist / "assets").exists() else 0,
        },
        "files": {
            "load_json": load_json.exists(),
            "load_json_size_mb": round(load_json.stat().st_size / (1024 * 1024), 1) if load_json.exists() else 0,
        },
        "all_checks_passed": all_ok,
    }

    summary_path = PROJECT_ROOT / "deployment_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  ✓ Summary saved to deployment_summary.json")

    # Final report
    print("\n" + "=" * 60)
    if all_ok:
        print("  ✓ ALL CHECKS PASSED - READY FOR DEPLOYMENT")
    else:
        print("  ⚠ SOME CHECKS FAILED - REVIEW ABOVE")
    print("=" * 60)

    print("\nNext steps:")
    print("  1. Commit changes: git add -A && git commit -m 'Prepare deployment'")
    print("  2. Push to GitHub: git push origin main")
    print("  3. Render will auto-deploy")
    print("  4. Verify: curl https://your-app.onrender.com/health/")
    print()

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
