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

    def test_create_destination_requires_admin(self):
        tourist = User.objects.create_user(email="tourist2@example.com", password="StrongPass123!", is_verified=True)
        self.client.force_authenticate(user=tourist)
        response = self.client.post(reverse("destination-list"), {
            "name": "Sarangkot", "category": self.category.id,
            "description": "Sunrise viewpoint", "latitude": 28.2380, "longitude": 83.9536,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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
