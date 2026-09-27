"""Tests for cross-place image reuse detection.

The property that matters: two different sizes of the same photograph must be
recognised as one image, or the audit invents reuse that does not exist. And a
blank image reference must never be treated as a shared image, or every
imageless row collapses into one enormous false positive.
"""
from __future__ import annotations

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from tourist.management.commands.audit_cross_place_images import (
    is_defect,
    normalise_image_url,
)
from tourist.models import Category, Destination, DestinationImage, Hotel


class NormaliseImageUrlTests(TestCase):
    def test_blank_reference_is_blank(self):
        """Blank must never become a cache key, or every imageless row
        collides into one giant false 'shared image'."""
        for value in ("", "   ", None):
            self.assertEqual(normalise_image_url(value), "")

    def test_size_variants_collapse_to_one_image(self):
        base = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Phulchoki.jpg/640px-Phulchoki.jpg"
        wide = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Phulchoki.jpg/1024px-Phulchoki.jpg"
        self.assertEqual(normalise_image_url(base), normalise_image_url(wide))

    def test_different_photographs_do_not_collapse(self):
        a = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Phulchoki.jpg/640px-Phulchoki.jpg"
        b = "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Gorkha.jpg/640px-Gorkha.jpg"
        self.assertNotEqual(normalise_image_url(a), normalise_image_url(b))

    def test_query_string_is_ignored(self):
        a = "https://images.example/photo.jpg?w=800"
        b = "https://images.example/photo.jpg?w=1200"
        self.assertEqual(normalise_image_url(a), normalise_image_url(b))

    def test_host_is_part_of_identity(self):
        a = "https://images.example/photo.jpg"
        b = "https://other.example/photo.jpg"
        self.assertNotEqual(normalise_image_url(a), normalise_image_url(b))

    def test_image_path_is_usable_as_an_identity(self):
        """A bare image-server path keeps its shape, so a hotel cover_image
        and a destination image_path for the same file compare equal."""
        self.assertEqual(
            normalise_image_url("nepal/pokhara/fewatal.jpg"),
            normalise_image_url("/nepal/pokhara/fewatal.jpg"),
        )


class SeverityTests(TestCase):
    def _reuse(self, dests=0, hotels=0):
        from tourist.management.commands.audit_cross_place_images import Reuse

        entry = Reuse(image="x")
        entry.destination_ids = set(range(dests))
        entry.hotel_ids = set(range(1000, 1000 + hotels))
        return entry

    def test_one_place_is_not_a_defect(self):
        self.assertFalse(is_defect(self._reuse(dests=1), threshold=3))

    def test_four_places_crosses_the_threshold(self):
        self.assertTrue(is_defect(self._reuse(dests=4), threshold=3))

    def test_hotel_showing_a_destination_photo_is_always_a_defect(self):
        """A category error, not a judgement call: reported at any threshold."""
        entry = self._reuse(dests=1, hotels=1)
        self.assertTrue(is_defect(entry, threshold=99))

    def test_two_places_is_ambiguous_not_a_defect_at_threshold_three(self):
        self.assertFalse(is_defect(self._reuse(dests=2), threshold=3))

    def test_severity_labels(self):
        self.assertEqual(self._reuse(dests=1).severity, "unique")
        self.assertEqual(self._reuse(dests=2).severity, "reused_by_2")
        self.assertEqual(self._reuse(dests=4).severity, "reused_by_3_plus")
        self.assertEqual(self._reuse(dests=1, hotels=1).severity, "destination_photo_on_hotel")


class AuditCommandTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Image Category")
        self.pokhara = Destination.objects.create(
            name="Phewa Lake", slug="phewa-lake", category=category, district="Kaski",
            source="wikidata", external_id=9001,
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
            latitude="28.209600", longitude="83.985600",
        )
        self.gorkha = Destination.objects.create(
            name="Gorkha Durbar", slug="gorkha-durbar", category=category, district="Gorkha",
            source="wikidata", external_id=9002,
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
            latitude="28.000000", longitude="84.630000",
        )
        self.own = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Own.jpg/800px-Own.jpg"

    def _image(self, destination, url, is_cover=False):
        return DestinationImage.objects.create(
            destination=destination, external_url=url, is_cover=is_cover,
            source=DestinationImage.Source.WIKIMEDIA, alt_text="",
        )

    def _run(self, *args, **kwargs):
        out = StringIO()
        call_command("audit_cross_place_images", *args, stdout=out, stderr=out, **kwargs)
        return out.getvalue()

    def test_reuse_across_destinations_is_reported(self):
        shared = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Kathmandu.jpg"
        self._image(self.pokhara, shared)
        self._image(self.gorkha, shared)
        self._image(self.pokhara, self.own)
        output = self._run()
        self.assertIn("images attached to >1 place: 1", output)
        self.assertIn("reused_by_2", output)
        self.assertIn("destinations affected    : 2", output)

    def test_size_variants_on_one_place_are_one_image_not_reuse(self):
        """Two widths of one photograph on the SAME place must collapse to a
        single image. Counting them as reuse would invent a finding."""
        self._image(
            self.pokhara,
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Own.jpg/640px-Own.jpg",
        )
        self._image(
            self.pokhara,
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Own.jpg/1024px-Own.jpg",
        )
        output = self._run()
        self.assertIn("distinct images in use   : 1", output)
        self.assertIn("images attached to >1 place: 0", output)

    def test_same_photo_on_two_places_is_real_reuse(self):
        """The counterpart: different widths, different places, one photo."""
        self._image(
            self.pokhara,
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Own.jpg/640px-Own.jpg",
        )
        self._image(
            self.gorkha,
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Own.jpg/1024px-Own.jpg",
        )
        output = self._run()
        self.assertIn("images attached to >1 place: 1", output)

    def test_hotel_showing_destination_image_is_flagged(self):
        self._image(self.pokhara, self.own)
        Hotel.objects.create(
            destination=self.pokhara, name="Hotel Phewa View", phone="",
            external_image_url=self.own, is_active=True,
        )
        output = self._run()
        self.assertIn("destination_photo_on_hotel", output)
        self.assertIn("hotels affected          : 1", output)

    def test_multiple_covers_are_reported(self):
        self._image(self.pokhara, self.own, is_cover=True)
        self._image(self.pokhara, self.own + "?v=2", is_cover=True)
        output = self._run()
        self.assertIn("destinations with more than one cover row: 1", output)

    def test_command_changes_nothing(self):
        shared = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Shared.jpg"
        self._image(self.pokhara, shared)
        self._image(self.gorkha, shared)
        before = list(
            DestinationImage.objects.values_list("id", "external_url", "is_cover", "source")
        )
        self._run(per_place=True)
        after = list(
            DestinationImage.objects.values_list("id", "external_url", "is_cover", "source")
        )
        self.assertEqual(before, after)

    def test_tsv_export_lists_every_affected_row(self):
        shared = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Shared.jpg"
        self._image(self.pokhara, shared)
        self._image(self.gorkha, shared)
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reuse.tsv"
            output = self._run(tsv=str(path))
            self.assertIn("TSV written", output)
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 3)  # header + 2 rows
            self.assertIn("severity", lines[0])
