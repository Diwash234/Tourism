"""Tests for Commons-backed place-specific image repair.

The rules that matter are all refusals. A command that quietly attaches a
photo of the wrong place is worse than one that attaches nothing, so the
tests below are mostly about what gets *rejected*:

  * a Pokhara photo is never accepted for a place merely located in Pokhara;
  * a destination photo is never accepted as a hotel photo;
  * an unreusable licence is refused;
  * an unrecognised licence is refused (absence of evidence is not permission);
  * a proposal is never written as verified or approved;
  * nothing is written at all without --apply.
"""
from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

import requests
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase

from tourist.management.commands.repair_real_place_images import (
    licence_is_reusable,
    specificity,
    words,
)
from tourist.models import Category, Destination, DestinationImage, Hotel


class LicenceTests(TestCase):
    def test_known_reusable_licences_are_accepted(self):
        for value in ("CC BY-SA 4.0", "CC0", "Public domain", "CC BY 2.0", "GFDL"):
            self.assertTrue(licence_is_reusable(value), value)

    def test_non_reusable_licences_are_refused(self):
        for value in ("CC BY-NC-SA 4.0", "Non-free", "Copyright", "All rights reserved"):
            self.assertFalse(licence_is_reusable(value), value)

    def test_unknown_licence_is_refused(self):
        """Silence is not permission. An unlabelled file is not reusable."""
        self.assertFalse(licence_is_reusable(""))
        self.assertFalse(licence_is_reusable("   "))


class SpecificityTests(TestCase):
    CONTEXT = {"nepal", "pokhara", "kaski", "pokhara Metropolitan"}

    def test_naming_the_place_is_required(self):
        self.assertTrue(specificity(["Ghandruk"], "File:Ghandruk village.jpg", self.CONTEXT))

    def test_pure_city_hit_for_a_destination_is_refused(self):
        """'Ghandruk' must not be satisfied by a file that only says 'Pokhara'."""
        self.assertEqual(
            specificity(["Ghandruk"], "File:Pokhara lake and boats.jpg", self.CONTEXT),
            set(),
        )

    def test_partial_name_does_not_match(self):
        """'Phewa' must not match a file that merely contains 'lake'."""
        self.assertEqual(
            specificity(["Phewa Lake"], "File:Snowy lake in the mountains.jpg", self.CONTEXT),
            set(),
        )

    def test_full_name_match_is_accepted(self):
        self.assertTrue(specificity(["Phewa Lake"], "File:Phewa Lake at dawn.jpg", self.CONTEXT))

    def test_hotel_name_is_matched_on_its_own(self):
        self.assertTrue(
            specificity(["Barahi Jungle Lodge"], "File:Barahi Jungle Lodge.jpg", self.CONTEXT)
        )

    def test_generic_hotel_hit_is_refused(self):
        self.assertEqual(
            specificity(["Barahi Jungle Lodge"], "File:Lodge room.jpg", self.CONTEXT), set()
        )

    def test_city_photo_is_refused_for_a_hotel(self):
        self.assertEqual(
            specificity(["Barahi Jungle Lodge"],
                        "File:Pokhara skyline.jpg", self.CONTEXT), set()
        )

    def test_multiword_name_requires_every_token(self):
        self.assertEqual(
            specificity(["Hotel Barahi Pokhara"], "File:Hotel Barahi.jpg", self.CONTEXT), set()
        )
        self.assertTrue(
            specificity(["Hotel Barahi Pokhara"], "File:Hotel Barahi Pokhara.jpg", self.CONTEXT)
        )


def commons_response(rows, status=200):
    built = requests.Response()
    built.status_code = status
    pages = {}
    for index, row in enumerate(rows, start=1):
        pages[str(index)] = {
            "title": row["title"],
            "imageinfo": [{
                "url": row.get("image_url", "https://upload.wikimedia.org/x.jpg"),
                "thumburl": row.get("image_url", "https://upload.wikimedia.org/x.jpg"),
                "descriptionurl": row.get("page_url", "https://commons.wikimedia.org/wiki/File:x"),
                "extmetadata": {
                    "LicenseShortName": {"value": row.get("licence", "CC BY-SA 4.0")},
                    "Artist": {"value": "<a>Real Photographer</a>"},
                },
            }],
        }
    built._content = json.dumps({"query": {"pages": pages}}).encode("utf-8")
    built.headers["Content-Type"] = "application/json"
    return built


