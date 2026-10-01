"""
Management command to migrate data from SQLite to PostgreSQL.
Usage: python manage.py migrate_sqlite_to_postgres --sqlite-path /path/to/db.sqlite3
"""
import sqlite3
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection

from tourist.models import (
    User, Category, Destination, DestinationImage, Hotel, Restaurant,
    Review, Favorite, TravelPlan, EmergencyContact, Alert,
)


class Command(BaseCommand):
    help = "Migrate data from SQLite to PostgreSQL"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sqlite-path",
            type=str,
            default="db.sqlite3",
            help="Path to the SQLite database file",
        )

    def handle(self, *args, **options):
        sqlite_path = Path(options["sqlite_path"])

        if not sqlite_path.exists():
            self.stderr.write(self.style.ERROR(f"SQLite database not found: {sqlite_path}"))
            return

        self.stdout.write(f"Migrating data from {sqlite_path}...")

        # Connect to SQLite
        sqlite_conn = sqlite3.connect(str(sqlite_path))
        sqlite_conn.row_factory = sqlite3.Row
        cursor = sqlite_conn.cursor()

        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        self.stdout.write(f"Found {len(tables)} tables in SQLite")

        # Migrate data
        migrated = 0

        # Users
        if "tourist_user" in tables:
            cursor.execute("SELECT * FROM tourist_user")
            rows = cursor.fetchall()
            self.stdout.write(f"  Migrating {len(rows)} users...")
            for row in rows:
                try:
                    User.objects.using("default").update_or_create(
                        id=row["id"],
                        defaults={
                            "email": row["email"],
                            "first_name": row.get("first_name", ""),
                            "last_name": row.get("last_name", ""),
                            "password": row["password"],
                            "role": row.get("role", "tourist"),
                            "is_active": bool(row.get("is_active", 1)),
                            "is_staff": bool(row.get("is_staff", 0)),
                            "is_superuser": bool(row.get("is_superuser", 0)),
                            "is_verified": bool(row.get("is_verified", 0)),
                            "date_joined": row.get("date_joined", "2026-01-01 00:00:00"),
                            "last_login": row.get("last_login"),
                        },
                    )
                    migrated += 1
                except Exception as e:
                    self.stderr.write(f"    Error migrating user {row['id']}: {e}")

        # Categories
        if "tourist_category" in tables:
            cursor.execute("SELECT * FROM tourist_category")
            rows = cursor.fetchall()
            self.stdout.write(f"  Migrating {len(rows)} categories...")
            for row in rows:
                try:
                    Category.objects.using("default").update_or_create(
                        id=row["id"],
                        defaults={
                            "name": row["name"],
                            "slug": row["slug"],
                            "description": row.get("description", ""),
                            "is_active": bool(row.get("is_active", 1)),
                        },
                    )
                    migrated += 1
                except Exception as e:
                    self.stderr.write(f"    Error migrating category {row['id']}: {e}")

        # Destinations
        if "tourist_destination" in tables:
            cursor.execute("SELECT * FROM tourist_destination")
            rows = cursor.fetchall()
            self.stdout.write(f"  Migrating {len(rows)} destinations...")
            for row in rows:
                try:
                    category_id = row.get("category_id")
                    category = None
                    if category_id:
                        try:
                            category = Category.objects.using("default").get(id=category_id)
                        except Category.DoesNotExist:
                            pass

                    Destination.objects.using("default").update_or_create(
                        id=row["id"],
                        defaults={
                            "name": row["name"],
                            "slug": row["slug"],
                            "description": row.get("description", ""),
                            "category": category,
                            "district": row.get("district", ""),
                            "province": row.get("province", ""),
                            "latitude": row.get("latitude", 0.0),
                            "longitude": row.get("longitude", 0.0),
                            "is_published": bool(row.get("is_published", 1)),
                            "is_featured": bool(row.get("is_featured", 0)),
                            "cover_image": row.get("cover_image", ""),
                            "created_at": row.get("created_at", "2026-01-01 00:00:00"),
                            "updated_at": row.get("updated_at", "2026-01-01 00:00:00"),
                        },
                    )
                    migrated += 1
                except Exception as e:
                    self.stderr.write(f"    Error migrating destination {row['id']}: {e}")

        # Destination Images
        if "tourist_destinationimage" in tables:
            cursor.execute("SELECT * FROM tourist_destinationimage")
            rows = cursor.fetchall()
            self.stdout.write(f"  Migrating {len(rows)} destination images...")
            for row in rows:
                try:
                    destination_id = row.get("destination_id")
                    destination = None
                    if destination_id:
                        try:
                            destination = Destination.objects.using("default").get(id=destination_id)
                        except Destination.DoesNotExist:
                            pass

                    if destination:
                        DestinationImage.objects.using("default").update_or_create(
                            id=row["id"],
                            defaults={
                                "destination": destination,
                                "image_path": row.get("image_path", ""),
                                "caption": row.get("caption", ""),
                                "is_cover": bool(row.get("is_cover", 0)),
                                "verification_status": row.get("verification_status", "pending"),
                                "is_verified": bool(row.get("is_verified", 0)),
                                "ordering": row.get("ordering", 0),
                            },
                        )
                        migrated += 1
                except Exception as e:
                    self.stderr.write(f"    Error migrating image {row['id']}: {e}")

        # Hotels
        if "tourist_hotel" in tables:
            cursor.execute("SELECT * FROM tourist_hotel")
            rows = cursor.fetchall()
            self.stdout.write(f"  Migrating {len(rows)} hotels...")
            for row in rows:
                try:
                    Hotel.objects.using("default").update_or_create(
                        id=row["id"],
                        defaults={
                            "name": row["name"],
                            "slug": row["slug"],
                            "description": row.get("description", ""),
                            "address": row.get("address", ""),
                            "district": row.get("district", ""),
                            "province": row.get("province", ""),
                            "phone": row.get("phone", ""),
                            "email": row.get("email", ""),
                            "website": row.get("website", ""),
                            "latitude": row.get("latitude", 0.0),
                            "longitude": row.get("longitude", 0.0),
                            "star_rating": row.get("star_rating", 0),
                            "is_active": bool(row.get("is_active", 1)),
                        },
                    )
                    migrated += 1
                except Exception as e:
                    self.stderr.write(f"    Error migrating hotel {row['id']}: {e}")

        # Restaurants
        if "tourist_restaurant" in tables:
            cursor.execute("SELECT * FROM tourist_restaurant")
            rows = cursor.fetchall()
            self.stdout.write(f"  Migrating {len(rows)} restaurants...")
            for row in rows:
                try:
                    Restaurant.objects.using("default").update_or_create(
                        id=row["id"],
                        defaults={
                            "name": row["name"],
                            "slug": row["slug"],
                            "description": row.get("description", ""),
                            "address": row.get("address", ""),
                            "district": row.get("district", ""),
                            "province": row.get("province", ""),
                            "phone": row.get("phone", ""),
                            "cuisine_type": row.get("cuisine_type", ""),
                            "price_range": row.get("price_range", ""),
                            "latitude": row.get("latitude", 0.0),
                            "longitude": row.get("longitude", 0.0),
                            "is_active": bool(row.get("is_active", 1)),
                        },
                    )
                    migrated += 1
                except Exception as e:
                    self.stderr.write(f"    Error migrating restaurant {row['id']}: {e}")

        # Reviews
        if "tourist_review" in tables:
            cursor.execute("SELECT * FROM tourist_review")
            rows = cursor.fetchall()
            self.stdout.write(f"  Migrating {len(rows)} reviews...")
            for row in rows:
                try:
                    user_id = row.get("user_id")
                    destination_id = row.get("destination_id")
                    user = None
                    destination = None
                    if user_id:
                        try:
                            user = User.objects.using("default").get(id=user_id)
                        except User.DoesNotExist:
                            pass
                    if destination_id:
                        try:
                            destination = Destination.objects.using("default").get(id=destination_id)
                        except Destination.DoesNotExist:
                            pass

                    if user and destination:
                        Review.objects.using("default").update_or_create(
                            id=row["id"],
                            defaults={
                                "user": user,
                                "destination": destination,
                                "rating": row.get("rating", 5),
                                "comment": row.get("comment", ""),
                                "is_approved": bool(row.get("is_approved", 1)),
                                "created_at": row.get("created_at", "2026-01-01T00:00:00Z"),
                            },
                        )
                        migrated += 1
                except Exception as e:
                    self.stderr.write(f"    Error migrating review {row['id']}: {e}")

        # Emergency Contacts
        if "tourist_emergencycontact" in tables:
            cursor.execute("SELECT * FROM tourist_emergencycontact")
            rows = cursor.fetchall()
            self.stdout.write(f"  Migrating {len(rows)} emergency contacts...")
            for row in rows:
                try:
                    EmergencyContact.objects.using("default").update_or_create(
                        id=row["id"],
                        defaults={
                            "name": row["name"],
                            "phone_number": row.get("phone_number", ""),
                            "contact_type": row.get("contact_type", "general"),
                            "district": row.get("district", ""),
                            "province": row.get("province", ""),
                            "is_active": bool(row.get("is_active", 1)),
                        },
                    )
                    migrated += 1
                except Exception as e:
                    self.stderr.write(f"    Error migrating contact {row['id']}: {e}")

        # Alerts
        if "tourist_alert" in tables:
            cursor.execute("SELECT * FROM tourist_alert")
            rows = cursor.fetchall()
            self.stdout.write(f"  Migrating {len(rows)} alerts...")
            for row in rows:
                try:
                    Alert.objects.using("default").update_or_create(
                        id=row["id"],
                        defaults={
                            "title": row["title"],
                            "description": row.get("description", ""),
                            "severity": row.get("severity", "low"),
                            "alert_type": row.get("alert_type", "general"),
                            "district": row.get("district", ""),
                            "province": row.get("province", ""),
                            "is_active": bool(row.get("is_active", 1)),
                            "created_at": row.get("created_at", "2026-01-01T00:00:00Z"),
                        },
                    )
                    migrated += 1
                except Exception as e:
                    self.stderr.write(f"    Error migrating alert {row['id']}: {e}")

        sqlite_conn.close()
        self.stdout.write(self.style.SUCCESS(f"Migration complete! {migrated} records migrated."))
