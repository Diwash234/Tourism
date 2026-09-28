"""Generated postcards must not be presented as photographs of a place.

5,996 rows were stored as ``approved`` and ``is_verified=True``, six of them as
the destination's cover, each declaring ``copyright_status='verified_reusable'``
-- a licence judgement about a photograph by somebody who took one, applied to
an image nobody took. None of the 5,996 carries an attribution, and 5,907
destinations had one as their only image.

These tests pin the quarantine: generated rows are marked as not being
photographs, and real photographs are never touched however they were sourced.
"""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from tourist.models import Category, Destination, DestinationImage, User

POSTCARD_URL = "/api/v1/postcard/hotel/Rockland%20Hotel/Kaski/id-1"
REAL_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Real.jpg"


class GeneratedPostcardQuarantineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("postcard-qa@test.local", "PostcardQA!123")
        category = Category.objects.create(name="Postcard QA")
        self.destination = Destination.objects.create(
            name="Rockland Hotel", slug="rockland-hotel", category=category,
            description="A lodge in Kaski.", latitude=28.2096, longitude=83.9856,
            created_by=self.user, status="approved", is_active=True)

    def _postcard(self, **overrides):
        fields = {
            "destination": self.destination,
            "external_url": POSTCARD_URL,
            "caption": "A generated card",
            "copyright_status": "verified_reusable",
            "source_platform": "postcard",
            "verification_status": DestinationImage.ImageStatus.APPROVED,
            "is_verified": True,
        }
        fields.update(overrides)
        return DestinationImage.objects.create(**fields)

    def _real(self, **overrides):
        fields = {
            "destination": self.destination,
            "external_url": REAL_URL,
            "caption": "A real photograph",
            "copyright_status": "verified_reusable",
            "source_platform": "wikimedia",
            "verification_status": DestinationImage.ImageStatus.APPROVED,
            "is_verified": True,
        }
        fields.update(overrides)
        return DestinationImage.objects.create(**fields)

    def _quarantine(self, *args):
        out = StringIO()
        call_command("quarantine_generated_postcards", *args, stdout=out)
        return out.getvalue()

    def test_a_postcard_stops_being_a_verified_photograph(self):
        card = self._postcard()
        self._quarantine("--apply")
        card.refresh_from_db()
        self.assertFalse(card.is_verified)
        self.assertNotEqual(card.verification_status,
                            DestinationImage.ImageStatus.APPROVED)

    def test_a_postcard_stops_claiming_reusable_copyright(self):
        card = self._postcard()
        self._quarantine("--apply")
        card.refresh_from_db()
        self.assertNotEqual(card.copyright_status, "verified_reusable",
                            "no author means no reusable-copyright claim to make")

    def test_a_postcard_stops_being_a_cover(self):
        card = self._postcard(is_cover=True)
        self._quarantine("--apply")
        card.refresh_from_db()
        self.assertFalse(card.is_cover)

    def test_a_real_photograph_is_never_touched(self):
        # Whatever its licence field says, a real photograph is not a postcard
        # and the quarantine must not reach it.
        photo = self._real(is_cover=True)
        self._quarantine("--apply")
        photo.refresh_from_db()
        self.assertTrue(photo.is_verified)
        self.assertTrue(photo.is_cover)
        self.assertEqual(photo.verification_status,
                         DestinationImage.ImageStatus.APPROVED)
        self.assertEqual(photo.copyright_status, "verified_reusable")

    def test_a_dry_run_changes_nothing(self):
        card = self._postcard()
        output = self._quarantine()
        card.refresh_from_db()
        self.assertTrue(card.is_verified)
        self.assertIn("DRY RUN", output)

    def test_the_report_counts_the_claims_being_made(self):
        self._postcard(is_cover=True)
        self._real()
        output = self._quarantine()
        self.assertIn("used as a destination cover", output)
        self.assertIn("claiming reusable copyright", output)
        self.assertIn("only image", output)

    def test_purge_removes_the_rows_instead(self):
        self._postcard()
        self._real()
        self._quarantine("--apply", "--purge")
        self.assertFalse(DestinationImage.objects.filter(
            source_platform__iexact="postcard").exists())
        self.assertTrue(DestinationImage.objects.filter(
            external_url=REAL_URL).exists())

    def test_a_database_with_no_postcards_is_a_clean_noop(self):
        self._real()
        output = self._quarantine("--apply")
        self.assertIn("no generated postcards", output)

    def test_a_postcard_is_kept_not_deleted(self):
        card = self._postcard()
        self._quarantine("--apply")
        self.assertTrue(DestinationImage.objects.filter(pk=card.pk).exists(),
                        "the row is kept so the decision stays visible in the admin")
