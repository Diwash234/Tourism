from unittest.mock import patch

from django.test import override_settings
import requests
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User, Category, Destination, Hotel, Review, EmailVerificationToken


class AuthTests(APITestCase):
    def test_register_creates_unverified_user_and_sends_token(self):
        url = reverse("auth-register")
        payload = {
            "email": "tourist@example.com",
            "first_name": "Test",
            "last_name": "Tourist",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="tourist@example.com")
        self.assertFalse(user.is_verified)
        self.assertTrue(EmailVerificationToken.objects.filter(user=user).exists())

    def test_register_password_mismatch_fails(self):
        url = reverse("auth-register")
        payload = {
            "email": "mismatch@example.com",
            "password": "StrongPass123!",
            "password_confirm": "Different123!",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_jwt_pair(self):
        User.objects.create_user(email="login@example.com", password="StrongPass123!", is_verified=True)
        url = reverse("auth-login")
        response = self.client.post(url, {"email": "login@example.com", "password": "StrongPass123!"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_verify_email_with_valid_token(self):
        user = User.objects.create_user(email="verify@example.com", password="StrongPass123!")
        from django.utils import timezone
        from datetime import timedelta

        token = EmailVerificationToken.objects.create(
            user=user, expires_at=timezone.now() + timedelta(hours=1)
        )
        url = reverse("auth-verify-email")
        response = self.client.post(url, {"token": str(token.token)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    def test_logout_blacklists_refresh_token(self):
        user = User.objects.create_user(email="logout@example.com", password="StrongPass123!", is_verified=True)
        login_resp = self.client.post(reverse("auth-login"), {"email": "logout@example.com", "password": "StrongPass123!"})
        access = login_resp.data["access"]
        refresh = login_resp.data["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(reverse("auth-logout"), {"refresh": refresh})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)


class DestinationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin@example.com", password="AdminPass123!")
        self.category = Category.objects.create(name="Lakes")
        self.destination = Destination.objects.create(
            name="Phewa Lake",
            category=self.category,
            description="A beautiful lake in Pokhara.",
            latitude=28.2096,
            longitude=83.9560,
            city="Pokhara",
            country="Nepal",
            created_by=self.admin,
        )

    def test_list_destinations_public(self):
        response = self.client.get(reverse("destination-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_tourist_can_submit_pending_place(self):
        """Any logged-in tourist can submit a place; it starts pending & inactive until approved."""
        tourist = User.objects.create_user(email="tourist2@example.com", password="StrongPass123!", is_verified=True)
        self.client.force_authenticate(user=tourist)
        response = self.client.post(reverse("destination-list"), {
            "name": "Sarangkot", "category": self.category.id,
            "description": "Sunrise viewpoint", "latitude": 28.2380, "longitude": 83.9536,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Destination.objects.get(name="Sarangkot")
        self.assertEqual(created.status, Destination.SubmissionStatus.PENDING)
        self.assertFalse(created.is_active)
        self.assertTrue(created.is_user_submitted)

        # Pending submissions shouldn't show up in the public list yet.
        self.client.force_authenticate(user=None)
        list_response = self.client.get(reverse("destination-list"))
        names = [d["name"] for d in list_response.data["results"]]
        self.assertNotIn("Sarangkot", names)

    def test_admin_can_approve_pending_submission(self):
        tourist = User.objects.create_user(email="tourist3@example.com", password="StrongPass123!", is_verified=True)
        self.client.force_authenticate(user=tourist)
        create_response = self.client.post(reverse("destination-list"), {
            "name": "Begnas Lake", "category": self.category.id,
            "description": "Quiet lakeside spot", "latitude": 28.1600, "longitude": 84.0400,
        })
        slug = create_response.data["slug"] if "slug" in create_response.data else Destination.objects.get(name="Begnas Lake").slug

        self.client.force_authenticate(user=self.admin)
        approve_response = self.client.post(
            reverse("destination-approve", kwargs={"slug": slug}), {"status": "approved"}
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        destination = Destination.objects.get(name="Begnas Lake")
        self.assertEqual(destination.status, Destination.SubmissionStatus.APPROVED)
        self.assertTrue(destination.is_active)

    def test_create_destination_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("destination-list"), {
            "name": "Sarangkot", "category": self.category.id,
            "description": "Sunrise viewpoint", "latitude": 28.2380, "longitude": 83.9536,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_nearby_destinations(self):
        url = reverse("destination-nearby")
        response = self.client.get(url, {"latitude": 28.2100, "longitude": 83.9600, "radius_km": 20})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)


class ReviewRatingTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin3@example.com", password="AdminPass123!")
        self.tourist = User.objects.create_user(email="reviewer@example.com", password="StrongPass123!", is_verified=True)
        self.category = Category.objects.create(name="Museums")
        self.destination = Destination.objects.create(
            name="International Mountain Museum", category=self.category,
            description="Museum about mountains.", latitude=28.1900, longitude=83.9700,
            created_by=self.admin,
        )
        self.client.force_authenticate(user=self.tourist)

    def test_create_review(self):
        response = self.client.post(reverse("review-list"), {
            "destination": self.destination.id, "comment": "Loved it!",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_rating_updates_destination_average(self):
        response = self.client.post(reverse("rating-list"), {
            "destination": self.destination.id, "value": 4,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.destination.refresh_from_db()
        self.assertEqual(float(self.destination.average_rating), 4.0)
        self.assertEqual(self.destination.ratings_count, 1)

    def test_duplicate_rating_rejected(self):
        self.client.post(reverse("rating-list"), {"destination": self.destination.id, "value": 4})
        response = self.client.post(reverse("rating-list"), {"destination": self.destination.id, "value": 5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FavoriteTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin4@example.com", password="AdminPass123!")
        self.tourist = User.objects.create_user(email="fan@example.com", password="StrongPass123!", is_verified=True)
        self.category = Category.objects.create(name="Adventure")
        self.destination = Destination.objects.create(
            name="Paragliding Point", category=self.category,
            description="Adventure sport spot.", latitude=28.2400, longitude=83.9500,
            created_by=self.admin,
        )
        self.client.force_authenticate(user=self.tourist)

    def test_add_and_list_favorite(self):
        response = self.client.post(reverse("favorite-list"), {"destination": self.destination.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        list_response = self.client.get(reverse("favorite-list"))
        self.assertEqual(list_response.data["count"], 1)


class EmergencyContactTests(APITestCase):
    def setUp(self):
        from .models import EmergencyContact
        self.police = EmergencyContact.objects.create(
            contact_type="police", name="Central Police", phone_number="+9779800000009",
            latitude=28.2096, longitude=83.9856, city="Pokhara",
        )

    def test_nearest_emergency_contact(self):
        url = reverse("emergency-contact-nearest")
        response = self.client.get(url, {"latitude": 28.2100, "longitude": 83.9800, "radius_km": 15})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Central Police")


class GeoIPTests(APITestCase):
    def test_detect_location_endpoint_available(self):
        response = self.client.get(reverse("auth-detect-location"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ViewCountTests(APITestCase):
    def test_retrieve_increments_views_count(self):
        admin = User.objects.create_superuser(email="admin5@example.com", password="AdminPass123!")
        category = Category.objects.create(name="Viewpoints")
        destination = Destination.objects.create(
            name="World Peace Pagoda", category=category,
            description="Hilltop stupa with panoramic views.",
            latitude=28.2000, longitude=83.9400, created_by=admin,
        )
        self.assertEqual(destination.views_count, 0)
        self.client.get(reverse("destination-detail", kwargs={"slug": destination.slug}))
        self.client.get(reverse("destination-detail", kwargs={"slug": destination.slug}))
        destination.refresh_from_db()
        self.assertEqual(destination.views_count, 2)


class MLIntegrationTests(APITestCase):
    @patch("tourist.views_ml.requests.post", side_effect=requests.RequestException("down"))
    def test_recommendations_falls_back_when_ml_service_unreachable(self, _mock):
        admin = User.objects.create_superuser(email="admin6@example.com", password="AdminPass123!")
        category = Category.objects.create(name="Trekking")
        Destination.objects.create(
            name="Annapurna Base Camp Trail", category=category,
            description="Classic trekking route.", latitude=28.5300, longitude=83.8800,
            created_by=admin, average_rating=5,
        )
        response = self.client.post(reverse("ml-recommendations"), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["source"], "fallback_top_rated")
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_ml_webhook_rejects_bad_secret(self):
        response = self.client.post(reverse("ml-results-webhook"), {
            "destination_id": 1, "insight_type": "image_classification",
        }, HTTP_X_ML_WEBHOOK_SECRET="wrong-secret")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("tourist.utils.requests.post", side_effect=requests.RequestException("down"))
    def test_safety_prediction_returns_503_when_ml_service_down(self, _mock):
        response = self.client.post(reverse("ml-safety"), {"latitude": 28.21, "longitude": 83.96})
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_safety_prediction_requires_coords_or_destination(self):
        response = self.client.post(reverse("ml-safety"), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("tourist.utils.requests.post", side_effect=requests.RequestException("down"))
    def test_budget_prediction_returns_503_when_ml_service_down(self, _mock):
        response = self.client.post(reverse("ml-budget"), {"city": "Pokhara", "days": 3, "travelers": 2})
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch("tourist.utils.requests.post", side_effect=requests.RequestException("down"))
    def test_best_route_uses_bundled_graph_when_ml_service_down(self, _mock):
        response = self.client.post(reverse("ml-best-route"), {
            "start_latitude": 28.21, "start_longitude": 83.96,
            "end_latitude": 28.23, "end_longitude": 83.99,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["routing_engine"], "bundled_nepal_graphml")
        self.assertTrue(response.data["route"])

    def test_best_route_requires_end_point(self):
        response = self.client.post(reverse("ml-best-route"), {"start_latitude": 28.21, "start_longitude": 83.96})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PhotoAndDataSourceTests(APITestCase):
    def setUp(self):
        from unittest.mock import patch

        from .models import Category, Destination

        self.admin = User.objects.create_superuser(email="admin7@example.com", password="AdminPass123!")
        self.tourist = User.objects.create_user(email="localphotographer@example.com", password="StrongPass123!", is_verified=True)
        self.category = Category.objects.create(name="Waterfalls")
        self.destination = Destination.objects.create(
            name="Devi's Fall", category=self.category,
            description="A dramatic waterfall.", latitude=28.1900, longitude=83.9500,
            created_by=self.admin,
        )
        # Deterministic tests: stub every external image source so the
        # "no external keys" scenario is actually simulated instead of
        # depending on the live Wikimedia/Unsplash APIs (Wikimedia needs
        # no key, so a real network would return real photos and break the
        # empty-gallery expectation).
        self.ext_patcher = patch.multiple(
            "tourist.utils",
            fetch_wikimedia_photos=lambda *a, **k: [],
            fetch_unsplash_photo=lambda *a, **k: None,
        )
        self.ext_patcher.start()
        self.addCleanup(self.ext_patcher.stop)

    def test_photos_endpoint_returns_empty_gallery_with_no_external_keys(self):
        response = self.client.get(reverse("destination-photos", kwargs={"slug": self.destination.slug}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # No Unsplash/Wikimedia keys configured (or unreachable) in the test
        # env, so ensure_cover_photo() can't find anything to cache.
        self.assertEqual(response.data["photos"], [])

    def test_search_result_cover_image_falls_back_gracefully_without_keys(self):
        """
        With no UNSPLASH_ACCESS_KEY configured, cover_image_url should be
        None rather than erroring — this is the exact bug scenario: a
        destination with zero local photos and no working external image
        source must not crash the list endpoint.
        """
        response = self.client.get(reverse("destination-list"), {"search": self.destination.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = next(r for r in response.data["results"] if r["id"] == self.destination.id)
        self.assertIsNone(result["cover_image_url"])

    def test_search_result_shows_cached_cover_image_once_one_exists(self):
        """
        This is the actual bug fix: once ANY photo exists for a destination
        (local upload, admin upload, or a previously-cached external one),
        cover_image_url must reflect it in search/list results — not just
        on the dedicated /photos/ endpoint.
        """
        from .models import DestinationImage

        DestinationImage.objects.create(
            destination=self.destination, external_url="https://images.example.com/devis-fall.jpg",
            source=DestinationImage.Source.WIKIMEDIA, attribution="Photo: Someone (Wikimedia Commons)",
            is_cover=True,
        )
        response = self.client.get(reverse("destination-list"), {"search": self.destination.name})
        result = next(r for r in response.data["results"] if r["id"] == self.destination.id)
        self.assertEqual(result["cover_image_url"], "https://images.example.com/devis-fall.jpg")

    def test_community_can_upload_photo(self):
        from .models import DestinationImage

        self.client.force_authenticate(user=self.tourist)
        response = self.client.post(
            reverse("destination-photos", kwargs={"slug": self.destination.slug}),
            {"caption": "Sunset view"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        photo = DestinationImage.objects.get(destination=self.destination)
        self.assertEqual(photo.source, DestinationImage.Source.USER_UPLOAD)
        self.assertEqual(photo.uploaded_by, self.tourist)
        self.assertFalse(photo.is_promoted)

    def test_popular_community_photo_gets_auto_promoted(self):
        from .models import DestinationImage
        from .utils import register_photo_view

        photo = DestinationImage.objects.create(
            destination=self.destination, external_url="https://example.com/photo.jpg",
            source=DestinationImage.Source.USER_UPLOAD, uploaded_by=self.tourist,
        )
        # Simulate the photo being viewed past the promotion threshold.
        photo.view_count = 100
        photo.save(update_fields=["view_count"])
        register_photo_view(photo)
        photo.refresh_from_db()
        self.assertTrue(photo.is_promoted)
        self.assertTrue(photo.is_cover)

    def test_weather_returns_503_without_api_key(self):
        response = self.client.get(reverse("destination-weather", kwargs={"slug": self.destination.slug}))
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_osm_nearby_requires_coordinates(self):
        response = self.client.get(reverse("osm-nearby-places"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_osm_nearby_gracefully_handles_no_network(self):
        response = self.client.get(reverse("osm-nearby-places"), {"latitude": 28.21, "longitude": 83.96})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_hotels_list_and_booking_status(self):
        from .models import Hotel

        Hotel.objects.create(
            destination=self.destination, name="Fishtail Lodge", price_per_night=80,
            booking_status=Hotel.BookingStatus.AVAILABLE, latitude=28.19, longitude=83.95,
        )
        response = self.client.get(reverse("hotel-list"), {"destination": self.destination.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["booking_status"], "available")


class CompatibilityRouteTests(APITestCase):
    """Covers the alias endpoints matching the existing frontend's exact URLs/params."""

    def setUp(self):
        from .models import Category, Destination

        self.user = User.objects.create_user(email="compat@example.com", password="StrongPass123!", is_verified=True)
        self.category = Category.objects.create(name="Lakes")
        self.destination = Destination.objects.create(
            name="Rupa Lake", category=self.category, description="A quiet lake.",
            latitude=28.15, longitude=84.05, created_by=self.user, average_rating=4.5,
        )

    def test_recommendations_personalized_get(self):
        response = self.client.get("/api/v1/recommendations/personalized", {"lat": 28.15, "lng": 84.05})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_budget_summary_requires_auth(self):
        response = self.client.get("/api/v1/budget/summary")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_budget_summary_aggregates_user_entries(self):
        from .models import Budget

        self.client.force_authenticate(user=self.user)
        Budget.objects.create(user=self.user, title="Hotel", category="accommodation", amount=100)
        Budget.objects.create(user=self.user, title="Lunch", category="food", amount=20)
        response = self.client.get("/api/v1/budget/summary")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data["total_amount"]), 120)
        self.assertEqual(response.data["entry_count"], 2)

    def test_emergency_contacts_compat_requires_coords(self):
        response = self.client.get("/api/v1/emergency/contacts")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_emergency_contacts_compat_with_lat_lng(self):
        from .models import EmergencyContact

        EmergencyContact.objects.create(
            contact_type="police", name="Rupa Police Post", phone_number="+9779800000010",
            latitude=28.15, longitude=84.05,
        )
        response = self.client.get("/api/v1/emergency/contacts", {"lat": 28.15, "lng": 84.05})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_nearby_hospitals_and_police_are_type_filtered(self):
        from .models import EmergencyContact

        EmergencyContact.objects.create(
            contact_type="hospital", name="Rupa Clinic", phone_number="+9779800000011",
            latitude=28.15, longitude=84.05,
        )
        response = self.client.get("/api/v1/nearby/police", {"lat": 28.15, "lng": 84.05})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # only a hospital exists, not police

        response = self.client.get("/api/v1/nearby/hospitals", {"lat": 28.15, "lng": 84.05})
        self.assertEqual(len(response.data), 1)

    @patch("tourist.utils.requests.post", side_effect=requests.RequestException("down"))
    def test_navigation_route_compat_accepts_camelcase_fields(self, _mock):
        response = self.client.post("/api/v1/navigation/route", {
            "startLat": 28.15, "startLng": 84.05, "endLat": 28.17, "endLng": 84.07,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["routing_engine"], "bundled_nepal_graphml")
        self.assertTrue(response.data["route"])

    def test_navigation_route_compat_missing_fields(self):
        response = self.client.post("/api/v1/navigation/route", {"startLat": 28.15})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("tourist.utils.requests.post", side_effect=requests.RequestException("down"))
    def test_navigation_route_resolves_destination_name(self, _mock):
        response = self.client.post("/api/v1/navigation/route", {
            "start_latitude": 28.10, "start_longitude": 84.00, "destination_name": "Rupa",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["routing_engine"], "bundled_nepal_graphml")
        self.assertEqual(response.data["destination"]["id"], self.destination.id)

    def test_navigation_route_unknown_destination_name(self):
        response = self.client.post("/api/v1/navigation/route", {
            "start_latitude": 28.10, "start_longitude": 84.00, "destination_name": "Nonexistent Place XYZ",
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_weather_current_compat_requires_coords(self):
        response = self.client.get("/api/v1/weather/current/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weather_current_compat_returns_503_without_key(self):
        response = self.client.get("/api/v1/weather/current/", {"lat": 28.15, "lng": 84.05})
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_nearby_places_compat_includes_own_destinations(self):
        response = self.client.get("/api/v1/nearby/places", {"lat": 28.15, "lng": 84.05, "radius": 20000})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [p["name"] for p in response.data]
        self.assertIn("Rupa Lake", names)

    def test_budget_summary_trailing_slash_variant_works(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/budget/summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_notification_mark_read_accepts_put(self):
        from .models import Notification

        self.client.force_authenticate(user=self.user)
        notification = Notification.objects.create(user=self.user, title="Test", message="hi")
        response = self.client.put(f"/api/v1/notifications/{notification.id}/mark_read/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    @patch("tourist.utils.requests.post", side_effect=requests.RequestException("down"))
    def test_ml_budget_accepts_free_text_destination_and_style_field(self, _mock):
        """Matches BudgetEstimator.jsx's exact payload: {destination: 'Rupa Lake', style: 'standard', ...}."""
        response = self.client.post(reverse("ml-budget"), {
            "destination": "Rupa Lake", "style": "standard", "days": 3, "travelers": 2,
        })
        # ML service is simulated down, but the request itself must be
        # accepted (name resolved, style mapped) rather than 400ing on bad input.
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_destination_search_q_alias_actually_filters(self):
        from .models import Category, Destination

        Destination.objects.create(
            name="Unrelated Museum", category=self.category, description="x",
            latitude=1, longitude=1, created_by=self.user,
        )
        response = self.client.get("/api/v1/destinations/", {"q": "Rupa"})
        names = [d["name"] for d in response.data["results"]]
        self.assertIn("Rupa Lake", names)
        self.assertNotIn("Unrelated Museum", names)

    def test_destination_limit_alias_controls_page_size(self):
        response = self.client.get("/api/v1/destinations/", {"limit": 1})
        self.assertEqual(len(response.data["results"]), 1)

    def test_destination_featured_filter(self):
        response = self.client.get("/api/v1/destinations/", {"featured": "true"})
        names = [d["name"] for d in response.data["results"]]
        self.assertIn("Rupa Lake", names)  # rating 4.5 >= 4.0 threshold

    def test_ward_member_contact_appears_in_nearby_results(self):
        from .models import EmergencyContact

        EmergencyContact.objects.create(
            contact_type=EmergencyContact.ContactType.WARD_MEMBER, name="Sita Gurung",
            designation="Ward Member - Female", ward_number=5,
            phone_number="+9779800000020", latitude=28.15, longitude=84.05,
        )
        response = self.client.get(reverse("emergency-contact-nearest"), {
            "latitude": 28.15, "longitude": 84.05, "radius_km": 10, "contact_type": "ward_member",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["ward_number"], 5)
        self.assertEqual(response.data[0]["designation"], "Ward Member - Female")


class PublicConfigTests(APITestCase):
    @override_settings(MAPILLARY_ACCESS_TOKEN="test-mapillary-token")
    def test_public_config_exposes_mapillary_token(self):
        response = self.client.get("/api/v1/config/public/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("mapillary_access_token", response.data)
        self.assertTrue(response.data["mapillary_access_token"])


class DestinationEssentialsTests(APITestCase):
    def setUp(self):
        from .models import Category, Destination, Hotel

        self.admin = User.objects.create_superuser(email="admin8@example.com", password="AdminPass123!")
        self.category = Category.objects.create(name="Trekking")
        self.destination = Destination.objects.create(
            name="Mustang Trailhead", category=self.category, description="Gateway to Upper Mustang.",
            latitude=28.9977, longitude=83.8460, city="Mustang", country="Nepal", created_by=self.admin,
        )
        Hotel.objects.create(
            destination=self.destination, name="Mustang Guesthouse", price_per_night=25,
            booking_status="available", latitude=28.9977, longitude=83.8460,
        )

    def test_essentials_bundle_returns_hotels_and_degrades_gracefully(self):
        response = self.client.get(reverse("destination-essentials", kwargs={"slug": self.destination.slug}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["hotels"][0]["name"], "Mustang Guesthouse")
        # No Foursquare/Google/OpenWeather keys configured in tests -> empty, not an error.
        self.assertEqual(response.data["restaurants"], [])
        self.assertIsNone(response.data["weather"])
        self.assertIsNone(response.data["active_alert"])
        self.assertEqual(response.data["emergency_helplines"], [])

    def test_essentials_surfaces_disaster_helplines_when_alert_active(self):
        from .models import Alert, EmergencyContact

        Alert.objects.create(
            alert_type=Alert.AlertType.LANDSLIDE, title="Landslide risk near Mustang",
            description="Heavy rainfall increasing landslide risk.", severity=Alert.Severity.HIGH,
            city="Mustang", is_active=True,
        )
        EmergencyContact.objects.create(
            contact_type=EmergencyContact.ContactType.WARD_OFFICE, name="Mustang Ward Office",
            phone_number="+9779800000030", latitude=28.99, longitude=83.84,
        )
        response = self.client.get(reverse("destination-essentials", kwargs={"slug": self.destination.slug}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["active_alert"])
        self.assertEqual(response.data["active_alert"]["alert_type"], "landslide")
        self.assertEqual(len(response.data["emergency_helplines"]), 1)
        self.assertEqual(response.data["emergency_helplines"][0]["name"], "Mustang Ward Office")


class OSMOverpassTests(APITestCase):
    def test_essential_services_sync_requires_coords(self):
        response = self.client.post(reverse("osm-essential-sync"), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_essential_services_sync_degrades_gracefully(self):
        response = self.client.post(reverse("osm-essential-sync"), {"latitude": 28.21, "longitude": 83.96})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("created", response.data)

    def test_essential_services_nearby_reads_from_db(self):
        from .models import OSMEssentialService

        OSMEssentialService.objects.create(
            osm_id="node/1", category="hospital", name="Western Regional Hospital",
            phone="+977-61-520066", latitude=28.2380, longitude=83.9956,
        )
        response = self.client.get(reverse("osm-essential-nearby"), {"latitude": 28.21, "longitude": 83.96, "radius_km": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["name"], "Western Regional Hospital")
        self.assertIn("distance_km", response.data[0])

    def test_tourism_places_nearby_reads_from_db(self):
        from .models import OSMTourismPlace

        OSMTourismPlace.objects.create(
            osm_id="node/2", category="viewpoint", name="Sarangkot Viewpoint",
            latitude=28.2380, longitude=83.9536,
        )
        response = self.client.get(reverse("osm-tourism-nearby"), {"latitude": 28.21, "longitude": 83.96, "radius_km": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["category"], "viewpoint")


class RecommendationAndRiskArchitectureTests(APITestCase):
    def setUp(self):
        self.trekking = Category.objects.create(name="Trekking Test", slug="trekking")
        self.heritage = Category.objects.create(name="Heritage Test", slug="heritage")
        self.trek = Destination.objects.create(
            name="Test Himalayan Trek", slug="test-himalayan-trek", category=self.trekking,
            district="Kaski", province="Gandaki", latitude=28.4, longitude=84.0,
            recommended_days=7, short_description="A mountain trek and base camp adventure",
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
        )
        self.city = Destination.objects.create(
            name="Test Heritage Square", slug="test-heritage-square", category=self.heritage,
            district="Kathmandu", province="Bagmati", latitude=27.7, longitude=85.3,
            recommended_days=1, short_description="A cultural durbar heritage museum",
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
        )

    def test_recommendation_uses_form_preferences_and_explains_match(self):
        response = self.client.get(reverse("mood-recommendations"), {
            "mood": "trekking,adventure", "days": 7, "difficulty": "hard", "limit": 3,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["source"], "live_database_content_model")
        result = next(row for row in response.data["results"] if row["id"] == self.trek.id)
        self.assertTrue(result["why_recommended"])
        self.assertEqual(result["difficulty"], "hard")
        self.assertIn("risk_summary", result)

    def test_risk_response_separates_history_current_and_prediction(self):
        from datetime import date
        from django.utils import timezone
        from .models import CurrentHazard, RiskIncident, TravelRiskFeedback

        RiskIncident.objects.create(
            destination=self.trek, hazard_type="landslide", event_date=date(2025, 7, 1),
            title="Verified trail landslide", severity="high", source_type="official",
            source_name="Test authority", verified=True,
        )
        CurrentHazard.objects.create(
            destination=self.trek, hazard_type="heavy_rain", title="Heavy rain watch",
            severity="moderate", source_type="official", source_name="DHM test feed",
            observed_at=timezone.now(), verified=True,
        )
        TravelRiskFeedback.objects.create(
            destination=self.trek, destination_name=self.trek.name,
            hazard_witnessed="Landslide", overall_safety_rating=6,
        )
        response = self.client.get(reverse("destination-risk-assessment", kwargs={"destination_ref": self.trek.slug}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["overall"]["is_official_warning"])
        self.assertEqual(response.data["historical"]["incident_count"], 1)
        self.assertEqual(response.data["current_conditions"]["active_count"], 1)
        self.assertEqual(response.data["traveler_evidence"]["report_count"], 1)

    def test_destination_emergency_directory_is_distance_ranked(self):
        from .models import Hospital, PoliceStation
        Hospital.objects.create(
            destination=self.trek, name="Test Mountain Hospital", address="Kaski",
            phone="061123456", latitude=28.401, longitude=84.001, district="Kaski",
        )
        PoliceStation.objects.create(
            destination=self.trek, name="Test Mountain Police", address="Kaski",
            phone="", latitude=28.402, longitude=84.002,
        )
        response = self.client.get(reverse(
            "destination-emergency-services", kwargs={"destination_ref": self.trek.slug}
        ), {"radius_km": 25})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["location"]["destination_id"], self.trek.id)
        self.assertEqual(response.data["hospitals"][0]["phone_number"], "061123456")
        self.assertEqual(response.data["police"][0]["phone_number"], "100")
        self.assertTrue(response.data["police"][0]["phone_is_national_fallback"])
        self.assertIn("risk", response.data)
        self.assertEqual(response.data["national_hotlines"][0]["phone_number"], "1144")

    def test_coordinate_emergency_directory_requires_valid_coordinates(self):
        response = self.client.get(reverse("nearby-emergency-services"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("tourist.community_data_service.sync_submission_csv")
    def test_admin_approval_publishes_community_hospital(self, sync_csv):
        from .community_data_service import publish_submission
        from .models import Hospital, InfrastructureSubmission
        admin = User.objects.create_user(
            email="infra-admin@example.com", password="StrongPass123!", role="admin", is_verified=True,
        )
        submission = InfrastructureSubmission.objects.create(
            submitted_by=admin, destination=self.trek, place_type="hospital",
            name="Community Mountain Clinic", phone="061999999", address="Ward 4",
            district="Kaski", province="Gandaki", latitude=28.401, longitude=84.001,
            municipality="Machhapuchhre", municipality_type="rural_municipality",
            route_origin="Pokhara", transport_mode="Jeep", travel_time_minutes=90,
        )
        publish_submission(submission, admin)
        submission.refresh_from_db()
        self.assertEqual(submission.status, "approved")
        self.assertTrue(Hospital.objects.filter(name="Community Mountain Clinic").exists())
        sync_csv.assert_called_once()

    def test_osm_nearby_returns_nearest_outside_small_radius(self):
        from .models import OSMEssentialService
        OSMEssentialService.objects.create(
            osm_id="node/far-bank", category="bank", name="Verified Far Bank",
            latitude=28.80, longitude=84.80, address="Regional center",
        )
        response = self.client.get(reverse("osm-essential-nearby"), {
            "latitude": 28.4, "longitude": 84.0, "radius_km": 1, "category": "bank",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["name"], "Verified Far Bank")
        self.assertTrue(response.data[0]["outside_requested_radius"])

    def test_itinerary_days_are_enriched_with_nearest_services(self):
        from .models import Hospital, Hotel, PoliceStation
        from .views_ml import enrich_itinerary_with_services
        Hotel.objects.create(
            destination=self.trek, name="Trail Hotel", latitude=28.401, longitude=84.001,
            price_per_night=2500, currency="NPR",
        )
        Hospital.objects.create(
            destination=self.trek, name="Trail Hospital", address="Kaski", phone="102",
            latitude=28.402, longitude=84.002, district="Kaski",
        )
        PoliceStation.objects.create(
            destination=self.trek, name="Trail Police", address="Kaski", phone="100",
            latitude=28.403, longitude=84.003,
        )
        payload = {"itinerary": [{"day": 1, "city": "Kaski", "destinations": [{
            "name": self.trek.name, "latitude": 28.4, "longitude": 84.0,
        }]}]}
        enriched = enrich_itinerary_with_services(payload)
        services = enriched["itinerary"][0]["nearby_services"]
        self.assertEqual(services["hotels"][0]["name"], "Trail Hotel")
        self.assertEqual(services["hospitals"][0]["name"], "Trail Hospital")
        self.assertEqual(services["police"][0]["name"], "Trail Police")

    def test_geofenced_alert_notifies_nearby_user_and_family(self):
        from .models import Alert, FamilyLink, Notification
        nearby = User.objects.create_user(
            email="nearby@example.com", password="StrongPass123!", is_verified=True,
            latitude=28.400, longitude=84.000,
        )
        family = User.objects.create_user(
            email="family@example.com", password="StrongPass123!", is_verified=True,
            latitude=27.7, longitude=85.3,
        )
        FamilyLink.objects.create(requester=nearby, member=family, status="accepted")
        Alert.objects.create(
            alert_type="flood", title="Test flood warning", description="Move away from the river.",
            severity="high", latitude=28.401, longitude=84.001, radius_km=4,
            source="DHM test", source_url="https://example.com/advisory", is_verified=True,
        )
        self.assertTrue(Notification.objects.filter(user=nearby, title__icontains="Nearby").exists())
        self.assertTrue(Notification.objects.filter(user=family, related_alert__title="Test flood warning").exists())

    def test_cross_destination_image_is_not_used_as_fallback(self):
        from .models import DestinationImage
        from .serializers import DestinationListSerializer
        DestinationImage.objects.create(
            destination=self.trek, external_url="https://example.com/rara-lake.jpg",
            caption=self.trek.name, alt_text=self.trek.name,
            is_cover=True, is_verified=True, verification_status="approved",
        )
        data = DestinationListSerializer(self.trek).data
        self.assertIsNone(data["cover_image_url"])

    def test_destination_linked_unverified_media_remains_visible_for_admin_review(self):
        from .models import DestinationImage
        from .serializers import DestinationListSerializer
        DestinationImage.objects.create(
            destination=self.trek, external_url="https://images.example.com/asset-abc123.jpg",
            is_cover=True, is_verified=False, verification_status="pending",
        )
        data = DestinationListSerializer(self.trek).data
        self.assertEqual(data["cover_image_url"], "https://images.example.com/asset-abc123.jpg")

    def test_district_gallery_uses_canonical_77_districts(self):
        from .models import DestinationImage
        DestinationImage.objects.create(
            destination=self.trek, external_url="https://example.com/test-himalayan-trek.jpg",
            is_cover=True, verification_status="approved",
        )
        response = self.client.get(reverse("district-gallery"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["district_count"], 77)
        kaski = next(item for item in response.data["districts"] if item["district"] == "Kaski")
        self.assertEqual(len(kaski["images"]), 1)

    def test_verified_risk_feed_ingestion_keeps_source_provenance(self):
        from .models import CurrentHazard
        from .risk_ingestion import ingest_records
        summary = ingest_records([{
            "destination_slug": self.trek.slug, "record_kind": "current",
            "hazard_type": "heavy_rain", "title": "Official rainfall watch",
            "severity": "high", "source_url": "https://example.com/dhm-record",
            "observed_at": "2026-08-18T08:00:00Z", "published_at": "2026-08-18T07:55:00Z",
            "affected_area": "Upper Kaski slopes",
        }], "dhm", verified=True)
        self.assertEqual(summary["current_created"], 1)
        hazard = CurrentHazard.objects.get(title="Official rainfall watch")
        self.assertTrue(hazard.verified)
        self.assertEqual(hazard.source_type, "official")
        self.assertEqual(hazard.affected_area, "Upper Kaski slopes")

    def test_verified_critical_warning_marks_recommendation_unavailable(self):
        from django.utils import timezone
        from .models import CurrentHazard
        CurrentHazard.objects.create(
            destination=self.trek, hazard_type="landslide", title="Trail officially closed",
            severity="critical", source_type="official", source_name="Test authority",
            source_url="https://example.com/closure", observed_at=timezone.now(),
            verified=True, is_active=True,
        )
        response = self.client.get(reverse("mood-recommendations"), {
            "mood": "trekking", "days": 7, "limit": 6,
        })
        result = next(row for row in response.data["results"] if row["id"] == self.trek.id)
        self.assertEqual(result["safety_context"]["availability"], "temporarily_unavailable")
        self.assertEqual(result["safety_context"]["current_warning"]["severity"], "critical")

    def test_admin_data_explorer_searches_destinations(self):
        admin = User.objects.create_user(email="explorer-admin@example.com", password="StrongPass123!", role="admin", is_verified=True, is_staff=True)
        self.client.force_authenticate(admin)
        response = self.client.get(reverse("admin-data-explorer"), {"resource": "destinations", "q": "Test Himalayan"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.trek.id)

    def test_staff_write_requires_exact_capability(self):
        from .models import StaffCapabilityProfile
        staff = User.objects.create_user(email="limited-staff@example.com", password="StrongPass123!", role="staff", is_staff=True, is_verified=True)
        StaffCapabilityProfile.objects.create(user=staff, capabilities={"images": ["view"]})
        self.client.force_authenticate(staff)
        denied = self.client.post("/api/v1/categories/", {"name": "Denied Category", "slug": "denied-category"})
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        staff.capability_profile.capabilities = {"destinations": ["view", "add"]}
        staff.capability_profile.save()
        allowed = self.client.post("/api/v1/categories/", {"name": "Allowed Category", "slug": "allowed-category"})
        self.assertEqual(allowed.status_code, status.HTTP_201_CREATED)

    def test_cms_rejects_unsafe_routes_and_colors(self):
        from .models import StaffCapabilityProfile
        admin=User.objects.create_user(email="cms-admin@example.com",password="StrongPass123!",role="admin",is_staff=True,is_verified=True)
        self.client.force_authenticate(admin)
        route=self.client.post(reverse("admin-cms"),{"resource":"navigation","location":"navbar","label":"Bad","route":"javascript:alert(1)"})
        self.assertEqual(route.status_code,status.HTTP_400_BAD_REQUEST)
        color=self.client.post(reverse("admin-cms"),{"resource":"settings","key":"branding","value":{"primary_color":"red<script>"}})
        self.assertEqual(color.status_code,status.HTTP_400_BAD_REQUEST)

    def test_notification_broadcast_requires_settings_capability(self):
        from .models import StaffCapabilityProfile, Notification
        staff=User.objects.create_user(email="notice-staff@example.com",password="StrongPass123!",role="staff",is_staff=True,is_verified=True)
        StaffCapabilityProfile.objects.create(user=staff,capabilities={"settings":["view"]})
        self.client.force_authenticate(staff)
        denied=self.client.post(reverse("admin-notifications"),{"title":"Test","message":"Denied"})
        self.assertEqual(denied.status_code,status.HTTP_403_FORBIDDEN)
        staff.capability_profile.capabilities={"settings":["view","add"]};staff.capability_profile.save()
        allowed=self.client.post(reverse("admin-notifications"),{"title":"Test","message":"Allowed","role":"staff"})
        self.assertEqual(allowed.status_code,status.HTTP_201_CREATED)
        self.assertTrue(Notification.objects.filter(user=staff,title="Test").exists())

    def test_safety_crud_requires_capabilities(self):
        from django.utils import timezone
        from .models import StaffCapabilityProfile
        staff=User.objects.create_user(email="safety-staff@example.com",password="StrongPass123!",role="staff",is_staff=True,is_verified=True)
        StaffCapabilityProfile.objects.create(user=staff,capabilities={"safety":["view"]})
        self.client.force_authenticate(staff)
        payload={"destination":self.trek.id,"hazard_type":"heavy_rain","title":"Field rain watch","description":"test","severity":"moderate","source_type":"admin","source_name":"Field team","observed_at":timezone.now().isoformat(),"is_active":True,"verified":False}
        denied=self.client.post("/api/v1/admin/current-hazards/",payload)
        self.assertEqual(denied.status_code,status.HTTP_403_FORBIDDEN)
        staff.capability_profile.capabilities={"safety":["view","add","change"]};staff.capability_profile.save()
        created=self.client.post("/api/v1/admin/current-hazards/",payload)
        self.assertEqual(created.status_code,status.HTTP_201_CREATED)
        updated=self.client.patch(f"/api/v1/admin/current-hazards/{created.data['id']}/",{"is_active":False})
        self.assertEqual(updated.status_code,status.HTTP_200_OK)
        self.assertFalse(updated.data["is_active"])

    def test_global_admin_search_filters_results_by_capability(self):
        from .models import StaffCapabilityProfile
        staff=User.objects.create_user(email="search-staff@example.com",password="StrongPass123!",role="staff",is_staff=True,is_verified=True)
        StaffCapabilityProfile.objects.create(user=staff,capabilities={"destinations":["view"]})
        self.client.force_authenticate(staff)
        response=self.client.get(reverse("admin-global-search"),{"q":"Test"})
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertTrue(any(item["type"]=="destination" for item in response.data["results"]))
        self.assertFalse(any(item["type"]=="user" for item in response.data["results"]))

    def test_media_delete_replaces_destination_cover(self):
        from .models import DestinationImage, StaffCapabilityProfile
        staff=User.objects.create_user(email="media-delete@example.com",password="StrongPass123!",role="staff",is_staff=True,is_verified=True)
        StaffCapabilityProfile.objects.create(user=staff,capabilities={"images":["view","delete"]})
        cover=DestinationImage.objects.create(destination=self.trek,external_url="https://example.com/test-himalayan-trek-cover.jpg",is_cover=True,ordering=0)
        replacement=DestinationImage.objects.create(destination=self.trek,external_url="https://example.com/test-himalayan-trek-second.jpg",is_cover=False,ordering=1)
        self.client.force_authenticate(staff)
        response=self.client.delete(reverse("admin-media-library"),{"id":cover.id},format="json")
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        replacement.refresh_from_db();self.assertTrue(replacement.is_cover)
        self.assertEqual(response.data["replacement_cover_id"],replacement.id)

    def test_dataset_upload_validation_import_backup_and_capability(self):
        import tempfile
        from pathlib import Path
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from .models import StaffCapabilityProfile
        from .views_admin import AdminDatasetManagerView
        staff=User.objects.create_user(email="dataset-staff@example.com",password="StrongPass123!",role="staff",is_staff=True,is_verified=True)
        StaffCapabilityProfile.objects.create(user=staff,capabilities={"datasets":["view"]})
        self.client.force_authenticate(staff)
        denied=self.client.post(reverse("admin-datasets"),{"dataset":"risk","file":SimpleUploadedFile("risk.csv",b"place,risk\nTest,low\n",content_type="text/csv")},format="multipart")
        self.assertEqual(denied.status_code,status.HTTP_403_FORBIDDEN)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/"dataset").mkdir();(root/"dataset/risk.csv").write_text("place,risk\nOld,low\n")
            original=AdminDatasetManagerView.DATASETS;AdminDatasetManagerView.DATASETS={"risk":"dataset/risk.csv"}
            try:
                staff.capability_profile.capabilities={"datasets":["view","add","change"]};staff.capability_profile.save()
                with override_settings(BASE_DIR=root):
                    valid=self.client.post(reverse("admin-datasets"),{"dataset":"risk","file":SimpleUploadedFile("risk.csv",b"place,risk\nNew,high\n",content_type="text/csv")},format="multipart")
                    self.assertEqual(valid.status_code,status.HTTP_201_CREATED)
                    imported=self.client.put(reverse("admin-datasets"),{"dataset":"risk","token":valid.data["token"]},format="json")
                    self.assertEqual(imported.status_code,status.HTTP_200_OK)
                    self.assertIn("New,high",(root/"dataset/risk.csv").read_text())
                    self.assertTrue(list((root/"dataset").glob("risk.backup-*.csv")))
            finally: AdminDatasetManagerView.DATASETS=original

    def test_feedback_thread_assignment_reply_and_notification(self):
        from .models import StaffCapabilityProfile, UserFeedback, Notification
        user=User.objects.create_user(email="feedback-user@example.com",password="StrongPass123!",is_verified=True)
        staff=User.objects.create_user(email="feedback-staff@example.com",password="StrongPass123!",role="staff",is_staff=True,is_verified=True)
        StaffCapabilityProfile.objects.create(user=staff,capabilities={"feedback":["view","change"]})
        thread=UserFeedback.objects.create(user=user,email=user.email,subject="Route correction",message="Wrong route",category="route")
        self.client.force_authenticate(staff)
        updated=self.client.patch(reverse("admin-feedback-reply",kwargs={"id":thread.id}),{"status":"in_progress","priority":"high","assigned_to":staff.id},format="json")
        self.assertEqual(updated.status_code,status.HTTP_200_OK)
        replied=self.client.post(reverse("admin-feedback-reply",kwargs={"id":thread.id}),{"reply":"We are checking this route.","is_internal":False},format="json")
        self.assertEqual(replied.status_code,status.HTTP_200_OK)
        self.assertTrue(Notification.objects.filter(user=user,title__icontains="Reply").exists())

    def test_reports_require_audit_capability_and_return_trends(self):
        from .models import StaffCapabilityProfile
        staff=User.objects.create_user(email="reports-staff@example.com",password="StrongPass123!",role="staff",is_staff=True,is_verified=True)
        StaffCapabilityProfile.objects.create(user=staff,capabilities={"audit":["view"]})
        self.client.force_authenticate(staff)
        response=self.client.get(reverse("admin-reports"),{"from":"2026-01-01","to":"2026-12-31"})
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertIn("trends",response.data);self.assertIn("staff_activity",response.data)

    def test_recommendation_events_require_consent(self):
        user = User.objects.create_user(email="events@example.com", password="StrongPass123!", is_verified=True)
        self.client.force_authenticate(user)
        denied = self.client.post(reverse("recommendation-events"), {
            "event_type": "select", "destination": self.trek.id, "consented": False,
        })
        self.assertEqual(denied.status_code, status.HTTP_400_BAD_REQUEST)
        accepted = self.client.post(reverse("recommendation-events"), {
            "event_type": "select", "destination": self.trek.id,
            "score": 0.91, "context": {"source": "test"}, "consented": True,
        })
        self.assertEqual(accepted.status_code, status.HTTP_201_CREATED)

    def test_verified_news_and_station_observation_remain_separate_from_warning(self):
        from django.utils import timezone
        from .models import RiskNewsReport, RiskObservation
        RiskNewsReport.objects.create(
            destination=self.trek, title="Road concerns reported", hazard_type="road_accident",
            source_name="Verified newsroom", source_url="https://example.com/news/road",
            published_at=timezone.now(), verification_status="verified",
        )
        RiskObservation.objects.create(
            destination=self.trek, observation_type="rainfall", value=32.5, unit="mm",
            trend="rising", station_name="Kaski Test Station", distance_km=6.4,
            source_name="DHM test", source_url="https://example.com/station",
            observed_at=timezone.now(), verified=True,
        )
        response = self.client.get(reverse("destination-risk-assessment", kwargs={"destination_ref": self.trek.slug}))
        self.assertEqual(len(response.data["verified_news"]), 1)
        self.assertEqual(response.data["observations"][0]["station_name"], "Kaski Test Station")
        self.assertFalse(response.data["current_conditions"]["official_warning_present"])

    @override_settings(DHM_FEED_URL="", BIPAD_FEED_URL="")
    def test_unconfigured_official_feed_is_reported_not_fabricated(self):
        from .official_connectors import fetch_official_feed
        result = fetch_official_feed("dhm")
        self.assertFalse(result["configured"])
        self.assertFalse(result["ingested"])

    @override_settings(ROUTING_API_URL="", LOCAL_GRAPH_ROUTING_ENABLED=False)
    def test_routing_fallback_labels_straight_line_distance(self):
        response = self.client.post(reverse("route-metrics"), {
            "start_latitude": 28.2096, "start_longitude": 83.9856,
            "end_latitude": 28.2380, "end_longitude": 83.9956,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "routing_unconfigured")
        self.assertIsNone(response.data["road_distance_km"])
        self.assertGreater(response.data["straight_line_km"], 0)


class AdminUserManagementSecurityTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="user-admin@example.com", password="StrongPass123!")
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role"])
        self.target = User.objects.create_user(email="target@example.com", password="StrongPass123!", is_verified=False)
        self.client.force_authenticate(self.admin)

    def test_filterable_directory_is_paginated(self):
        response = self.client.get(reverse("admin-users"), {"q": "target", "status": "active", "page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["email"], self.target.email)

    def test_admin_cannot_change_own_access_state(self):
        response = self.client.put(reverse("admin-update-user-status", kwargs={"id": self.admin.id}), {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_staff_capability_cannot_escalate_user_to_admin(self):
        from .models import StaffCapabilityProfile
        staff = User.objects.create_user(email="limited-staff@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=staff, capabilities={"users": ["view", "change"]})
        self.client.force_authenticate(staff)
        response = self.client.put(reverse("admin-update-user-status", kwargs={"id": self.target.id}), {"role": "admin"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.target.refresh_from_db()
        self.assertEqual(self.target.role, User.Role.TOURIST)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_verification_reminder_does_not_verify_identity(self):
        response = self.client.post(reverse("admin-send-verification", kwargs={"id": self.target.id}), {"channel": "email"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_verified)

    def test_delete_is_retention_safe_deactivation(self):
        response = self.client.delete(reverse("admin-update-user-status", kwargs={"id": self.target.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)
        self.assertTrue(User.objects.filter(pk=self.target.pk).exists())

    def test_detail_includes_activity_and_audit_history(self):
        self.client.post(reverse("admin-user-access-action", kwargs={"id": self.target.id}), {"action": "verify"}, format="json")
        response = self.client.get(reverse("admin-user-detail-full", kwargs={"id": self.target.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("activity", response.data)
        self.assertTrue(response.data["role_history"])


class CMSPublishingWorkflowTests(APITestCase):
    def setUp(self):
        from .models import ManagedPage, ContentSection
        self.admin = User.objects.create_superuser(email="cms-workflow@example.com", password="StrongPass123!")
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role"])
        self.client.force_authenticate(self.admin)
        self.page = ManagedPage.objects.create(route="/workflow-test", key="workflow-test", title="Workflow test", status="draft", updated_by=self.admin)
        self.section = ContentSection.objects.create(page=self.page, key="hero", title="Draft hero", body="Not public yet", status="draft", updated_by=self.admin)

    def test_draft_is_previewable_but_not_public(self):
        preview = self.client.get(reverse("admin-cms"), {"resource": "pages", "id": self.page.id, "preview": "true"})
        self.assertEqual(preview.status_code, status.HTTP_200_OK)
        self.assertEqual(preview.data["preview"]["sections"][0]["title"], "Draft hero")
        public = self.client.get(reverse("public-config"))
        self.assertNotIn("workflow-test", [page["key"] for page in public.data["pages"]])

    def test_publish_actions_make_page_and_section_public(self):
        for resource, object_id in (("pages", self.page.id), ("sections", self.section.id)):
            response = self.client.patch(reverse("admin-cms"), {"resource": resource, "id": object_id, "action": "publish"}, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        public = self.client.get(reverse("public-config"))
        page = next(item for item in public.data["pages"] if item["key"] == "workflow-test")
        self.assertEqual(page["sections"][0]["body"], "Not public yet")

    def test_updates_create_history_and_rollback_creates_new_revision(self):
        from .models import CMSRevision
        changed = self.client.patch(reverse("admin-cms"), {"resource": "pages", "id": self.page.id, "title": "Changed title"}, format="json")
        self.assertEqual(changed.status_code, status.HTTP_200_OK)
        first = CMSRevision.objects.filter(resource="pages", object_id=self.page.id).order_by("revision_number").first()
        restored = self.client.patch(reverse("admin-cms"), {"resource": "pages", "id": self.page.id, "action": "rollback", "revision_id": first.id}, format="json")
        self.assertEqual(restored.status_code, status.HTTP_200_OK)
        self.page.refresh_from_db()
        self.assertEqual(self.page.title, "Workflow test")
        self.assertEqual(CMSRevision.objects.filter(resource="pages", object_id=self.page.id).count(), 3)

    def test_future_schedule_and_due_publication(self):
        from datetime import timedelta
        from django.utils import timezone
        scheduled = self.client.patch(reverse("admin-cms"), {"resource": "pages", "id": self.page.id, "action": "schedule", "scheduled_publish_at": (timezone.now() + timedelta(hours=1)).isoformat()}, format="json")
        self.assertEqual(scheduled.status_code, status.HTTP_200_OK)
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, "scheduled")
        self.page.scheduled_publish_at = timezone.now() - timedelta(minutes=1)
        self.page.save(update_fields=["scheduled_publish_at"])
        self.client.get(reverse("public-config"))
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, "published")

    def test_invalid_or_past_schedule_is_rejected(self):
        from datetime import timedelta
        from django.utils import timezone
        response = self.client.patch(reverse("admin-cms"), {"resource": "pages", "id": self.page.id, "action": "schedule", "scheduled_publish_at": (timezone.now() - timedelta(hours=1)).isoformat()}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_without_change_capability_cannot_publish(self):
        from .models import StaffCapabilityProfile
        staff = User.objects.create_user(email="cms-viewer@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=staff, capabilities={"content": ["view"]})
        self.client.force_authenticate(staff)
        response = self.client.patch(reverse("admin-cms"), {"resource": "pages", "id": self.page.id, "action": "publish"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReviewModerationWorkflowTests(APITestCase):
    def setUp(self):
        from .models import StaffCapabilityProfile
        from booking.models import HotelReview
        self.admin = User.objects.create_user(email="review-admin@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=self.admin, capabilities={"reviews": ["view", "change", "approve", "delete"]})
        self.author = User.objects.create_user(email="reviewer@example.com", password="StrongPass123!", is_verified=True)
        category = Category.objects.create(name="Review Test")
        self.destination = Destination.objects.create(name="Review Valley", category=category, description="Test", latitude=28, longitude=84, created_by=self.admin)
        self.hotel = Hotel.objects.create(destination=self.destination, name="Review Lodge", price_per_night=20)
        self.destination_review = Review.objects.create(destination=self.destination, user=self.author, comment="Destination comment", moderation_status="pending")
        self.hotel_review = HotelReview.objects.create(hotel=self.hotel, user=self.author, rating=4, comment="Hotel comment", moderation_status="pending")

    def test_pending_reviews_are_hidden_from_public_apis(self):
        destination = self.client.get(reverse("review-list"), {"destination": self.destination.id})
        hotel = self.client.get(reverse("hotel-review-list"), {"hotel": self.hotel.id})
        self.assertEqual(destination.data["count"], 0)
        self.assertEqual(hotel.data["count"], 0)

    def test_author_can_see_own_pending_review(self):
        self.client.force_authenticate(self.author)
        response = self.client.get(reverse("review-list"), {"destination": self.destination.id})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["moderation_status"], "pending")

    def test_approve_publishes_review_and_writes_audit(self):
        from audit.models import AuditLog
        self.client.force_authenticate(self.admin)
        response = self.client.patch(reverse("admin-review-moderation"), {"type": "destination", "ids": [self.destination_review.id], "action": "approve"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(None)
        public = self.client.get(reverse("review-list"), {"destination": self.destination.id})
        self.assertEqual(public.data["count"], 1)
        self.assertTrue(AuditLog.objects.filter(action="reviews.approve").exists())

    def test_flag_requires_change_and_archive_requires_delete_capability(self):
        from .models import StaffCapabilityProfile
        limited = User.objects.create_user(email="review-limited@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=limited, capabilities={"reviews": ["view"]})
        self.client.force_authenticate(limited)
        denied = self.client.patch(reverse("admin-review-moderation"), {"type": "destination", "id": self.destination_review.id, "action": "flag", "note": "Needs review"}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

    def test_archive_preserves_review_and_restore_returns_to_pending(self):
        self.client.force_authenticate(self.admin)
        archived = self.client.patch(reverse("admin-review-moderation"), {"type": "hotel", "id": self.hotel_review.id, "action": "archive", "note": "Policy violation"}, format="json")
        self.assertEqual(archived.status_code, status.HTTP_200_OK)
        from booking.models import HotelReview
        self.assertTrue(HotelReview.objects.filter(pk=self.hotel_review.id, moderation_status="archived").exists())
        restored = self.client.patch(reverse("admin-review-moderation"), {"type": "hotel", "id": self.hotel_review.id, "action": "restore"}, format="json")
        self.assertEqual(restored.status_code, status.HTTP_200_OK)
        self.hotel_review.refresh_from_db()
        self.assertEqual(self.hotel_review.moderation_status, "pending")

    def test_owner_delete_archives_instead_of_hard_deleting(self):
        self.client.force_authenticate(self.author)
        response = self.client.delete(reverse("review-detail", kwargs={"pk": self.destination_review.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.destination_review.refresh_from_db()
        self.assertEqual(self.destination_review.moderation_status, "archived")

    def test_user_cannot_modify_another_users_hotel_review(self):
        stranger = User.objects.create_user(email="review-stranger@example.com", password="StrongPass123!")
        self.client.force_authenticate(stranger)
        response = self.client.delete(reverse("hotel-review-detail", kwargs={"pk": self.hotel_review.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(type(self.hotel_review).objects.filter(pk=self.hotel_review.id).exists())


class StaffWorkspaceScopeTests(APITestCase):
    def setUp(self):
        from .models import StaffCapabilityProfile
        from admin_panel.models import AdminTask, HotelAssignment
        self.superadmin = User.objects.create_superuser(email="workspace-admin@example.com", password="StrongPass123!")
        self.staff = User.objects.create_user(email="kaski-staff@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=self.staff, capabilities={"dashboard": ["view"], "destinations": ["view", "approve"], "images": ["view", "approve"], "hotels": ["view"]}, managed_districts=["Kaski"])
        category = Category.objects.create(name="Workspace Test")
        self.kaski = Destination.objects.create(name="Kaski Queue", category=category, description="Test", district="Kaski", status="pending", latitude=28, longitude=84, created_by=self.superadmin)
        self.mustang = Destination.objects.create(name="Mustang Queue", category=category, description="Test", district="Mustang", status="pending", latitude=29, longitude=84, created_by=self.superadmin)
        self.kaski_hotel = Hotel.objects.create(destination=self.kaski, name="Assigned Kaski Hotel", price_per_night=30)
        self.mustang_hotel = Hotel.objects.create(destination=self.mustang, name="Unassigned Mustang Hotel", price_per_night=40)
        HotelAssignment.objects.create(hotel=self.kaski_hotel, admin=self.staff, assigned_by=self.superadmin)
        self.task = AdminTask.objects.create(title="Verify Kaski queue", assigned_to=self.staff, assigned_by=self.superadmin)
        self.client.force_authenticate(self.staff)

    def test_destination_queue_is_limited_to_managed_districts(self):
        response = self.client.get(reverse("staff-workspace"), {"module": "destinations"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in response.data["results"]], [self.kaski.id])

    def test_staff_cannot_act_outside_district_scope(self):
        denied = self.client.post(reverse("staff-workspace"), {"module": "destinations", "id": self.mustang.id, "action": "approve"}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_404_NOT_FOUND)
        allowed = self.client.post(reverse("staff-workspace"), {"module": "destinations", "id": self.kaski.id, "action": "approve"}, format="json")
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.kaski.refresh_from_db()
        self.assertEqual(self.kaski.status, "approved")

    def test_unassigned_module_is_denied_by_backend(self):
        response = self.client.get(reverse("staff-workspace"), {"module": "safety"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_hotel_workspace_only_returns_explicit_assignments(self):
        response = self.client.get(reverse("staff-workspace"), {"module": "hotels"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in response.data["results"]], [self.kaski_hotel.id])

    def test_staff_can_complete_only_own_tasks(self):
        from admin_panel.models import AdminTask
        other = AdminTask.objects.create(title="Other task", assigned_to=self.superadmin, assigned_by=self.superadmin)
        denied = self.client.post(reverse("staff-workspace"), {"module": "tasks", "id": other.id, "action": "completed"}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_400_BAD_REQUEST)
        allowed = self.client.post(reverse("staff-workspace"), {"module": "tasks", "id": self.task.id, "action": "completed"}, format="json")
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")
        self.assertIsNotNone(self.task.completed_at)

    def test_staff_task_patch_cannot_reassign_or_edit_task(self):
        response = self.client.patch(f"/api/v1/admin-panel/tasks/{self.task.id}/", {"assigned_to": self.superadmin.id, "title": "Escalated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to, self.staff)

    def test_traveler_cannot_self_verify_expense_submission(self):
        traveler = User.objects.create_user(email="expense-traveler@example.com", password="StrongPass123!")
        self.client.force_authenticate(traveler)
        response = self.client.post(reverse("expense-feedback-list"), {"destination": self.kaski.id, "destination_name": self.kaski.name, "num_people": 1, "num_days": 1, "is_employee_verified": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["is_employee_verified"])

    def test_field_feedback_lists_are_private_and_district_scoped(self):
        from .models import TravelExpenseFeedback
        own = TravelExpenseFeedback.objects.create(user=self.staff, destination=self.kaski, destination_name=self.kaski.name)
        TravelExpenseFeedback.objects.create(user=self.superadmin, destination=self.mustang, destination_name=self.mustang.name)
        # Add budget view while retaining the Kaski district scope.
        self.staff.capability_profile.capabilities["budget"] = ["view"]
        self.staff.capability_profile.save(update_fields=["capabilities"])
        response = self.client.get(reverse("expense-feedback-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in response.data["results"]], [own.id])


class BrandingThemeTranslationTests(APITestCase):
    def setUp(self):
        from .models import ManagedPage, ContentSection, ManagedNavigationItem
        self.admin = User.objects.create_superuser(email="branding-admin@example.com", password="StrongPass123!")
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role"])
        self.client.force_authenticate(self.admin)
        self.page = ManagedPage.objects.create(route="/translated-page", key="translated-page", title="English page", status="published")
        self.section = ContentSection.objects.create(page=self.page, key="hero", title="English hero", body="English body", status="published")
        self.nav = ManagedNavigationItem.objects.create(location="navbar", label="English link", route="/translated-page")

    def test_safe_theme_preset_is_published_without_arbitrary_css(self):
        response = self.client.patch(reverse("admin-branding"), {"branding": {"site_title": "Tourism Nepal", "theme_preset": "forest", "facebook_url": "https://facebook.com/nepal"}}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["branding"]["primary_color"], "#166534")
        denied = self.client.patch(reverse("admin-branding"), {"branding": {"custom_css": "body{display:none}"}}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_400_BAD_REQUEST)

    def test_social_links_require_https(self):
        response = self.client.patch(reverse("admin-branding"), {"branding": {"theme_preset": "himalayan", "facebook_url": "javascript:alert(1)"}}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_logo_upload_and_invalid_favicon_dimensions(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        buffer = io.BytesIO(); Image.new("RGB", (120, 60), "blue").save(buffer, format="PNG")
        logo = self.client.post(reverse("admin-branding"), {"kind": "logo", "file": SimpleUploadedFile("logo.png", buffer.getvalue(), content_type="image/png")}, format="multipart")
        self.assertEqual(logo.status_code, status.HTTP_201_CREATED)
        buffer = io.BytesIO(); Image.new("RGB", (64, 32), "red").save(buffer, format="PNG")
        favicon = self.client.post(reverse("admin-branding"), {"kind": "favicon", "file": SimpleUploadedFile("favicon.png", buffer.getvalue(), content_type="image/png")}, format="multipart")
        self.assertEqual(favicon.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cms_translation_overlays_only_requested_language(self):
        for target, object_id, content in (("pages", self.page.id, {"title": "नेपाली पृष्ठ"}), ("sections", self.section.id, {"title": "नेपाली शीर्षक", "body": "नेपाली सामग्री"}), ("navigation", self.nav.id, {"label": "नेपाली लिङ्क"})):
            response = self.client.post(reverse("admin-cms"), {"resource": "translations", "target_resource": target, "object_id": object_id, "language_code": "ne", "content": content}, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        nepali = self.client.get(reverse("public-config"), {"lang": "ne"})
        page = next(row for row in nepali.data["pages"] if row["id"] == self.page.id)
        self.assertEqual(page["title"], "नेपाली पृष्ठ")
        self.assertEqual(page["sections"][0]["body"], "नेपाली सामग्री")
        self.assertEqual(next(row for row in nepali.data["navigation"] if row["id"] == self.nav.id)["label"], "नेपाली लिङ्क")
        english = self.client.get(reverse("public-config"), {"lang": "en"})
        self.assertEqual(next(row for row in english.data["pages"] if row["id"] == self.page.id)["title"], "English page")

    def test_translation_rejects_unsupported_fields_and_missing_target(self):
        bad_field = self.client.post(reverse("admin-cms"), {"resource": "translations", "target_resource": "pages", "object_id": self.page.id, "language_code": "ne", "content": {"script": "alert(1)"}}, format="json")
        self.assertEqual(bad_field.status_code, status.HTTP_400_BAD_REQUEST)
        missing = self.client.post(reverse("admin-cms"), {"resource": "translations", "target_resource": "pages", "object_id": 999999, "language_code": "ne", "content": {"title": "Missing"}}, format="json")
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)

    def test_navigation_rejects_cross_location_parent_and_cycles(self):
        from .models import ManagedNavigationItem
        footer = ManagedNavigationItem.objects.create(location="footer", label="Footer", route="/about")
        cross = self.client.post(reverse("admin-cms"), {"resource": "navigation", "location": "navbar", "label": "Bad child", "route": "/bad", "parent_id": footer.id}, format="json")
        self.assertEqual(cross.status_code, status.HTTP_400_BAD_REQUEST)
        child = ManagedNavigationItem.objects.create(location="navbar", label="Child", route="/child", parent=self.nav)
        cycle = self.client.patch(reverse("admin-cms"), {"resource": "navigation", "id": self.nav.id, "parent_id": child.id}, format="json")
        self.assertEqual(cycle.status_code, status.HTTP_400_BAD_REQUEST)

    def test_view_only_settings_staff_cannot_change_branding(self):
        from .models import StaffCapabilityProfile
        staff = User.objects.create_user(email="branding-viewer@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=staff, capabilities={"settings": ["view"]})
        self.client.force_authenticate(staff)
        visible = self.client.get(reverse("admin-branding"))
        self.assertEqual(visible.status_code, status.HTTP_200_OK)
        denied = self.client.patch(reverse("admin-branding"), {"branding": {"theme_preset": "forest"}}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)


class NotificationDeliveryPreferenceTests(APITestCase):
    def setUp(self):
        from .models import NotificationPreference
        self.admin = User.objects.create_superuser(email="notification-admin@example.com", password="StrongPass123!")
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role"])
        self.user = User.objects.create_user(email="notification-user@example.com", password="StrongPass123!", is_active=True)
        self.preference = NotificationPreference.objects.create(user=self.user, in_app_enabled=True, email_enabled=False, sms_enabled=False, push_enabled=False, marketing=False)

    def test_user_preferences_are_persisted_and_private(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(reverse("notification-preferences"), {"email_enabled": True, "booking_updates": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.preference.refresh_from_db()
        self.assertTrue(self.preference.email_enabled)
        self.assertFalse(self.preference.booking_updates)

    def test_broadcast_respects_channel_and_category_preferences(self):
        from .models import Notification
        self.client.force_authenticate(self.admin)
        response = self.client.post(reverse("admin-notifications"), {"title": "Platform update", "message": "Test delivery", "role": "tourist", "category": "general", "channels": ["in_app", "email", "sms", "push"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        records = Notification.objects.filter(user=self.user)
        self.assertEqual(records.count(), 4)
        self.assertEqual(records.get(channel="in_app").delivery_status, "sent")
        self.assertEqual(set(records.exclude(channel="in_app").values_list("delivery_status", flat=True)), {"skipped"})

    def test_external_delivery_stays_queued_until_provider_confirms(self):
        from .models import Notification
        self.preference.email_enabled = True; self.preference.save(update_fields=["email_enabled"])
        self.client.force_authenticate(self.admin)
        self.client.post(reverse("admin-notifications"), {"title": "Email test", "message": "Queued", "role": "tourist", "channels": ["email"]}, format="json")
        notification = Notification.objects.get(user=self.user, channel="email")
        self.assertEqual(notification.delivery_status, "queued")
        self.assertFalse(notification.is_sent)

    @patch("tourist.notification_delivery.send_mail")
    def test_provider_confirmation_marks_email_sent(self, mocked_send):
        from .models import Notification
        from .notification_delivery import deliver_notification
        notification = Notification.objects.create(user=self.user, channel="email", title="Confirmed", message="Delivered")
        result = deliver_notification(notification.id)
        self.assertEqual(result, "sent")
        notification.refresh_from_db()
        self.assertTrue(notification.is_sent)
        self.assertEqual(notification.delivery_attempts, 1)
        self.assertIsNotNone(notification.sent_at)
        mocked_send.assert_called_once()

    def test_provider_failure_records_reason_and_bounded_retry(self):
        from .models import Notification
        from .notification_delivery import deliver_notification
        notification = Notification.objects.create(user=self.user, channel="sms", title="SMS", message="Unavailable", max_attempts=2)
        self.assertEqual(deliver_notification(notification.id), "failed")
        notification.refresh_from_db()
        self.assertIn("phone", notification.failure_reason.lower())
        self.assertIsNotNone(notification.next_retry_at)
        self.assertEqual(deliver_notification(notification.id), "failed")
        notification.refresh_from_db()
        self.assertIsNone(notification.next_retry_at)
        self.assertEqual(notification.delivery_attempts, 2)

    def test_retry_action_does_not_reset_exhausted_deliveries(self):
        from .models import Notification
        failed = Notification.objects.create(user=self.user, channel="email", title="Retry", message="Retry", delivery_status="failed", delivery_attempts=1, max_attempts=3)
        exhausted = Notification.objects.create(user=self.user, channel="email", title="Done", message="Done", delivery_status="failed", delivery_attempts=3, max_attempts=3)
        self.client.force_authenticate(self.admin)
        response = self.client.patch(reverse("admin-notifications"), {"ids": [failed.id, exhausted.id], "action": "retry"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        failed.refresh_from_db(); exhausted.refresh_from_db()
        self.assertEqual(failed.delivery_status, "queued")
        self.assertEqual(exhausted.delivery_status, "failed")

    def test_user_read_unread_and_delete_are_owner_scoped(self):
        from .models import Notification
        own = Notification.objects.create(user=self.user, title="Own", message="Message")
        other = Notification.objects.create(user=self.admin, title="Other", message="Message")
        self.client.force_authenticate(self.user)
        read = self.client.put(reverse("notification-mark-read", kwargs={"pk": own.id}))
        self.assertEqual(read.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(read.data["read_at"])
        unread = self.client.put(reverse("notification-mark-unread", kwargs={"pk": own.id}))
        self.assertFalse(unread.data["is_read"])
        denied = self.client.delete(reverse("notification-detail", kwargs={"pk": other.id}))
        self.assertEqual(denied.status_code, status.HTTP_404_NOT_FOUND)
        removed = self.client.delete(reverse("notification-detail", kwargs={"pk": own.id}))
        self.assertEqual(removed.status_code, status.HTTP_204_NO_CONTENT)

    @patch("tourist.notification_delivery.send_mail")
    def test_queue_management_command_processes_due_delivery(self, mocked_send):
        from django.core.management import call_command
        from .models import Notification
        notification = Notification.objects.create(user=self.user, channel="email", title="Worker", message="Process me")
        call_command("process_notification_queue", limit=10)
        notification.refresh_from_db()
        self.assertEqual(notification.delivery_status, "sent")
        mocked_send.assert_called_once()

    def test_disabled_marketing_category_is_skipped_even_for_in_app(self):
        from .models import Notification
        self.client.force_authenticate(self.admin)
        response = self.client.post(reverse("admin-notifications"), {"title": "Offer", "message": "Marketing", "role": "tourist", "category": "marketing", "channels": ["in_app"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification = Notification.objects.get(user=self.user, title="Offer")
        self.assertEqual(notification.delivery_status, "skipped")
        self.assertIn("preferences", notification.failure_reason)


class TravelServicesManagementTests(APITestCase):
    def setUp(self):
        from .models import Restaurant, DestinationTransitRoute
        self.admin = User.objects.create_superuser(email="travel-service-admin@example.com", password="StrongPass123!")
        self.admin.role = User.Role.SUPER_ADMIN; self.admin.save(update_fields=["role"])
        self.user = User.objects.create_user(email="planner@example.com", password="StrongPass123!")
        self.other = User.objects.create_user(email="other-planner@example.com", password="StrongPass123!")
        category = Category.objects.create(name="Travel Services Test")
        self.destination = Destination.objects.create(name="Service Destination", category=category, description="Test", district="Kaski", status="approved", is_active=True, latitude=28, longitude=84, created_by=self.admin)
        self.restaurant = Restaurant.objects.create(destination=self.destination, name="Pending Kitchen", status="pending")
        self.route = DestinationTransitRoute.objects.create(destination=self.destination, origin="Kathmandu", transport_mode="Bus", approx_duration="5 hours")

    def test_pending_restaurant_is_hidden_until_admin_publishes(self):
        public = self.client.get(reverse("restaurant-list"), {"destination": self.destination.id})
        self.assertEqual(public.data["count"], 0)
        self.client.force_authenticate(self.admin)
        published = self.client.patch(reverse("admin-travel-services"), {"resource": "restaurants", "id": self.restaurant.id, "action": "publish"}, format="json")
        self.assertEqual(published.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(reverse("restaurant-list"), {"destination": self.destination.id}).data["count"], 1)

    def test_restaurant_source_verification_is_explicit_and_audited(self):
        from audit.models import AuditLog
        self.client.force_authenticate(self.admin)
        response = self.client.patch(reverse("admin-travel-services"), {"resource": "restaurants", "id": self.restaurant.id, "action": "verify"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.restaurant.refresh_from_db(); self.assertTrue(self.restaurant.is_verified)
        self.assertTrue(AuditLog.objects.filter(action="restaurants.verify", object_id=str(self.restaurant.id)).exists())

    def test_transport_archive_hides_route_without_deleting(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(reverse("admin-travel-services"), {"resource": "transportation", "id": self.route.id, "action": "archive"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.route.refresh_from_db(); self.assertFalse(self.route.is_active)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(reverse("transit-route-list"), {"destination": self.destination.id}).data["count"], 0)

    def test_staff_requires_exact_restaurant_write_capability(self):
        from .models import StaffCapabilityProfile
        staff = User.objects.create_user(email="restaurant-viewer@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=staff, capabilities={"restaurants": ["view"]})
        self.client.force_authenticate(staff)
        denied = self.client.post(reverse("restaurant-list"), {"destination": self.destination.id, "name": "Denied Restaurant"}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

    def test_travel_plans_are_private_to_owner(self):
        self.client.force_authenticate(self.user)
        created = self.client.post(reverse("travel-plan-list"), {"title": "My Nepal plan", "travelers": 2, "generation_source": "ml", "itinerary_data": {"days": []}}, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.other)
        response = self.client.get(reverse("travel-plan-list"))
        self.assertEqual(response.data["count"], 0)
        denied = self.client.get(reverse("travel-plan-detail", kwargs={"pk": created.data["id"]}))
        self.assertEqual(denied.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_delete_archives_plan(self):
        from .models import TravelPlan
        plan = TravelPlan.objects.create(user=self.user, title="Withdraw plan")
        self.client.force_authenticate(self.user)
        response = self.client.delete(reverse("travel-plan-detail", kwargs={"pk": plan.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        plan.refresh_from_db(); self.assertEqual(plan.status, "archived")

    def test_invalid_plan_date_range_is_rejected(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("travel-plan-list"), {"title": "Bad dates", "start_date": "2026-10-10", "end_date": "2026-10-01"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_plan_stop_cannot_be_added_to_another_users_plan(self):
        from .models import TravelPlan
        plan = TravelPlan.objects.create(user=self.other, title="Other plan")
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("travel-plan-stop-list"), {"plan": plan.id, "destination": self.destination.id, "day_number": 1, "display_order": 0}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restaurant_staff_workspace_is_capability_and_district_scoped(self):
        from .models import StaffCapabilityProfile
        staff = User.objects.create_user(email="restaurant-manager@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=staff, capabilities={"restaurants": ["view", "approve"]}, managed_districts=["Kaski"])
        self.client.force_authenticate(staff)
        queue = self.client.get(reverse("staff-workspace"), {"module": "restaurants"})
        self.assertEqual(queue.status_code, status.HTTP_200_OK)
        self.assertEqual(queue.data["results"][0]["id"], self.restaurant.id)
        published = self.client.post(reverse("staff-workspace"), {"module": "restaurants", "id": self.restaurant.id, "action": "publish"}, format="json")
        self.assertEqual(published.status_code, status.HTTP_200_OK)
        self.restaurant.refresh_from_db(); self.assertEqual(self.restaurant.status, "published")

    def test_travel_plan_view_capability_does_not_grant_edit(self):
        from .models import StaffCapabilityProfile, TravelPlan
        plan = TravelPlan.objects.create(user=self.user, title="Protected plan")
        staff = User.objects.create_user(email="plan-viewer@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=staff, capabilities={"travel_plans": ["view"]})
        self.client.force_authenticate(staff)
        visible = self.client.get(reverse("travel-plan-detail", kwargs={"pk": plan.id}))
        self.assertEqual(visible.status_code, status.HTTP_200_OK)
        denied = self.client.patch(reverse("travel-plan-detail", kwargs={"pk": plan.id}), {"title": "Changed"}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)


class RetentionAndAnonymizationTests(APITestCase):
    def setUp(self):
        from datetime import date, timedelta
        from booking.models import Booking
        self.admin = User.objects.create_superuser(email="retention-admin@example.com", password="StrongPass123!")
        self.admin.role = User.Role.SUPER_ADMIN; self.admin.save(update_fields=["role"])
        self.user = User.objects.create_user(email="retention-user@example.com", password="StrongPass123!", first_name="Private", last_name="Person", city="Kathmandu", bio="Personal biography")
        category = Category.objects.create(name="Retention Test")
        self.destination = Destination.objects.create(name="Retained Destination", category=category, description="Protected", status="approved", is_active=True, latitude=28, longitude=84, created_by=self.admin)
        self.hotel = Hotel.objects.create(destination=self.destination, name="Retained Hotel", price_per_night=25)
        self.booking = Booking.objects.create(user=self.user, hotel=self.hotel, check_in=date.today()+timedelta(days=2), check_out=date.today()+timedelta(days=4))

    def test_destination_delete_archives_and_preserves_related_booking(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(reverse("destination-detail", kwargs={"slug": self.destination.slug}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.destination.refresh_from_db(); self.assertEqual(self.destination.status, "archived"); self.assertFalse(self.destination.is_active)
        self.assertTrue(type(self.booking).objects.filter(pk=self.booking.id).exists())

    def test_hotel_delete_archives_and_preserves_booking(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(reverse("hotel-detail", kwargs={"pk": self.hotel.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.hotel.refresh_from_db(); self.assertFalse(self.hotel.is_active); self.assertIsNotNone(self.hotel.archived_at)
        self.assertTrue(type(self.booking).objects.filter(pk=self.booking.id).exists())

    def test_booking_delete_cancels_and_completed_booking_is_protected(self):
        from booking.models import Booking
        self.client.force_authenticate(self.user)
        cancelled = self.client.delete(reverse("booking-detail", kwargs={"pk": self.booking.id}))
        self.assertEqual(cancelled.status_code, status.HTTP_204_NO_CONTENT)
        self.booking.refresh_from_db(); self.assertEqual(self.booking.status, "cancelled")
        self.booking.status = Booking.Status.COMPLETED; self.booking.save(update_fields=["status"])
        protected = self.client.delete(reverse("booking-detail", kwargs={"pk": self.booking.id}))
        self.assertEqual(protected.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Booking.objects.filter(pk=self.booking.id).exists())

    def test_official_risk_delete_archives_instead_of_destroying(self):
        from datetime import date
        from .models import RiskIncident
        incident = RiskIncident.objects.create(destination=self.destination, hazard_type="landslide", event_date=date.today(), title="Official history", source_type="official", source_name="Authority", verified=True)
        self.client.force_authenticate(self.admin)
        response = self.client.delete(reverse("admin-risk-incidents-detail", kwargs={"pk": incident.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        incident.refresh_from_db(); self.assertTrue(incident.is_archived); self.assertIsNotNone(incident.archived_at)

    def test_user_anonymization_is_irreversible_and_preserves_booking(self):
        from .models import UserFeedback
        feedback = UserFeedback.objects.create(user=self.user, name="Private Person", email=self.user.email, subject="Help", message="Message")
        old_email = self.user.email
        self.client.force_authenticate(self.admin)
        response = self.client.post(reverse("admin-user-access-action", kwargs={"id": self.user.id}), {"action":"anonymize","confirmation":old_email}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db(); feedback.refresh_from_db()
        self.assertTrue(self.user.email.endswith("@deleted.invalid")); self.assertFalse(self.user.is_active); self.assertIsNotNone(self.user.anonymized_at)
        self.assertEqual(self.user.city, ""); self.assertEqual(feedback.email, ""); self.assertTrue(type(self.booking).objects.filter(pk=self.booking.id,user=self.user).exists())
        self.assertFalse(self.user.has_usable_password())

    def test_anonymization_requires_exact_email_confirmation(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(reverse("admin-user-access-action", kwargs={"id": self.user.id}), {"action":"anonymize","confirmation":"wrong@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db(); self.assertIsNone(self.user.anonymized_at)

    def test_retention_dry_run_and_apply_remove_only_expired_ephemeral_data(self):
        from datetime import timedelta
        from django.utils import timezone
        from .models import Notification, LocationPing, SharedTrip, RecommendationEvent
        trip = SharedTrip.objects.create(user=self.user, expires_at=timezone.now()+timedelta(days=1))
        ping = LocationPing.objects.create(trip=trip, latitude=28, longitude=84)
        notification = Notification.objects.create(user=self.user, title="Old read", message="Old", is_read=True)
        event = RecommendationEvent.objects.create(user=self.user, event_type="view", consented=True)
        old = timezone.now()-timedelta(days=400)
        Notification.objects.filter(pk=notification.pk).update(created_at=old)
        LocationPing.objects.filter(pk=ping.pk).update(recorded_at=old)
        RecommendationEvent.objects.filter(pk=event.pk).update(created_at=old)
        self.client.force_authenticate(self.admin)
        preview = self.client.post(reverse("admin-retention"), {"dry_run":True}, format="json")
        self.assertGreaterEqual(preview.data["total"], 3)
        self.assertTrue(Notification.objects.filter(pk=notification.pk).exists())
        applied = self.client.post(reverse("admin-retention"), {"dry_run":False}, format="json")
        self.assertEqual(applied.status_code, status.HTTP_200_OK)
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())
        self.assertFalse(LocationPing.objects.filter(pk=ping.pk).exists())
        self.assertFalse(RecommendationEvent.objects.filter(pk=event.pk).exists())
        self.assertTrue(type(self.booking).objects.filter(pk=self.booking.pk).exists())

    def test_view_only_settings_staff_can_preview_but_not_apply_retention(self):
        from .models import StaffCapabilityProfile
        staff = User.objects.create_user(email="retention-viewer@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=staff, capabilities={"settings":["view"]})
        self.client.force_authenticate(staff)
        self.assertEqual(self.client.post(reverse("admin-retention"), {"dry_run":True}, format="json").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(reverse("admin-retention"), {"dry_run":False}, format="json").status_code, status.HTTP_403_FORBIDDEN)


class HotelImageDeliveryTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="hotel-image-admin@example.com", password="StrongPass123!")
        category = Category.objects.create(name="Hotel Image Test")
        self.destination = Destination.objects.create(name="Bandipur", category=category, description="Test", status="approved", is_active=True, latitude=28, longitude=84, created_by=self.admin)
        self.hotel = Hotel.objects.create(destination=self.destination, name="Image Test Hotel", price_per_night=30)

    def test_verified_destination_media_is_labelled_context_fallback(self):
        from .models import DestinationImage
        image = DestinationImage.objects.create(destination=self.destination, external_url="https://example.com/bandipur.jpg", verification_status="approved", is_cover=False)
        response = self.client.get(reverse("hotel-detail", kwargs={"pk": self.hotel.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["image_url"], image.external_url)
        self.assertEqual(response.data["destination_context_image_url"], image.external_url)
        self.assertFalse(response.data["image_is_hotel_specific"])
        self.assertEqual(response.data["image_source"], "destination_context")

    def test_hotel_specific_image_has_priority(self):
        from .models import DestinationImage
        DestinationImage.objects.create(destination=self.destination, external_url="https://example.com/area.jpg", verification_status="approved", is_cover=True)
        self.hotel.external_image_url = "https://example.com/hotel.jpg"; self.hotel.save(update_fields=["external_image_url"])
        response = self.client.get(reverse("hotel-detail", kwargs={"pk": self.hotel.id}))
        self.assertEqual(response.data["image_url"], "https://example.com/hotel.jpg")
        self.assertTrue(response.data["image_is_hotel_specific"])
        self.assertEqual(response.data["image_source"], "hotel_external")

    def test_missing_media_is_explicitly_unavailable(self):
        response = self.client.get(reverse("hotel-detail", kwargs={"pk": self.hotel.id}))
        self.assertIsNone(response.data["image_url"])
        self.assertEqual(response.data["image_source"], "unavailable")

    def test_hotel_search_excludes_archived_and_returns_context_image(self):
        from .models import DestinationImage
        DestinationImage.objects.create(destination=self.destination, external_url="https://example.com/context.jpg", verification_status="approved", is_cover=True)
        archived = Hotel.objects.create(destination=self.destination, name="Archived Image Hotel", is_active=False)
        response = self.client.get(reverse("hotel-search"), {"query":"Hotel"})
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(self.hotel.id, ids); self.assertNotIn(archived.id, ids)
        row = next(row for row in response.data["results"] if row["id"] == self.hotel.id)
        self.assertEqual(row["image_url"], "https://example.com/context.jpg")

    def test_admin_can_assign_valid_hotel_specific_image_url(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(reverse("hotel-detail", kwargs={"pk": self.hotel.id}), {"external_image_url":"https://example.com/specific.webp"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["image_url"], "https://example.com/specific.webp")
        self.assertTrue(response.data["image_is_hotel_specific"])
        insecure = self.client.patch(reverse("hotel-detail", kwargs={"pk": self.hotel.id}), {"external_image_url":"http://example.com/insecure.jpg"}, format="json")
        self.assertEqual(insecure.status_code, status.HTTP_400_BAD_REQUEST)


class AdminNavigationCMSAndMediaRegressionTests(APITestCase):
    def setUp(self):
        self.admin=User.objects.create_superuser(email="navigation-media-admin@example.com",password="StrongPass123!")
        self.admin.role=User.Role.SUPER_ADMIN;self.admin.save(update_fields=["role"])
        category=Category.objects.create(name="Admin Media Regression")
        self.destination=Destination.objects.create(name="Media Ordering Place",category=category,description="Test",status="approved",is_active=True,latitude=28,longitude=84,created_by=self.admin)
        self.client.force_authenticate(self.admin)

    def test_seeded_cms_catalog_exposes_all_editable_pages_sections_and_navigation(self):
        from .models import ManagedPage,ContentSection,ManagedNavigationItem
        self.assertGreaterEqual(ManagedPage.objects.count(),25)
        self.assertGreaterEqual(ContentSection.objects.count(),25)
        self.assertGreaterEqual(ManagedNavigationItem.objects.count(),25)
        pages=self.client.get(reverse("admin-cms"),{"resource":"pages"})
        sections=self.client.get(reverse("admin-cms"),{"resource":"sections"})
        navigation=self.client.get(reverse("admin-cms"),{"resource":"navigation"})
        self.assertGreaterEqual(len(pages.data["results"]),25)
        self.assertGreaterEqual(len(sections.data["results"]),25)
        self.assertGreaterEqual(len(navigation.data["results"]),25)

    def test_external_media_upload_enters_pending_queue(self):
        response=self.client.post(reverse("admin-media-library"),{"destination_id":self.destination.id,"external_url":"https://example.com/place.webp","caption":"External place","source_url":"https://example.com/source"},format="multipart")
        self.assertEqual(response.status_code,status.HTTP_201_CREATED)
        from .models import DestinationImage
        image=DestinationImage.objects.get(pk=response.data["id"])
        self.assertEqual(image.verification_status,"pending");self.assertFalse(image.is_verified)

    def test_computer_media_upload_validates_real_image(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        output=io.BytesIO();Image.new("RGB",(80,60),"green").save(output,format="JPEG")
        upload=SimpleUploadedFile("place.jpg",output.getvalue(),content_type="image/jpeg")
        response=self.client.post(reverse("admin-media-library"),{"destination_id":self.destination.id,"file":upload,"caption":"Local upload"},format="multipart")
        self.assertEqual(response.status_code,status.HTTP_201_CREATED)
        bad=SimpleUploadedFile("bad.jpg",b"not-an-image",content_type="image/jpeg")
        rejected=self.client.post(reverse("admin-media-library"),{"destination_id":self.destination.id,"file":bad},format="multipart")
        self.assertEqual(rejected.status_code,status.HTTP_400_BAD_REQUEST)

    def test_move_up_normalizes_and_swaps_gallery_order(self):
        from .models import DestinationImage
        first=DestinationImage.objects.create(destination=self.destination,external_url="https://example.com/1.jpg",ordering=0)
        second=DestinationImage.objects.create(destination=self.destination,external_url="https://example.com/2.jpg",ordering=0)
        third=DestinationImage.objects.create(destination=self.destination,external_url="https://example.com/3.jpg",ordering=0)
        response=self.client.patch(reverse("admin-media-library"),{"id":third.id,"action":"move_up"},format="json")
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        ordered=list(DestinationImage.objects.filter(destination=self.destination).order_by("ordering","id").values_list("id",flat=True))
        self.assertEqual(ordered,[first.id,third.id,second.id])

    def test_staff_without_image_add_capability_cannot_upload(self):
        from .models import StaffCapabilityProfile
        staff=User.objects.create_user(email="media-viewer@example.com",password="StrongPass123!",role="staff",is_staff=True)
        StaffCapabilityProfile.objects.create(user=staff,capabilities={"images":["view"]})
        self.client.force_authenticate(staff)
        response=self.client.post(reverse("admin-media-library"),{"destination_id":self.destination.id,"external_url":"https://example.com/denied.jpg"},format="multipart")
        self.assertEqual(response.status_code,status.HTTP_403_FORBIDDEN)


class CMSStudioExtensionTests(APITestCase):
    def setUp(self):
        from .models import ManagedPage, ContentSection, DestinationImage
        self.admin = User.objects.create_superuser(email="cms-studio@example.com", password="StrongPass123!")
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role"])
        self.client.force_authenticate(self.admin)
        self.category = Category.objects.create(name="CMS Studio")
        self.destination = Destination.objects.create(
            name="Studio Place", category=self.category, description="Test",
            status="approved", is_active=True, latitude=28, longitude=84, created_by=self.admin,
        )

    def test_page_template_creates_sections(self):
        from .models import ContentSection
        created = self.client.post(reverse("admin-cms"), {
            "resource": "pages", "route": "/guide-page", "key": "guide-page",
            "title": "Guide", "status": "draft", "template": "travel_guide",
        }, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(ContentSection.objects.filter(page_id=created.data["id"]).count(), 3)

    def test_reusable_section_can_be_cloned(self):
        from .models import ManagedPage, ContentSection
        page = ManagedPage.objects.create(route="/reusable-src", key="reusable-src", title="Source", status="draft")
        target = ManagedPage.objects.create(route="/reusable-dst", key="reusable-dst", title="Target", status="draft")
        source = ContentSection.objects.create(page=page, key="tips", title="Travel Tips", body="Pack light", is_reusable=True, status="published")
        cloned = self.client.patch(reverse("admin-cms"), {
            "resource": "pages", "id": target.id, "action": "clone_reusable", "source_id": source.id, "page_id": target.id,
        }, format="json")
        self.assertEqual(cloned.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ContentSection.objects.filter(page=target, title="Travel Tips").exists())

    def test_global_search_includes_pages_and_images(self):
        from .models import ManagedPage, DestinationImage
        ManagedPage.objects.create(route="/searchable-page", key="searchable-page", title="UniqueSearchPage", status="published")
        DestinationImage.objects.create(destination=self.destination, external_url="https://example.com/unique-search-photo.jpg", caption="UniqueSearchPhoto")
        response = self.client.get(reverse("admin-global-search"), {"q": "UniqueSearch"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        types = {item["type"] for item in response.data["results"]}
        self.assertIn("page", types)
        self.assertIn("image", types)
        filtered = self.client.get(reverse("admin-global-search"), {"q": "UniqueSearch", "type": "page"})
        self.assertTrue(all(item["type"] == "page" for item in filtered.data["results"]))
        self.assertTrue(any("snippet" in item for item in filtered.data["results"]))

    def test_media_library_reports_used_on_and_crop(self):
        from .models import DestinationImage
        image = DestinationImage.objects.create(
            destination=self.destination, external_url="https://example.com/used-on.jpg",
            caption="Used photo", verification_status="approved",
        )
        listed = self.client.get(reverse("admin-media-library"), {"q": "used-on"})
        row = next(item for item in listed.data["results"] if item["id"] == image.id)
        self.assertTrue(row["used_on"])
        cropped = self.client.patch(reverse("admin-media-library"), {"id": image.id, "crop_box": {"x": 10, "y": 10, "w": 80, "h": 80}}, format="json")
        self.assertEqual(cropped.status_code, status.HTTP_200_OK)
        image.refresh_from_db()
        self.assertEqual(image.crop_box["w"], 80)

    def test_crop_rewrites_jpeg_file(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import DestinationImage
        output = io.BytesIO()
        Image.new("RGB", (100, 80), "blue").save(output, format="JPEG")
        upload = SimpleUploadedFile("place.jpg", output.getvalue(), content_type="image/jpeg")
        image = DestinationImage.objects.create(destination=self.destination, image=upload, caption="Crop me")
        cropped = self.client.patch(
            reverse("admin-media-library"),
            {"id": image.id, "crop_box": {"x": 10, "y": 10, "w": 50, "h": 50}},
            format="json",
        )
        self.assertEqual(cropped.status_code, status.HTTP_200_OK)
        image.refresh_from_db()
        image.image.open()
        rewritten = Image.open(image.image)
        self.assertEqual(rewritten.format, "JPEG")
        self.assertLess(rewritten.size[0], 100)
        self.assertLess(rewritten.size[1], 80)

    def test_templates_and_reusable_catalogs(self):
        from .models import ManagedPage, ContentSection
        page = ManagedPage.objects.create(route="/reusable-list", key="reusable-list", title="Reusable list", status="draft")
        ContentSection.objects.create(page=page, key="pack", title="Packing list", body="Warm layers", is_reusable=True, status="published")
        templates = self.client.get(reverse("admin-cms"), {"templates": "1"})
        self.assertEqual(templates.status_code, status.HTTP_200_OK)
        self.assertIn("travel_guide", templates.data["templates"])
        reusable = self.client.get(reverse("admin-cms"), {"resource": "sections", "reusable": "true"})
        self.assertEqual(reusable.status_code, status.HTTP_200_OK)
        self.assertTrue(any(row["title"] == "Packing list" for row in reusable.data["results"]))

    def test_apply_template_and_reorder_sections(self):
        from .models import ManagedPage, ContentSection
        page = ManagedPage.objects.create(route="/builder-page", key="builder-page", title="Builder", status="draft")
        applied = self.client.patch(reverse("admin-cms"), {
            "resource": "pages", "id": page.id, "action": "apply_template", "template": "information",
        }, format="json")
        self.assertEqual(applied.status_code, status.HTTP_200_OK)
        sections = list(ContentSection.objects.filter(page=page).order_by("display_order", "id"))
        self.assertGreaterEqual(len(sections), 3)
        reversed_ids = [section.id for section in reversed(sections)]
        reordered = self.client.patch(reverse("admin-cms"), {
            "resource": "pages", "id": page.id, "action": "reorder", "section_ids": reversed_ids,
        }, format="json")
        self.assertEqual(reordered.status_code, status.HTTP_200_OK)
        ordered = list(ContentSection.objects.filter(page=page).order_by("display_order", "id").values_list("id", flat=True))
        self.assertEqual(list(ordered), reversed_ids)

    def test_all_page_sections_are_listed_for_builder(self):
        from .models import ManagedPage, ContentSection
        page = ManagedPage.objects.create(route="/dashboard-builder", key="dashboard-builder", title="Dashboard builder", status="published")
        for index, key in enumerate(["hero", "alerts", "hotels", "safety"]):
            ContentSection.objects.create(page=page, key=key, title=key, display_order=index * 10, status="published")
        listed = self.client.get(reverse("admin-cms"), {"resource": "sections", "page_id": page.id})
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual({row["key"] for row in listed.data["results"]}, {"hero", "alerts", "hotels", "safety"})
        self.assertTrue(all(row.get("page_title") == "Dashboard builder" for row in listed.data["results"]))

    def test_staff_can_publish_content_section(self):
        from .models import StaffCapabilityProfile, ManagedPage, ContentSection
        page = ManagedPage.objects.create(route="/staff-cms", key="staff-cms", title="Staff CMS", status="draft")
        section = ContentSection.objects.create(page=page, key="hero", title="Draft hero", status="draft")
        staff = User.objects.create_user(email="content-staff@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=staff, capabilities={"content": ["view", "approve", "change"]})
        self.client.force_authenticate(staff)
        listed = self.client.get(reverse("staff-workspace"), {"module": "content"})
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertTrue(any(row["id"] == section.id for row in listed.data["results"]))
        published = self.client.post(reverse("staff-workspace"), {"module": "content", "id": section.id, "action": "publish"}, format="json")
        self.assertEqual(published.status_code, status.HTTP_200_OK)
        section.refresh_from_db()
        self.assertEqual(section.status, "published")

    def test_import_layout_json_creates_draft_sections(self):
        from .models import ManagedPage, ContentSection
        page = ManagedPage.objects.create(route="/layout-import", key="layout-import", title="Layout import", status="draft")
        imported = self.client.patch(reverse("admin-cms"), {
            "resource": "pages", "id": page.id, "action": "import_layout",
            "layout": [
                {"key": "hero", "section_type": "heading", "title": "Imported hero", "body": "Hello"},
                {"key": "video", "section_type": "video", "title": "Clip", "config": {"media_url": "https://example.com/clip.mp4", "media_kind": "video"}},
            ],
        }, format="json")
        self.assertEqual(imported.status_code, status.HTTP_200_OK)
        self.assertEqual(imported.data["created"], 2)
        self.assertTrue(ContentSection.objects.filter(page=page, key="hero", status="draft").exists())
        insecure = self.client.patch(reverse("admin-cms"), {
            "resource": "pages", "id": page.id, "action": "import_layout",
            "source_url": "http://example.com/layout.json",
        }, format="json")
        self.assertEqual(insecure.status_code, status.HTTP_400_BAD_REQUEST)

    def test_community_video_is_capped_at_25mb_and_stays_pending(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import DestinationVideo
        tourist = User.objects.create_user(email="clip@example.com", password="StrongPass123!", is_verified=True)
        self.client.force_authenticate(tourist)
        too_big = SimpleUploadedFile("huge.mp4", b"0" * (25 * 1024 * 1024 + 1), content_type="video/mp4")
        denied = self.client.post(reverse("destination-videos", kwargs={"slug": self.destination.slug}), {"video_file": too_big, "title": "Too big"}, format="multipart")
        self.assertEqual(denied.status_code, status.HTTP_400_BAD_REQUEST)
        clip = SimpleUploadedFile("place.mp4", b"fake-video-bytes", content_type="video/mp4")
        created = self.client.post(reverse("destination-videos", kwargs={"slug": self.destination.slug}), {"video_file": clip, "title": "Trail clip"}, format="multipart")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        video = DestinationVideo.objects.get(pk=created.data["id"])
        self.assertEqual(video.verification_status, "pending")
        self.assertEqual(video.uploaded_by, tourist)

    def test_staff_can_approve_pending_community_video(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import DestinationVideo, StaffCapabilityProfile
        tourist = User.objects.create_user(email="clipper@example.com", password="StrongPass123!", is_verified=True)
        video = DestinationVideo.objects.create(
            destination=self.destination, title="Trail clip",
            video_file=SimpleUploadedFile("place.mp4", b"fake-video-bytes", content_type="video/mp4"),
            uploaded_by=tourist, verification_status="pending",
        )
        staff = User.objects.create_user(email="media-staff@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=staff, capabilities={"images": ["view", "approve", "change"]})
        self.client.force_authenticate(staff)
        listed = self.client.get(reverse("staff-workspace"), {"module": "images"})
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertTrue(any(row["id"] == video.id and row.get("type") == "video" for row in listed.data["results"]))
        approved = self.client.post(reverse("staff-workspace"), {
            "module": "images", "id": video.id, "type": "video", "action": "approve",
        }, format="json")
        self.assertEqual(approved.status_code, status.HTTP_200_OK)
        video.refresh_from_db()
        self.assertEqual(video.verification_status, "approved")


class CMSFormAndServiceMediaTests(APITestCase):
    def setUp(self):
        from .models import ManagedPage
        self.admin = User.objects.create_superuser(email="form-media-admin@example.com", password="StrongPass123!")
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role"])
        self.client.force_authenticate(self.admin)
        self.page = ManagedPage.objects.create(route="/form-test", key="form-test", title="Form test", status="draft")

    def test_form_fields_are_sanitised(self):
        from .models import ContentSection
        from .views_admin import AdminCMSView
        safe = AdminCMSView._safe_section_config({
            "fields": [
                {"name": "Email!!", "label": "Email", "field_type": "email", "required": True},
                {"name": "bad", "label": "Hack", "field_type": "javascript", "required": True},
                {"name": "notes", "label": "Notes", "field_type": "textarea"},
            ]
        })
        self.assertEqual([field["name"] for field in safe["fields"]], ["email", "notes"])
        self.assertEqual([field["field_type"] for field in safe["fields"]], ["email", "textarea"])
        created = self.client.post(reverse("admin-cms"), {
            "resource": "sections", "page_id": self.page.id, "key": "contact-form",
            "title": "Contact", "section_type": "form", "status": "draft",
            "config": {"fields": [
                {"name": "visitor_email", "label": "Email", "field_type": "email"},
                {"name": "hack", "label": "Hack", "field_type": "file"},
            ]},
        }, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        section = ContentSection.objects.get(page=self.page, key="contact-form")
        self.assertEqual([field["field_type"] for field in section.config.get("fields", [])], ["email"])

    def test_service_media_requires_file(self):
        from .models import Hospital
        dest = Destination.objects.create(
            name="Photo Place", category=Category.objects.create(name="Service Media"),
            description="Test", latitude=28, longitude=84, created_by=self.admin,
            status="approved", is_active=True,
        )
        hospital = Hospital.objects.create(
            destination=dest, name="Photo Hospital", address="Kaski", phone="061123456",
            latitude=28.4, longitude=84.0, district="Kaski",
        )
        missing = self.client.post(reverse("admin-service-media"), {"kind": "hospital", "id": hospital.id})
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        listed = self.client.get(reverse("admin-service-media"), {"kind": "hospital"})
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertTrue(any(row["id"] == hospital.id for row in listed.data["results"]))


class OwnerDeskTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="owner-desk@example.com", password="StrongPass123!")
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role"])
        self.client.force_authenticate(self.admin)
        self.category = Category.objects.create(name="Owner Desk")
        self.destination = Destination.objects.create(
            name="Desk Lake", category=self.category, description="Pinned lake",
            latitude=28.2, longitude=83.9, city="Pokhara", district="Kaski",
            status="approved", is_active=True, created_by=self.admin, average_rating=3.2,
        )

    def test_notice_requires_title(self):
        response = self.client.post(reverse("admin-visitor-desk"), {"kind": "festival", "body": "Dashain crowds"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unpublished_notice_is_hidden_from_public_config(self):
        from .models import VisitorNotice
        VisitorNotice.objects.create(title="Draft closure", kind="closure", body="Hidden", is_published=False)
        VisitorNotice.objects.create(title="Live festival", kind="festival", body="Dashain in Bhaktapur", is_published=True)
        public = self.client.get(reverse("public-config"))
        self.assertEqual(public.status_code, status.HTTP_200_OK)
        titles = [row["title"] for row in public.data["notices"]]
        self.assertIn("Live festival", titles)
        self.assertNotIn("Draft closure", titles)

    def test_expired_notice_is_hidden_from_public_config(self):
        from datetime import timedelta
        from django.utils import timezone
        from .models import VisitorNotice
        VisitorNotice.objects.create(
            title="Old permit", kind="permit", body="Expired", is_published=True,
            starts_at=timezone.now() - timedelta(days=10),
            ends_at=timezone.now() - timedelta(days=1),
        )
        public = self.client.get(reverse("public-config"))
        self.assertFalse(any(row["title"] == "Old permit" for row in public.data["notices"]))

    def test_feature_toggle_prefers_pinned_places(self):
        other = Destination.objects.create(
            name="High Rated Ridge", category=self.category, description="Rated",
            latitude=28.3, longitude=84.0, status="approved", is_active=True,
            created_by=self.admin, average_rating=4.8,
        )
        featured = self.client.get("/api/v1/destinations/", {"featured": "true"})
        names = [row["name"] for row in featured.data["results"]]
        self.assertIn("High Rated Ridge", names)
        pinned = self.client.post(reverse("admin-visitor-desk"), {
            "action": "feature", "destination_id": self.destination.id, "is_featured": True,
        }, format="json")
        self.assertEqual(pinned.status_code, status.HTTP_200_OK)
        self.destination.refresh_from_db()
        self.assertTrue(self.destination.is_featured)
        featured = self.client.get("/api/v1/destinations/", {"featured": "true"})
        names = [row["name"] for row in featured.data["results"]]
        self.assertEqual(names, ["Desk Lake"])
        self.assertNotIn("High Rated Ridge", names)

    def test_destination_page_shows_place_and_district_notices(self):
        from .models import VisitorNotice
        VisitorNotice.objects.create(
            title="TIMS required", kind="permit", body="Buy a TIMS card first",
            destination=self.destination, is_published=True,
        )
        VisitorNotice.objects.create(
            title="Kaski festival week", kind="festival", body="Local jatra",
            district="Kaski", is_published=True,
        )
        VisitorNotice.objects.create(
            title="Nationwide advisory", kind="info", body="General", is_published=True,
        )
        other = Destination.objects.create(
            name="Other Valley", category=self.category, description="Elsewhere",
            latitude=27.7, longitude=85.3, city="Kathmandu", district="Kathmandu",
            status="approved", is_active=True, created_by=self.admin,
        )
        VisitorNotice.objects.create(
            title="Kathmandu only", kind="closure", body="Road work",
            destination=other, is_published=True,
        )
        page = self.client.get(reverse("destination-detail", kwargs={"slug": self.destination.slug}))
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        titles = [row["title"] for row in page.data["notices"]]
        self.assertIn("TIMS required", titles)
        self.assertIn("Kaski festival week", titles)
        self.assertNotIn("Nationwide advisory", titles)
        self.assertNotIn("Kathmandu only", titles)

    def test_published_notice_notifies_favorite_watchers_once(self):
        from .models import Favorite, Notification
        tourist = User.objects.create_user(email="watcher@example.com", password="StrongPass123!", is_verified=True)
        Favorite.objects.create(user=tourist, destination=self.destination)
        created = self.client.post(reverse("admin-visitor-desk"), {
            "title": "Trail closed after rain", "kind": "closure",
            "body": "Use the lower path", "destination_id": self.destination.id, "is_published": True,
        }, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["notified"], 1)
        self.assertTrue(Notification.objects.filter(user=tourist, title__icontains="Trail closed").exists())
        again = self.client.post(reverse("admin-visitor-desk"), {
            "title": "Trail closed after rain", "kind": "closure",
            "body": "Use the lower path", "destination_id": self.destination.id, "is_published": True,
        }, format="json")
        self.assertEqual(again.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.filter(user=tourist, title__icontains="Trail closed").count(), 2)
        # republish of the same notice id should not duplicate
        notice_id = created.data["id"]
        self.client.patch(reverse("admin-visitor-desk"), {"id": notice_id, "is_published": False}, format="json")
        republished = self.client.patch(reverse("admin-visitor-desk"), {"id": notice_id, "is_published": True}, format="json")
        self.assertEqual(republished.data["notified"], 0)


class MarketplaceTests(APITestCase):
    def setUp(self):
        from .models import MarketplaceListing, MarketplacePartner
        self.admin = User.objects.create_superuser(email="market-admin@example.com", password="StrongPass123!")
        self.admin.role = User.Role.SUPER_ADMIN
        self.admin.save(update_fields=["role"])
        self.category = Category.objects.create(name="Marketplace")
        self.destination = Destination.objects.create(
            name="Phewa Shore", category=self.category, description="Lakeside",
            latitude=28.2, longitude=83.9, city="Pokhara", district="Kaski",
            status="approved", is_active=True, created_by=self.admin,
        )
        self.partner = MarketplacePartner.objects.create(
            name="Pokhara Lodge Co", kind="hotel", email="lodge@example.com",
            status="approved", website="https://lodge.example.com",
        )
        self.listing = MarketplaceListing.objects.create(
            partner=self.partner, destination=self.destination, title="Phewa Lake Weekend",
            kind="package", summary="Two nights by the lake", description="Boat and stay",
            includes="Breakfast", excludes="Flights", price_npr="15000.00",
            status="published", city="Pokhara",
        )
        self.draft = MarketplaceListing.objects.create(
            partner=self.partner, title="Hidden draft stay", price_npr="1.00", status="draft",
        )

    def test_unpublished_listing_is_hidden(self):
        listed = self.client.get(reverse("marketplace-listings"))
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        slugs = [row["slug"] for row in listed.data["results"]]
        self.assertIn(self.listing.slug, slugs)
        self.assertNotIn(self.draft.slug, slugs)
        missing = self.client.get(reverse("marketplace-listing-detail", kwargs={"slug": self.draft.slug}))
        self.assertEqual(missing.status_code, status.HTTP_404_NOT_FOUND)

    def test_card_number_is_rejected_and_no_order_created(self):
        from .models import MarketplaceOrder
        response = self.client.post(reverse("marketplace-checkout"), {
            "guest_name": "Ada Traveller", "guest_email": "ada@example.com",
            "card_number": "4111111111111111",
            "items": [{"listing_id": self.listing.id}],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(MarketplaceOrder.objects.exists())

    def test_partner_apply_requires_https_website(self):
        bad = self.client.post(reverse("marketplace-partner-apply"), {
            "name": "Insecure Lodge", "email": "bad@example.com", "website": "http://insecure.example.com",
        }, format="json")
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)
        ok = self.client.post(reverse("marketplace-partner-apply"), {
            "name": "Himalayan Guides", "email": "guides@example.com", "kind": "operator",
            "website": "https://guides.example.com",
        }, format="json")
        self.assertEqual(ok.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ok.data["status"], "pending")

    def test_admin_approve_publish_and_request_checkout(self):
        from .models import MarketplaceListing, MarketplaceOrder
        applied = self.client.post(reverse("marketplace-partner-apply"), {
            "name": "Annapurna Hotel", "email": "annapurna@example.com", "kind": "hotel",
        }, format="json")
        self.assertEqual(applied.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.admin)
        approved = self.client.patch(reverse("admin-marketplace"), {
            "resource": "partners", "id": applied.data["id"], "action": "approve",
        }, format="json")
        self.assertEqual(approved.status_code, status.HTTP_200_OK)
        created = self.client.post(reverse("admin-marketplace"), {
            "resource": "listings", "partner_id": applied.data["id"], "destination_id": self.destination.id,
            "title": "ABC Lodge Night", "kind": "hotel", "price_npr": "8000", "status": "published",
            "summary": "Room with mountain view",
        }, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        listing = MarketplaceListing.objects.get(pk=created.data["id"])
        self.client.force_authenticate(None)
        public = self.client.get(reverse("marketplace-listing-detail", kwargs={"slug": listing.slug}))
        self.assertEqual(public.status_code, status.HTTP_200_OK)
        checkout = self.client.post(reverse("marketplace-checkout"), {
            "guest_name": "Sita", "guest_email": "sita@example.com", "payment_method": "request",
            "travelers": 2, "items": [{"listing_id": listing.id, "quantity": 1}],
        }, format="json")
        self.assertEqual(checkout.status_code, status.HTTP_201_CREATED)
        order = MarketplaceOrder.objects.get(reference=checkout.data["order"]["reference"])
        self.assertEqual(order.status, "requested")
        self.assertEqual(str(order.total_npr), "8000.00")
        self.assertFalse(hasattr(order, "card_number"))

    def test_destination_detail_includes_published_listings(self):
        page = self.client.get(reverse("destination-detail", kwargs={"slug": self.destination.slug}))
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        titles = [row["title"] for row in page.data["marketplace_listings"]]
        self.assertIn("Phewa Lake Weekend", titles)
        self.assertNotIn("Hidden draft stay", titles)

    def test_staff_needs_marketplace_capability(self):
        from .models import StaffCapabilityProfile
        staff = User.objects.create_user(email="market-staff@example.com", password="StrongPass123!", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=staff, capabilities={"hotels": ["view"]})
        self.client.force_authenticate(staff)
        denied = self.client.get(reverse("admin-marketplace"))
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        staff.capability_profile.capabilities = {"marketplace": ["view"]}
        staff.capability_profile.save()
        allowed = self.client.get(reverse("admin-marketplace"))
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)

    def test_admin_search_finds_listings(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("admin-global-search"), {"q": "Phewa Lake"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item["type"] == "listing" for item in response.data["results"]))
