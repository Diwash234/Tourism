from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Category, Destination, Hospital, Hotel
from .views_ml import enrich_itinerary_with_services


class VerifiedItineraryServiceTests(TestCase):
    def test_city_catalogue_normalizes_city_and_district_names(self):
        from .data_itineraries import get_city_profile

        profile = get_city_profile("pokhara")
        self.assertEqual(profile["city"], "Pokhara")
        self.assertEqual(profile["district"], "Kaski")

    def setUp(self):
        category = Category.objects.create(name="Test Attraction", slug="test-attraction")
        self.destination = Destination.objects.create(
            name="Verified Itinerary Anchor",
            slug="verified-itinerary-anchor",
            category=category,
            city="Pokhara",
            city_english="Pokhara",
            district="Kaski",
            latitude=28.2096,
            longitude=83.9856,
            status=Destination.SubmissionStatus.APPROVED,
            is_active=True,
        )

    def test_only_verified_services_with_source_links_are_attached(self):
        Hotel.objects.create(
            destination=self.destination,
            name="Unverified Nearby Hotel",
            latitude=28.2100,
            longitude=83.9856,
            is_verified=False,
        )
        Hotel.objects.create(
            destination=self.destination,
            name="Verified Hotel",
            latitude=28.2110,
            longitude=83.9856,
            source_url="https://example.test/hotel-source",
            is_verified=True,
        )
        Hospital.objects.create(
            destination=self.destination,
            name="Verified Hospital",
            address="Pokhara",
            phone="061555555",
            latitude=28.2120,
            longitude=83.9856,
            district="Kaski",
            source_name="Verified directory",
            source_url="https://example.test/hospital-source",
            is_verified=True,
        )
        Hospital.objects.create(
            destination=self.destination,
            name="Unverified Hospital",
            address="Pokhara",
            phone="061555556",
            latitude=28.2097,
            longitude=83.9856,
            district="Kaski",
            is_verified=False,
        )

        payload = {
            "itinerary": [{
                "destinations": [{
                    "latitude": 28.2096,
                    "longitude": 83.9856,
                }],
            }],
        }

        result = enrich_itinerary_with_services(payload)
        services = result["itinerary"][0]["nearby_services"]

        self.assertEqual([row["name"] for row in services["hotels"]], ["Verified Hotel"])
        self.assertEqual([row["name"] for row in services["hospitals"]], ["Verified Hospital"])
        self.assertEqual(services["hotels"][0]["source_url"], "https://example.test/hotel-source")
        self.assertEqual(services["hospitals"][0]["source_url"], "https://example.test/hospital-source")
        self.assertEqual(result["service_distance_method"], "haversine_straight_line")
        self.assertGreater(services["hotels"][0]["distance_km"], 0)

    @patch("tourist.trip_readiness.enrich_with_trip_readiness", side_effect=lambda payload, **kwargs: payload)
    @patch("tourist.views_ml.requests.post")
    def test_recognized_city_uses_real_catalogue_stops_not_generic_city_template(
        self, ml_post, _readiness
    ):
        response = APIClient().post(
            "/api/v1/ml/itinerary/",
            {"start_city": "Pokhara", "days": 1, "interests": ["nature"]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        ml_post.assert_not_called()
        result = response.json()
        self.assertEqual(result["source"], "internal_db_engine")
        stops = [
            stop
            for day in result["itinerary"]
            for stop in day.get("destinations", [])
        ]
        self.assertIn("Verified Itinerary Anchor", [stop["name"] for stop in stops])
        self.assertNotIn("data_source", result)
