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

    def test_admin_can_import_image_to_destination(self):
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

        # Check DB state
        self.destination.refresh_from_db()
        self.assertTrue(self.destination.gallery.filter(caption__icontains="Phewa Lake").exists())
        self.assertTrue(bool(self.destination.cover_image))

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