class RepairCommandTests(TestCase):
    def setUp(self):
        cache.clear()
        category = Category.objects.create(name="Repair Category")
        self.ghandruk = Destination.objects.create(
            name="Ghandruk", slug="ghandruk", category=category,
            district="Kaski", city="Pokhara", is_active=True,
            status=Destination.SubmissionStatus.APPROVED,
        )
        # A context photo wrongly serving the place: this is what gets replaced.
        DestinationImage.objects.create(
            destination=self.ghandruk,
            external_url="https://upload.wikimedia.org/commons/9/9a/Pokhara_lake.jpg",
            source=DestinationImage.Source.WIKIMEDIA,
        )
        self.ok_row = {
            "title": "File:Ghandruk from the ridge.jpg",
            "image_url": "https://upload.wikimedia.org/commons/1/1b/Ghandruk_ridge.jpg",
            "page_url": "https://commons.wikimedia.org/wiki/File:Ghandruk_from_the_ridge.jpg",
            "licence": "CC BY-SA 4.0",
        }
        self.pokhara_row = {
            "title": "File:Pokhara Lakeside.jpg",
            "image_url": "https://upload.wikimedia.org/commons/2/2c/Pokhara_Lakeside.jpg",
            "page_url": "https://commons.wikimedia.org/wiki/File:Pokhara_Lakeside.jpg",
            "licence": "CC BY-SA 4.0",
        }

    def _run(self, *args, **kwargs):
        # min_places=1 so a place whose image is shared with only itself is still
        # exercised; the production default of 2 is the honest "detectable
        # reuse" floor and is covered by the real-data run instead.
        kwargs.setdefault("min_places", 1)
        out = StringIO()
        call_command("repair_real_place_images", *args, stdout=out, stderr=out, **kwargs)
        return out.getvalue()

    def test_dry_run_writes_nothing(self):
        before = DestinationImage.objects.count()
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   return_value=commons_response([self.ok_row])):
            output = self._run(kind="destination", limit=5)
        self.assertIn("DRY RUN", output)
        self.assertEqual(DestinationImage.objects.count(), before)

    def test_place_specific_image_is_proposed_and_recorded(self):
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   return_value=commons_response([self.ok_row])):
            output = self._run(kind="destination", limit=5, apply=True)
        row = DestinationImage.objects.exclude(
            external_url__contains="Pokhara_lake").first()
        self.assertIsNotNone(row, "no new image was created")
        self.assertIn("Ghandruk_ridge", row.external_url)
        self.assertEqual(row.source, DestinationImage.Source.WIKIMEDIA)
        self.assertIn("commons.wikimedia.org", row.source_url)
        self.assertEqual(row.license_type, "CC BY-SA 4.0")
        self.assertIn("Real Photographer", row.photographer)

    def test_proposals_are_never_published_as_verified(self):
        """The model defaults these to APPROVED/True, which would publish a
        photo no human has seen as verified media."""
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   return_value=commons_response([self.ok_row])):
            self._run(kind="destination", limit=5, apply=True)
        row = DestinationImage.objects.exclude(
            external_url__contains="Pokhara_lake").first()
        self.assertEqual(row.verification_status, DestinationImage.ImageStatus.PENDING)
        self.assertFalse(row.is_verified)

    def test_proposal_carries_no_invented_scores(self):
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   return_value=commons_response([self.ok_row])):
            self._run(kind="destination", limit=5, apply=True)
        row = DestinationImage.objects.exclude(
            external_url__contains="Pokhara_lake").first()
        for field_name in ("quality_score", "realism_score", "authenticity_score",
                           "destination_match_score", "overall_score"):
            self.assertIsNone(
                getattr(row, field_name),
                f"{field_name} must stay NULL until a human reviews",
            )

    def test_city_photo_is_refused_for_a_destination(self):
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   return_value=commons_response([self.pokhara_row])):
            output = self._run(kind="destination", limit=5, apply=True)
        self.assertIn("unresolved", output)
        self.assertEqual(DestinationImage.objects.count(), 1)
        self.assertEqual(
            DestinationImage.objects.get().external_url,
            "https://upload.wikimedia.org/commons/9/9a/Pokhara_lake.jpg",
        )

    def test_unreusable_licence_is_refused(self):
        row = dict(self.ok_row, licence="CC BY-NC-SA 4.0")
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   return_value=commons_response([row])):
            self._run(kind="destination", limit=5, apply=True)
        self.assertEqual(DestinationImage.objects.count(), 1)

    def test_hotel_never_receives_a_destination_photo(self):
        """The rule the user was most explicit about."""
        hotel = Hotel.objects.create(
            destination=self.ghandruk, name="Barahi Jungle Lodge", phone="",
            external_image_url="https://upload.wikimedia.org/commons/3/3d/Chitwan_safari.jpg",
            is_active=True,
        )
        # Same photo is on the destination, so it is flagged as reused...
        DestinationImage.objects.create(
            destination=self.ghandruk,
            external_url="https://upload.wikimedia.org/commons/3/3d/Chitwan_safari.jpg",
            source=DestinationImage.Source.WIKIMEDIA,
        )
        # ...and the only Commons hit is a Pokhara cityscape, not this hotel.
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   return_value=commons_response([self.pokhara_row])):
            self._run(kind="hotel", limit=5, apply=True)
        hotel.refresh_from_db()
        self.assertEqual(
            hotel.external_image_url,
            "https://upload.wikimedia.org/commons/3/3d/Chitwan_safari.jpg",
            "a wrong-but-existing image must be left in place, not overwritten by a city photo",
        )

    def test_hotel_does_get_its_own_photo_when_one_exists(self):
        hotel = Hotel.objects.create(
            destination=self.ghandruk, name="Barahi Jungle Lodge", phone="",
            external_image_url="https://upload.wikimedia.org/commons/3/3d/Chitwan_safari.jpg",
            is_active=True,
        )
        DestinationImage.objects.create(
            destination=self.ghandruk,
            external_url="https://upload.wikimedia.org/commons/3/3d/Chitwan_safari.jpg",
            source=DestinationImage.Source.WIKIMEDIA,
        )
        hotel_row = {
            "title": "File:Barahi Jungle Lodge.jpg",
            "image_url": "https://upload.wikimedia.org/commons/4/4e/Barahi.jpg",
            "page_url": "https://commons.wikimedia.org/wiki/File:Barahi_Jungle_Lodge.jpg",
            "licence": "CC BY-SA 4.0",
        }
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   return_value=commons_response([hotel_row])):
            self._run(kind="hotel", limit=5, apply=True)
        hotel.refresh_from_db()
        self.assertIn("Barahi", hotel.external_image_url)
        self.assertIn("commons.wikimedia.org", hotel.source_url)

    def test_no_match_leaves_the_place_untouched(self):
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   return_value=commons_response([])):
            output = self._run(kind="destination", limit=5, apply=True)
        self.assertIn("unresolved", output)
        self.assertEqual(DestinationImage.objects.count(), 1)

    def test_provider_failure_does_not_crash_or_write(self):
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   side_effect=requests.Timeout()):
            output = self._run(kind="destination", limit=5, apply=True)
        self.assertIn("Commons unavailable", output)
        self.assertEqual(DestinationImage.objects.count(), 1)

    def test_identifying_user_agent_is_sent(self):
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   return_value=commons_response([self.ok_row])) as mocked:
            self._run(kind="destination", limit=5)
        agent = mocked.call_args.kwargs["headers"].get("User-Agent", "")
        self.assertTrue(agent)
        self.assertNotIn("python-requests", agent.lower())
        self.assertIn("NepalYatra", agent)

    def test_summary_reports_exact_counts_per_kind(self):
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   return_value=commons_response([self.ok_row])):
            output = self._run(kind="destination", limit=5, apply=True)
        self.assertIn("SUMMARY", output)
        self.assertIn("destination", output)
        self.assertIn("proposals:", output)


