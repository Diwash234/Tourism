from unittest.mock import patch

from django.test import override_settings
import requests
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User, Category, Destination, EmailVerificationToken


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
    def test_best_route_returns_503_when_ml_service_down(self, _mock):
        response = self.client.post(reverse("ml-best-route"), {
            "start_latitude": 28.21, "start_longitude": 83.96,
            "end_latitude": 28.23, "end_longitude": 83.99,
        })
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

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
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)  # ML service not running in tests

    def test_navigation_route_compat_missing_fields(self):
        response = self.client.post("/api/v1/navigation/route", {"startLat": 28.15})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("tourist.utils.requests.post", side_effect=requests.RequestException("down"))
    def test_navigation_route_resolves_destination_name(self, _mock):
        response = self.client.post("/api/v1/navigation/route", {
            "start_latitude": 28.10, "start_longitude": 84.00, "destination_name": "Rupa",
        })
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)  # ML service not running
        # (resolves the name fine -> only fails at the routing call itself, not a 400/404)

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
