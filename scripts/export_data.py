#!/usr/bin/env python3
"""Export data in various formats.

Supports:
- JSON (Django fixtures)
- CSV (per table)
- SQL (PostgreSQL dump)

Usage:
    python scripts/export_data.py --format json --output data.json
    python scripts/export_data.py --format csv --output exports/
    python scripts/export_data.py --format sql --output dump.sql
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Tourism"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django
django.setup()

from django.core.management import call_command
from django.db import connection


def export_json(output):
    """Export to JSON fixture."""
    print(f"Exporting to JSON: {output}")
    with open(output, 'w', encoding='utf-8') as f:
        call_command(
            'dumpdata',
            '--exclude', 'contenttypes',
            '--exclude', 'auth.permission',
            '--exclude', 'admin.logentry',
            '--exclude', 'sessions',
            '--exclude', 'token_blacklist',
            '--natural-foreign',
            '--natural-primary',
            '--indent', '2',
            stdout=f,
        )
    print(f"✓ Exported to {output}")


def export_csv(output_dir):
    """Export to CSV files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tables = [
        ('tourist_destination', 'destinations'),
        ('tourist_hotel', 'hotels'),
        ('tourist_hospital', 'hospitals'),
        ('tourist_policestation', 'police_stations'),
        ('tourist_restaurant', 'restaurants'),
        ('tourist_managedpage', 'cms_pages'),
    ]

    for table_name, file_name in tables:
        print(f"Exporting {table_name} to CSV...")
        with connection.cursor() as cur:
            cur.execute(f"SELECT * FROM {table_name}")
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        output_file = output_dir / f"{file_name}.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)

        print(f"  ✓ {len(rows)} rows -> {output_file}")


def export_sql(output):
    """Export to SQL dump."""
    print(f"Exporting to SQL: {output}")
    # Use pg_dump for PostgreSQL
    if connection.vendor == 'postgresql':
        import subprocess
        db = connection.settings_dict
        cmd = [
            'pg_dump',
            '--host', db['HOST'],
            '--port', str(db['PORT']),
            '--username', db['USER'],
            '--dbname', db['NAME'],
            '--file', output,
        ]
        env = os.environ.copy()
        env['PGPASSWORD'] = db['PASSWORD']
        subprocess.run(cmd, env=env, check=True)
    else:
        # For SQLite, just copy the file
        import shutil
        src = connection.settings_dict['NAME']
        shutil.copy2(src, output)
    print(f"✓ Exported to {output}")


def main():
    parser = argparse.ArgumentParser(description='Export data')
    parser.add_argument('--format', choices=['json', 'csv', 'sql'], default='json')
    parser.add_argument('--output', default='data.json')
    args = parser.parse_args()

    print("=" * 60)
    print("  DATA EXPORT")
    print("=" * 60)

    if args.format == 'json':
        export_json(args.output)
    elif args.format == 'csv':
        export_csv(args.output)
    elif args.format == 'sql':
        export_sql(args.output)

    print("\n" + "=" * 60)
    print("  EXPORT COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
