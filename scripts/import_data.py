#!/usr/bin/env python3
"""Import data from various formats.

Supports:
- JSON (Django fixtures)
- CSV (per table)
- SQL (PostgreSQL dump)

Usage:
    python scripts/import_data.py --input data.json
    python scripts/import_data.py --input exports/ --format csv
    python scripts/import_data.py --input dump.sql --format sql
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
from django.db import connection, transaction


def import_json(input_file):
    """Import from JSON fixture."""
    print(f"Importing from JSON: {input_file}")
    call_command('loaddata', input_file, verbosity=2)
    print(f"✓ Imported from {input_file}")


def import_csv(input_dir):
    """Import from CSV files."""
    input_dir = Path(input_dir)

    tables = [
        ('destinations', 'tourist_destination'),
        ('hotels', 'tourist_hotel'),
        ('hospitals', 'tourist_hospital'),
        ('police_stations', 'tourist_policestation'),
        ('restaurants', 'tourist_restaurant'),
    ]

    for file_name, table_name in tables:
        csv_file = input_dir / f"{file_name}.csv"
        if not csv_file.exists():
            print(f"  ⚠ Skipping {csv_file} (not found)")
            continue

        print(f"Importing {csv_file}...")
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            print(f"  ⚠ No rows in {csv_file}")
            continue

        # Build INSERT statement
        columns = list(rows[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join(columns)

        with transaction.atomic():
            with connection.cursor() as cur:
                for row in rows:
                    values = [row[col] for col in columns]
                    cur.execute(
                        f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})",
                        values
                    )

        print(f"  ✓ {len(rows)} rows imported")


def import_sql(input_file):
    """Import from SQL dump."""
    print(f"Importing from SQL: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    with connection.cursor() as cur:
        cur.execute(sql)

    print(f"✓ Imported from {input_file}")


def main():
    parser = argparse.ArgumentParser(description='Import data')
    parser.add_argument('--input', required=True, help='Input file or directory')
    parser.add_argument('--format', choices=['json', 'csv', 'sql'], default='json')
    args = parser.parse_args()

    print("=" * 60)
    print("  DATA IMPORT")
    print("=" * 60)

    if args.format == 'json':
        import_json(args.input)
    elif args.format == 'csv':
        import_csv(args.input)
    elif args.format == 'sql':
        import_sql(args.input)

    print("\n" + "=" * 60)
    print("  IMPORT COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
