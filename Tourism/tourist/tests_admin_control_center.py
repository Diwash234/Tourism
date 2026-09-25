"""Focused regression tests for the authenticated Admin Control Center path.

These tests exercise the boundaries that matter most: capability checks,
object scope, public media visibility, publication snapshots, and honest
emergency data. They intentionally use the existing domain models and API
contracts rather than creating a parallel test model.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import (
    Category,
    ContentSection,
    Destination,
    DestinationImage,
    Hotel,
    ManagedPage,
    StaffCapabilityProfile,
)

User = get_user_model()


class AdminControlCenterSecurityTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="control-center-admin@test.local", password="Sup!Pass123"
        )
        self.staff = User.objects.create_user(
            email="control-center-staff@test.local",
            password="Staff!Pass123",
            role="staff",
            is_staff=True,
        )
        StaffCapabilityProfile.objects.create(
            user=self.staff,
            capabilities={"destinations": ["view", "change"], "images": ["view"]},
            managed_districts=["Kaski"],
        )
        self.category = Category.objects.create(name="Control Center Test")
        self.kaski = Destination.objects.create(
            name="Kaski Control Place",
            slug="kaski-control-place",
            category=self.category,
            district="Kaski",
            description="Recorded description",
            latitude=28.2,
            longitude=83.9,
            status="approved",
            is_active=True,
        )
        self.kathmandu = Destination.objects.create(
            name="Kathmandu Control Place",
            slug="kathmandu-control-place",
            category=self.category,
            district="Kathmandu",
            description="Recorded description",
            latitude=27.7,
            longitude=85.3,
            status="approved",
            is_active=True,
        )

    def test_admin_destination_routes_require_capability_and_district_scope(self):
        self.client.force_authenticate(self.staff)
        listing = self.client.get("/api/v1/admin/destinations")
        self.assertEqual(listing.status_code, 200)
        result_ids = {row["id"] for row in listing.json()["results"]}
        self.assertIn(self.kaski.id, result_ids)
        self.assertNotIn(self.kathmandu.id, result_ids)
        self.assertEqual(
            self.client.get(f"/api/v1/admin/destinations/{self.kathmandu.id}").status_code,
            403,
        )

    def test_generic_explorer_cannot_bypass_domain_permissions(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(
            "/api/v1/admin/data-explorer/",
            {"resource": "categories", "id": self.category.id, "fields": {"name": "hijacked"}},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Control Center Test")

    def test_public_image_read_is_side_effect_free_and_hides_pending_media(self):
        pending = DestinationImage.objects.create(
            destination=self.kaski,
            external_url="https://cdn.example/pending-control.jpg",
            verification_status="pending",
            is_verified=False,
        )
        with patch("tourist.views_images.ImageAcquisitionPipeline.acquire_images_for_destination") as acquire:
            response = self.client.get("/api/v1/destinations/kaski-control-place/images")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.json()["images"]], [])
        acquire.assert_not_called()
        self.assertTrue(DestinationImage.objects.filter(pk=pending.pk).exists())

    def test_media_replacement_refreshes_published_cms_snapshot(self):
        page = ManagedPage.objects.create(
            route="/control-center-media", key="control-center-media", title="Media", status="published"
        )
        section = ContentSection.objects.create(
            page=page,
            key="hero",
            title="Hero",
            image_url="https://cdn.example/old-control.jpg",
            section_type="image",
            status="published",
        )
        from .cms_publishing import sync_published_snapshot
        sync_published_snapshot(section)
        image = DestinationImage.objects.create(
            destination=self.kaski,
            external_url="https://cdn.example/old-control.jpg",
            verification_status="approved",
            is_verified=True,
        )
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            "/api/v1/admin/media-library/",
            {"id": image.id, "external_url": "https://cdn.example/new-control.jpg"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        section.refresh_from_db()
        self.assertEqual(section.published_snapshot["image_url"], "https://cdn.example/new-control.jpg")
        public = self.client.get("/api/v1/config/public/").json()
        rendered = next(p for p in public["pages"] if p["key"] == page.key)
        self.assertEqual(rendered["sections"][0]["image_url"], "https://cdn.example/new-control.jpg")

    def test_emergency_creation_never_invents_a_phone_number(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/admin/emergency-directory/",
            {
                "kind": "hospital",
                "name": "No Placeholder Hospital",
                "address": "Kaski",
                "district": "Kaski",
                "latitude": 28.2,
                "longitude": 83.9,
                "destination_id": self.kaski.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("phone", response.json()["detail"].lower())

    def test_page_metadata_draft_isolated_until_publish(self):
        page = ManagedPage.objects.create(
            route="/control-center-page", key="control-center-page", title="Old title", status="published"
        )
        from .cms_publishing import sync_published_page
        sync_published_page(page)
        self.client.force_authenticate(self.admin)
        saved = self.client.patch(
            "/api/v1/admin/cms/",
            {"resource": "pages", "id": page.id, "title": "New draft title"},
            format="json",
        )
        self.assertEqual(saved.status_code, 200)
        public = self.client.get("/api/v1/config/public/")
        page_rows = [row for row in public.json()["pages"] if row["id"] == page.id]
        self.assertEqual(page_rows[0]["title"], "Old title")
        self.client.patch(
            "/api/v1/admin/cms/",
            {"resource": "pages", "id": page.id, "action": "publish"},
            format="json",
        )
        public = self.client.get("/api/v1/config/public/")
        self.assertIn("New draft title", [row["title"] for row in public.json()["pages"] if row["id"] == page.id])

    def test_ai_image_public_surface_hides_pending_assets(self):
        DestinationImage.objects.create(
            destination=self.kaski,
            external_url="https://cdn.example/ai-pending.jpg",
            verification_status="pending",
            is_verified=False,
        )
        response = self.client.get(f"/api/v1/ai-images/destinations/{self.kaski.id}/images")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["images"], [])

    def test_public_destination_cover_ignores_unverified_media(self):
        pending = DestinationImage.objects.create(
            destination=self.kaski,
            external_url="https://cdn.example/unverified-cover.jpg",
            verification_status="pending",
            is_verified=False,
        )
        self.kaski.cover_image = pending.external_url
        self.kaski.save(update_fields=["cover_image", "updated_at"])
        response = self.client.get("/api/v1/destinations/kaski-control-place/")
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()["cover_image_url"], pending.external_url)

    def test_scoped_travel_plan_listing_does_not_filter_destination_field(self):
        from .models import TravelPlan
        from .models import StaffCapabilityProfile as Profile
        profile = Profile.objects.get(user=self.staff)
        profile.capabilities = {**profile.capabilities, "travel_plans": ["view"]}
        profile.save(update_fields=["capabilities", "updated_at"])
        plan = TravelPlan.objects.create(title="Scoped plan", user=self.staff)
        self.client.force_authenticate(self.staff)
        response = self.client.get("/api/v1/admin/travel-services/?resource=travel_plans")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["id"], plan.id)

    def test_public_destination_detail_hides_archived_hotels(self):
        Hotel.objects.create(
            destination=self.kaski,
            name="Archived Control Hotel",
            is_active=False,
        )
        response = self.client.get("/api/v1/destinations/kaski-control-place/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Archived Control Hotel", [row["name"] for row in response.json()["hotels"]])
