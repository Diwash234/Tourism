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
    def test_recommendations_falls_back_when_ml_service_unreachable(self):
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

    def test_safety_prediction_returns_503_when_ml_service_down(self):
        response = self.client.post(reverse("ml-safety"), {"latitude": 28.21, "longitude": 83.96})
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_safety_prediction_requires_coords_or_destination(self):
        response = self.client.post(reverse("ml-safety"), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_budget_prediction_returns_503_when_ml_service_down(self):
        response = self.client.post(reverse("ml-budget"), {"city": "Pokhara", "days": 3, "travelers": 2})
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_best_route_returns_503_when_ml_service_down(self):
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
        from .models import Category, Destination

        self.admin = User.objects.create_superuser(email="admin7@example.com", password="AdminPass123!")
        self.tourist = User.objects.create_user(email="localphotographer@example.com", password="StrongPass123!", is_verified=True)
        self.category = Category.objects.create(name="Waterfalls")
        self.destination = Destination.objects.create(
            name="Devi's Fall", category=self.category,
            description="A dramatic waterfall.", latitude=28.1900, longitude=83.9500,
            created_by=self.admin,
        )

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

    def test_navigation_route_compat_accepts_camelcase_fields(self):
        response = self.client.post("/api/v1/navigation/route", {
            "startLat": 28.15, "startLng": 84.05, "endLat": 28.17, "endLng": 84.07,
        })
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)  # ML service not running in tests

    def test_navigation_route_compat_missing_fields(self):
        response = self.client.post("/api/v1/navigation/route", {"startLat": 28.15})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_navigation_route_resolves_destination_name(self):
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

    def test_ml_budget_accepts_free_text_destination_and_style_field(self):
        """Matches BudgetEstimator.jsx's exact payload: {destination: 'Rupa Lake', style: 'standard', ...}."""
        response = self.client.post(reverse("ml-budget"), {
            "destination": "Rupa Lake", "style": "standard", "days": 3, "travelers": 2,
        })
        # ML service isn't running in tests, but the request itself must be
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