class HotelCoverImageTests(TestCase):
    """A regression: hotel.cover_image is an ImageFieldFile, not a string."""

    def _run(self, *args, **kwargs):
        out = StringIO()
        call_command("repair_real_place_images", *args, stdout=out, stderr=out, **kwargs)
        return out.getvalue()

    def setUp(self):
        cache.clear()
        category = Category.objects.create(name="Cover Category")
        self.destination = Destination.objects.create(
            name="Chitwan", slug="chitwan", category=category, district="Chitwan",
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
        )
        self.hotel = Hotel.objects.create(
            destination=self.destination, name="Barahi Jungle Lodge", phone="",
            cover_image="hotels/chitwan/safari.jpg", is_active=True,
        )
        DestinationImage.objects.create(
            destination=self.destination,
            external_url="https://upload.wikimedia.org/commons/3/3d/Chitwan_safari.jpg",
            source=DestinationImage.Source.WIKIMEDIA,
        )

    def test_hotel_path_handles_imagefieldfile(self):
        with patch("tourist.management.commands.repair_real_place_images.requests.get",
                   return_value=commons_response([])):
            output = self._run(kind="hotel", limit=5, apply=True)
        self.assertNotIn("Traceback", output)
        self.assertIn("hotel", output)
    def test_audit_handles_imagefieldfile(self):
        out = StringIO()
        call_command("audit_cross_place_images", stdout=out, stderr=out)
        self.assertIn("destination_photo_on_hotel", out.getvalue())


