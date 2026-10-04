from rest_framework import status
from rest_framework.test import APITestCase
from tourist.models import User, Destination, DestinationImage, Category
from tourist.services.image_search.search import ImageHit, calculate_hit_scores


class MultiSourceImageSearchTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="media_admin@example.com",
            password="TestPassword123!",
        )
        self.regular_user = User.objects.create_user(
            email="regular_user@example.com",
            password="TestPassword123!",
        )
        self.cat = Category.objects.create(name="Lake")
        self.destination = Destination.objects.create(
            name="Phewa Lake",
            city="Pokhara",
            district="Kaski",
            province="Gandaki",
            category=self.cat,
        )

    def test_anonymous_cannot_search_multi_source(self):
        res = self.client.post("/api/v1/admin/images/multi-search/", {
            "query": "Phewa Lake",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_search_multi_source(self):
        self.client.force_authenticate(user=self.regular_user)
        res = self.client.post("/api/v1/admin/images/multi-search/", {
            "query": "Phewa Lake",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_search_multi_source(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post("/api/v1/admin/images/multi-search/", {
            "destination_id": self.destination.id,
            "query": "Phewa Lake",
            "district": "Kaski",
            "province": "Gandaki",
            "sources": ["wikimedia", "unsplash"],
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("results", res.data)
        self.assertIn("total_found", res.data)
        self.assertIn("destination", res.data)
        # Results should have the required fields
        if res.data["results"]:
            first = res.data["results"][0]
            self.assertIn("url", first)
            self.assertIn("source", first)
            self.assertIn("confidence_score", first)
            self.assertIn("location_match", first)
            self.assertIn("keyword_match", first)

    def test_search_requires_query_or_destination(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post("/api/v1/admin/images/multi-search/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_imports_candidate_without_publishing_or_replacing_current_cover(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post("/api/v1/admin/images/import-media/", {
            "destination_id": self.destination.id,
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Phewa_Lake_Pokhara.jpg/1280px-Phewa_Lake_Pokhara.jpg",
            "source_platform": "wikimedia",
            "source_url": "https://commons.wikimedia.org/wiki/File:Phewa_Lake_Pokhara.jpg",
            "photographer": "Wikimedia Contributor",
            "license_type": "CC-BY-SA-4.0",
            "caption": "Panoramic view of Phewa Lake with Annapurna reflection",
            "alt_text": "Phewa Lake Pokhara",
            "confidence_score": 92,
            "is_cover": True,
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["success"])
        self.assertTrue(res.data["needs_review"])
        self.assertEqual(res.data["verification_status"], DestinationImage.ImageStatus.PENDING)

        # Search confidence is not verification. The candidate stays private
        # until a reviewer checks both its subject match and its license.
        self.destination.refresh_from_db()
        image = self.destination.gallery.get(caption__icontains="Phewa Lake")
        self.assertFalse(image.is_verified)
        self.assertEqual(image.verification_status, DestinationImage.ImageStatus.PENDING)
        self.assertIsNone(image.destination_match_score)
        self.assertEqual(image.copyright_status, "pending_review")
        self.assertEqual(image.source, DestinationImage.Source.WIKIMEDIA)
        self.assertEqual(image.source_url, "https://commons.wikimedia.org/wiki/File:Phewa_Lake_Pokhara.jpg")
        self.assertTrue(image.is_cover)  # cover request is held until approval
        self.assertFalse(bool(self.destination.cover_image))
        queue = self.client.get("/api/v1/admin/pending-images/")
        self.assertEqual(queue.status_code, status.HTTP_200_OK)
        queued_image = next(row for row in queue.data if row["id"] == image.id)
        self.assertEqual(queued_image["source_url"], image.source_url)
        self.assertEqual(queued_image["license_type"], image.license_type)
        self.assertEqual(queued_image["copyright_status"], "pending_review")

    def test_reimport_preserves_existing_approval_and_cover(self):
        image_url = "https://upload.wikimedia.org/wikipedia/commons/phewa.jpg"
        existing = DestinationImage.objects.create(
            destination=self.destination,
            external_url=image_url,
            source=DestinationImage.Source.WIKIMEDIA,
            source_url="https://commons.wikimedia.org/wiki/File:Phewa.jpg",
            verification_status=DestinationImage.ImageStatus.APPROVED,
            is_verified=True,
            is_cover=True,
        )
        self.destination.cover_image = image_url
        self.destination.save(update_fields=["cover_image"])
        self.client.force_authenticate(user=self.admin)

        response = self.client.post("/api/v1/admin/images/import-media/", {
            "destination_id": self.destination.id,
            "image_url": image_url,
            "source_platform": "wikimedia",
            "confidence_score": 99,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["needs_review"])
        self.assertEqual(self.destination.gallery.count(), 1)
        existing.refresh_from_db()
        self.destination.refresh_from_db()
        self.assertTrue(existing.is_verified)
        self.assertEqual(existing.verification_status, DestinationImage.ImageStatus.APPROVED)
        self.assertEqual(self.destination.cover_image, image_url)

    def test_import_requires_image_url_and_destination(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post("/api/v1/admin/images/import-media/", {
            "destination_id": self.destination.id,
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confidence_scoring_logic(self):
        hit = ImageHit(
            url="https://example.com/phewa.jpg",
            source="wikimedia",
            title="Phewa Lake Pokhara Annapurna reflection",
            thumbnail="https://example.com/phewa_thumb.jpg",
            source_page_url="https://commons.wikimedia.org/wiki/File:Phewa.jpg",
            author="Photographer",
            license="CC-BY-SA-4.0",
        )
        calculate_hit_scores(hit, destination_name="Phewa Lake", district="Kaski", province="Gandaki", keywords="lake")
        self.assertGreaterEqual(hit.confidence_score, 40)
        self.assertGreater(hit.location_match, 0)
        self.assertGreater(hit.keyword_match, 0)
