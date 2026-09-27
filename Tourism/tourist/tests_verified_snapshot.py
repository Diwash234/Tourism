"""Regression tests for the privacy-safe canonical data snapshot."""
from datetime import datetime, timezone
import json
import tempfile
from pathlib import Path

from django.core.serializers.json import DjangoJSONEncoder
from django.test import TestCase

from tourist.models import Category, Destination, DestinationImage, Hotel, User
from tourist.verified_snapshot import (
    build_snapshot_payload,
    read_payload,
    sanitize_html_fragment,
    validate_payload,
    write_payload,
)


class VerifiedSnapshotTests(TestCase):
    fixed_cutoff = datetime(2026, 9, 25, 23, 59, 59, tzinfo=timezone.utc)

    def setUp(self):
        self.user = User.objects.create_user(
            email="snapshot-private@example.com",
            password="StrongPass123!",
        )
        self.category = Category.objects.create(name="Snapshot Test Category")
        self.destination = Destination.objects.create(
            external_id=987654321,
            name="Snapshot Verified Place",
            slug="snapshot-verified-place",
            category=self.category,
            description="A sourced public place.",
            source="OpenStreetMap",
            latitude=28.2096,
            longitude=83.9856,
            city="Pokhara",
            district="Kaski",
            country="Nepal",
            status=Destination.SubmissionStatus.APPROVED,
            is_active=True,
        )
        Destination.objects.create(
            name="E2E Lifecycle Place",
            slug="e2e-lifecycle-place",
            category=self.category,
            source="OpenStreetMap",
            latitude=28.21,
            longitude=83.99,
            status=Destination.SubmissionStatus.APPROVED,
            is_active=True,
        )
        Destination.objects.create(
            name="Unsourced Place",
            slug="unsourced-place",
            category=self.category,
            latitude=28.22,
            longitude=84.00,
            status=Destination.SubmissionStatus.APPROVED,
            is_active=True,
        )
        Destination.objects.create(
            name="Outside Nepal Place",
            slug="outside-nepal-place",
            external_id=987654322,
            category=self.category,
            source="OpenStreetMap",
            latitude=60.18,
            longitude=84.0,
            status=Destination.SubmissionStatus.APPROVED,
            is_active=True,
        )
        self.image = DestinationImage.objects.create(
            destination=self.destination,
            # The filename must name the place: the release now applies the same
            # destination-specificity rule the website does, so a generic
            # "Example.jpg" would (correctly) be treated as another place's
            # photo and excluded.
            external_url="https://upload.wikimedia.org/wikipedia/commons/3/3a/Snapshot_Verified_Place.jpg",
            thumbnail_url="https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Snapshot_Verified_Place.jpg/960px-Snapshot_Verified_Place.jpg",
            source_url="https://commons.wikimedia.org/wiki/File:Snapshot_Verified_Place.jpg",
            source="wikimedia",
            source_platform="Wikimedia Commons",
            license_type="CC BY-SA 4.0",
            photographer="Example photographer",
            alt_text="Snapshot Verified Place",
            is_verified=True,
            verification_status="approved",
            destination_match_score=0.95,
            authenticity_score=0.96,
        )
        # A score only counts once a named reviewer assigned it, so this fixture
        # records provenance. The reviewer foreign key itself never ships; the
        # timestamps are what a release can actually verify.
        self.reviewer = User.objects.create_user(
            email="snapshot-reviewer@example.com", password="ReviewerPass123!",
        )
        self.image.authenticity_score_by = self.reviewer
        self.image.authenticity_score_at = self.fixed_cutoff
        self.image.destination_match_score_by = self.reviewer
        self.image.destination_match_score_at = self.fixed_cutoff
        self.image.media_reviewed_by = self.reviewer
        self.image.media_reviewed_at = self.fixed_cutoff
        self.image.save()
        DestinationImage.objects.create(
            destination=self.destination,
            external_url="https://upload.wikimedia.org/wikipedia/commons/3/3b/Wrong.jpg",
            source_url="https://commons.wikimedia.org/wiki/File:Wrong.jpg",
            source="wikimedia",
            is_verified=True,
            verification_status="approved",
            destination_match_score=0.2,
            authenticity_score=0.99,
        )
        self.hotel = Hotel.objects.create(
            destination=self.destination,
            name="Snapshot Verified Hotel",
            address="Pokhara",
            source="manual",
            source_url="https://example.com/verified-hotel",
            is_verified=True,
            is_active=True,
        )
        Hotel.objects.create(
            destination=self.destination,
            name="Unverified Snapshot Hotel",
            source="dataset",
            latitude=28.21,
            longitude=83.96,
            is_active=True,
        )
        # Exact duplicate import of the unverified hotel (same name, coordinates
        # and destination): published once.
        Hotel.objects.create(
            destination=self.destination,
            name="Unverified  Snapshot Hotel",
            source="dataset",
            latitude=28.21,
            longitude=83.96,
            is_active=True,
        )
        Hotel.objects.create(
            destination=self.destination,
            name="Hotel Outside Nepal",
            source="dataset",
            latitude=51.5,
            longitude=-0.12,
            is_active=True,
        )

    def test_snapshot_excludes_private_synthetic_and_low_quality_records(self):
        payload = build_snapshot_payload(as_of=self.fixed_cutoff)
        validate_payload(payload)
        destination_names = {
            row["fields"]["name"]
            for row in payload["records"]
            if row["model"] == "tourist.destination"
        }
        self.assertIn(self.destination.name, destination_names)
        self.assertNotIn("E2E Lifecycle Place", destination_names)
        self.assertNotIn("Unsourced Place", destination_names)
        self.assertNotIn("Outside Nepal Place", destination_names)
        self.assertNotIn(
            self.user.email,
            json.dumps(payload, cls=DjangoJSONEncoder),
        )

        image_pks = {
            row["pk"] for row in payload["records"]
            if row["model"] == "tourist.destinationimage"
            and row["fields"].get("destination") == self.destination.pk
        }
        self.assertIn(self.image.pk, image_pks)
        self.assertEqual(len(image_pks), 1)

        hotel_rows = [row for row in payload["records"] if row["model"] == "tourist.hotel"]
        hotels = {row["fields"]["name"]: row["fields"] for row in hotel_rows}
        self.assertEqual(
            sum(1 for row in hotel_rows if " ".join(row["fields"]["name"].split()) == "Unverified Snapshot Hotel"), 1,
        )
        self.assertIn(self.hotel.name, hotels)
        # Policy v2: a sourced but unverified listing is published with its
        # flag intact (the UI labels it); it is never upgraded to verified.
        self.assertIn("Unverified Snapshot Hotel", hotels)
        self.assertIs(hotels["Unverified Snapshot Hotel"]["is_verified"], False)
        self.assertNotIn("Hotel Outside Nepal", hotels)

    def test_snapshot_json_round_trip_and_digest(self):
        payload = build_snapshot_payload(as_of=self.fixed_cutoff)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            write_payload(path, payload)
            loaded = read_payload(path)
        self.assertEqual(loaded["records_sha256"], payload["records_sha256"])
        self.assertEqual(loaded["counts"], payload["counts"])
        self.assertEqual(loaded["identity_policy"]["destination"].split(";")[0], "slug plus external_id")

    def test_snapshot_html_sanitizer_is_explicit(self):
        value = sanitize_html_fragment(
            '<p>Hello</p><script>alert(1)</script>'
            '<a href="javascript:alert(1)" onclick="bad()">link</a>'
            '<img src="data:text/html,bad" onerror="bad()">'
        )
        self.assertIn("<p>Hello</p>", value)
        self.assertNotIn("script", value.lower())
        self.assertNotIn("javascript:", value.lower())
        self.assertNotIn("onerror", value.lower())
        self.assertNotIn("onclick", value.lower())
