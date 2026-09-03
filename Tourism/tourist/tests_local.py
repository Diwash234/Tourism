"""
Tests for the endpoints added in views_local.py:

  - /local/places            (Local Guide Dashboard submissions)
  - /user/personal-details/  (traveller document / emergency contacts)
  - /safety/shared/<token>/  (public shared-trip alias)

These close the frontend->backend contract gaps found by auditing every
axios call in frontend/Tourism/src/api against the OpenAPI schema: the
pages existed (LocalDashboard.jsx, PersonalDetails.jsx, SharedTripView.jsx)
but the backend routes did not, so the UI silently fell back to
localStorage and share links 404'd.
"""
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    Destination,
    DestinationImage,
    PersonalDetail,
    User,
)


class PersonalDetailAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="traveller@example.com", password="StrongPass123!", is_verified=True
        )
        other = User.objects.create_user(
            email="other@example.com", password="StrongPass123!", is_verified=True
        )
        PersonalDetail.objects.create(
            user=other, full_name="Someone Else", relation_tag="relative"
        )
        self.client.force_authenticate(self.user)

    def test_list_wraps_items_and_is_owner_scoped(self):
        PersonalDetail.objects.create(
            user=self.user,
            full_name="Ram Bahadur",
            relation_tag="relative",
            relation="Father",
            phone="+9779851000111",
            id_type="Citizenship",
            id_number="12-34-56",
            nationality="Nepali",
        )
        response = self.client.get("/api/v1/user/personal-details/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        item = response.data["items"][0]
        self.assertEqual(item["fullName"], "Ram Bahadur")
        self.assertEqual(item["relationTag"], "relative")
        self.assertEqual(item["idType"], "Citizenship")

    def test_create_update_delete_flow(self):
        payload = {
            "fullName": "Sita Sharma",
            "relationTag": "self",
            "phone": "+9779801111222",
            "idType": "Passport",
            "idNumber": "PN1234567",
            "nationality": "Nepali",
            "notes": "Passport expires 2030",
        }
        response = self.client.post("/api/v1/user/personal-details/", payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pk = response.data["id"]

        response = self.client.put(
            f"/api/v1/user/personal-details/{pk}/", {**payload, "fullName": "Sita S."}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["fullName"], "Sita S.")

        response = self.client.delete(f"/api/v1/user/personal-details/{pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PersonalDetail.objects.filter(pk=pk).exists())

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get("/api/v1/user/personal-details/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LocalPlaceSubmissionAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="guide@example.com", password="StrongPass123!", is_verified=True
        )
        self.client.force_authenticate(self.user)

    def test_submit_creates_pending_destination_in_admin_pipeline(self):
        response = self.client.post(
            "/api/v1/local/places",
            {
                "name": "Silent Gumba",
                "location": "Ward 4, Bandipur",
                "category": "monastery",
                "imageUrl": "https://example.com/gumba.jpg",
                "description": "A quiet monastery on the ridge.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Destination.SubmissionStatus.PENDING)

        place = Destination.objects.get(pk=response.data["id"])
        self.assertTrue(place.is_user_submitted)
        self.assertFalse(place.is_active)
        self.assertEqual(place.created_by, self.user)
        self.assertEqual(place.category.name, "Monastery / Gumba")
        # The submitted photo lands in the gallery as a pending community upload
        photo = place.gallery.get()
        self.assertEqual(photo.external_url, "https://example.com/gumba.jpg")
        self.assertEqual(photo.source, DestinationImage.Source.USER_UPLOAD)
        self.assertEqual(
            photo.verification_status, DestinationImage.ImageStatus.PENDING
        )

    def test_list_returns_own_submissions_only(self):
        other = User.objects.create_user(
            email="other-guide@example.com", password="StrongPass123!", is_verified=True
        )
        Destination.objects.create(
            name="Other Guide Place", is_user_submitted=True, created_by=other
        )
        Destination.objects.create(
            name="My Place", is_user_submitted=True, created_by=self.user
        )
        response = self.client.get("/api/v1/local/places")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data["items"]]
        self.assertEqual(names, ["My Place"])

    def test_update_and_delete_own_pending_place(self):
        place = Destination.objects.create(
            name="Old Name",
            is_user_submitted=True,
            created_by=self.user,
            status=Destination.SubmissionStatus.PENDING,
        )
        response = self.client.put(
            f"/api/v1/local/places/{place.pk}",
            {"description": "Updated description."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        place.refresh_from_db()
        self.assertEqual(place.description, "Updated description.")

        response = self.client.delete(f"/api/v1/local/places/{place.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Destination.objects.filter(pk=place.pk).exists())

    def test_cannot_touch_another_users_place(self):
        other = User.objects.create_user(
            email="stranger@example.com", password="StrongPass123!", is_verified=True
        )
        place = Destination.objects.create(
            name="Not Mine",
            is_user_submitted=True,
            created_by=other,
            status=Destination.SubmissionStatus.PENDING,
        )
        response = self.client.delete(f"/api/v1/local/places/{place.pk}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_name_is_required(self):
        response = self.client.post("/api/v1/local/places", {"location": "Somewhere"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SharedTripAliasTests(APITestCase):
    """The share links the frontend copies point at /safety/shared/<token>/."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="sharer@example.com", password="StrongPass123!", is_verified=True
        )

    def test_alias_serves_the_same_view_as_trip_share(self):
        trip_resp = self.client.post(
            "/api/v1/safety/trips/",
            {
                "label": "Annapurna Day 3",
                "expires_at": (timezone.now() + timedelta(days=1)).isoformat(),
            },
        )
        # The tourist demo user may lack permission in a pristine test DB;
        # authenticate to be safe.
        self.client.force_authenticate(self.user)
        trip_resp = self.client.post(
            "/api/v1/safety/trips/",
            {
                "label": "Annapurna Day 3",
                "expires_at": (timezone.now() + timedelta(days=1)).isoformat(),
            },
        )
        self.assertEqual(trip_resp.status_code, status.HTTP_201_CREATED, trip_resp.content)
        token = trip_resp.data["share_token"]

        alias_resp = self.client.get(f"/api/v1/safety/shared/{token}/")
        self.assertEqual(alias_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(alias_resp.data["label"], "Annapurna Day 3")
        self.assertIn("latest_ping", alias_resp.data)

        # ...and the original path keeps working
        original_resp = self.client.get(f"/api/v1/safety/trip-share/{token}/")
        self.assertEqual(original_resp.status_code, status.HTTP_200_OK)

    def test_unknown_token_is_404(self):
        response = self.client.get("/api/v1/safety/shared/00000000-0000-0000-0000-000000000000/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