class OfflineTriageTests(TestCase):
    """The triage steps use evidence already on the row and contact nobody."""

    def setUp(self):
        cache.clear()
        category = Category.objects.create(name="Triage Category")
        self.phewa = Destination.objects.create(
            name="Phewa Lake", slug="phewa-lake", category=category, district="Kaski",
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
        )
        self.ghandruk = Destination.objects.create(
            name="Ghandruk", slug="ghandruk", category=category, district="Kaski",
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
        )
        self.gorkha = Destination.objects.create(
            name="Gorkha Durbar", slug="gorkha-durbar", category=category, district="Gorkha",
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
        )
        self.shared_url = "https://upload.wikimedia.org/commons/1/1a/Shared.jpg"

    def _run(self, *args, **kwargs):
        out = StringIO()
        call_command("repair_real_place_images", *args, stdout=out, stderr=out, **kwargs)
        return out.getvalue()

    def test_caption_naming_one_holder_keeps_it_and_flags_the_rest(self):
        """The caption already says which place this is; trust that."""
        keeper = DestinationImage.objects.create(
            destination=self.phewa, external_url=self.shared_url,
            caption="Phewa Lake at dawn", source=DestinationImage.Source.WIKIMEDIA,
        )
        wrong_a = DestinationImage.objects.create(
            destination=self.ghandruk, external_url=self.shared_url,
            caption="", source=DestinationImage.Source.WIKIMEDIA,
        )
        wrong_b = DestinationImage.objects.create(
            destination=self.gorkha, external_url=self.shared_url,
            caption="", source=DestinationImage.Source.WIKIMEDIA,
        )
        self._run(triage_only=True, reassign_by_caption=True, apply=True)
        keeper.refresh_from_db()
        wrong_a.refresh_from_db()
        wrong_b.refresh_from_db()
        self.assertNotEqual(keeper.verification_status, DestinationImage.ImageStatus.REJECTED)
        for wrong in (wrong_a, wrong_b):
            self.assertEqual(wrong.verification_status, DestinationImage.ImageStatus.REJECTED)
            self.assertFalse(wrong.is_verified)
            self.assertIn("Phewa Lake", wrong.review_note)

    def test_ambiguous_caption_flags_nothing(self):
        """A caption naming two holders proves nothing; do not act on it."""
        a = DestinationImage.objects.create(
            destination=self.phewa, external_url=self.shared_url,
            caption="Phewa Lake", source=DestinationImage.Source.WIKIMEDIA,
        )
        b = DestinationImage.objects.create(
            destination=self.ghandruk, external_url=self.shared_url,
            caption="Ghandruk village", source=DestinationImage.Source.WIKIMEDIA,
        )
        self._run(triage_only=True, reassign_by_caption=True, apply=True)
        a.refresh_from_db()
        b.refresh_from_db()
        self.assertNotEqual(a.verification_status, DestinationImage.ImageStatus.REJECTED)
        self.assertNotEqual(b.verification_status, DestinationImage.ImageStatus.REJECTED)

    def test_no_caption_flags_nothing(self):
        a = DestinationImage.objects.create(
            destination=self.phewa, external_url=self.shared_url,
            source=DestinationImage.Source.WIKIMEDIA,
        )
        b = DestinationImage.objects.create(
            destination=self.ghandruk, external_url=self.shared_url,
            source=DestinationImage.Source.WIKIMEDIA,
        )
        output = self._run(triage_only=True, reassign_by_caption=True, apply=True)
        self.assertIn("0 rows flagged for review", output)
        a.refresh_from_db()
        b.refresh_from_db()
        self.assertNotEqual(a.verification_status, DestinationImage.ImageStatus.REJECTED)
        self.assertNotEqual(b.verification_status, DestinationImage.ImageStatus.REJECTED)

    def test_reassignment_is_not_quadratic(self):
        """One image on many places, each caption naming its own place, must not
        produce a flag per row per holder. This is the bug that reported 1,045,254
        changes against a 26,203-row gallery."""
        rows = []
        for destination in (self.phewa, self.ghandruk, self.gorkha):
            rows.append(DestinationImage.objects.create(
                destination=destination, external_url=self.shared_url,
                caption=f"Photo of {destination.name}",
                source=DestinationImage.Source.WIKIMEDIA,
            ))
        output = self._run(triage_only=True, reassign_by_caption=True)
        self.assertIn("more than one holder's caption", output)
        for row in rows:
            row.refresh_from_db()
            self.assertNotEqual(
                row.verification_status, DestinationImage.ImageStatus.REJECTED,
                "an image whose every caption claims a different place is ambiguous",
            )

    def test_quarantine_flags_every_holder_of_a_widely_shared_image(self):
        rows = [
            DestinationImage.objects.create(
                destination=d, external_url=self.shared_url,
                source=DestinationImage.Source.WIKIMEDIA,
                verification_status=DestinationImage.ImageStatus.APPROVED, is_verified=True,
            )
            for d in (self.phewa, self.ghandruk, self.gorkha)
        ]
        self._run(triage_only=True, quarantine_shared=3, apply=True)
        for row in rows:
            row.refresh_from_db()
            self.assertEqual(row.verification_status, DestinationImage.ImageStatus.PENDING)
            self.assertFalse(row.is_verified)
            self.assertIn("shared by 3 different places", row.review_note)

    def test_quarantine_below_threshold_touches_nothing(self):
        row = DestinationImage.objects.create(
            destination=self.phewa, external_url=self.shared_url,
            source=DestinationImage.Source.WIKIMEDIA,
        )
        self._run(triage_only=True, quarantine_shared=5, apply=True)
        row.refresh_from_db()
        self.assertNotEqual(row.verification_status, DestinationImage.ImageStatus.PENDING)

    def test_duplicate_covers_are_reduced_to_one(self):
        for index in range(3):
            DestinationImage.objects.create(
                destination=self.phewa,
                external_url=f"https://upload.wikimedia.org/commons/2/2{index}/C{index}.jpg",
                is_cover=True, ordering=index, source=DestinationImage.Source.WIKIMEDIA,
            )
        self._run(triage_only=True, fix_multiple_covers=True, apply=True)
        covers = DestinationImage.objects.filter(destination=self.phewa, is_cover=True)
        self.assertEqual(covers.count(), 1)

    def test_triage_dry_run_writes_nothing(self):
        rows = [
            DestinationImage.objects.create(
                destination=d, external_url=self.shared_url,
                source=DestinationImage.Source.WIKIMEDIA,
                verification_status=DestinationImage.ImageStatus.APPROVED, is_verified=True,
            )
            for d in (self.phewa, self.ghandruk, self.gorkha)
        ]
        before = list(DestinationImage.objects.values_list("id", "verification_status", "is_verified"))
        output = self._run(triage_only=True, quarantine_shared=3)
        after = list(DestinationImage.objects.values_list("id", "verification_status", "is_verified"))
        self.assertEqual(before, after)
        self.assertIn("would flag", output)

    def test_triage_never_invents_a_score(self):
        row = DestinationImage.objects.create(
            destination=self.phewa, external_url=self.shared_url,
            source=DestinationImage.Source.WIKIMEDIA,
        )
        self._run(triage_only=True, quarantine_shared=2, apply=True)
        row.refresh_from_db()
        self.assertIsNone(row.quality_score)
        self.assertIsNone(row.authenticity_score)
