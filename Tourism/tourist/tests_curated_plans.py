"""Tests for Curated Travel Plans, Dual-Persona Itinerary Engine and Authentic Landmark Imagery.
"""
from __future__ import annotations

import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from tourist.models import (
    Category,
    Destination,
    DestinationImage,
    Itinerary,
    MarketplaceListing,
    MarketplacePartner,
    TravelPlan,
    User,
)
from tourist.serializers import public_destination_cover


class CuratedTravelPlansTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create categories
        cls.trekking_cat = Category.objects.create(name="Trekking", slug="trekking")
        cls.pilgrimage_cat = Category.objects.create(name="Pilgrimage", slug="pilgrimage")
        cls.heritage_cat = Category.objects.create(name="Heritage", slug="heritage")

        # Create staff user
        cls.staff_user = User.objects.create(
            email="curator_test@tourism.gov.np",
            first_name="Curator",
            last_name="Test",
            role=User.Role.ADMIN,
            is_staff=True,
            is_active=True,
        )

        # Create sample destination with authentic photo
        cls.pashupati = Destination.objects.create(
            name="Pashupatinath Sacred Hindu Sanctuary",
            slug="pashupatinath-sacred-hindu-sanctuary",
            category=cls.pilgrimage_cat,
            city="Kathmandu",
            district="Kathmandu",
            province="Bagmati",
            latitude=27.7104,
            longitude=85.3487,
            status=Destination.SubmissionStatus.APPROVED,
            is_active=True,
            is_featured=True,
            cover_image="https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Pashupatinath_Temple-2020.jpg/1280px-Pashupatinath_Temple-2020.jpg",
        )
        DestinationImage.objects.create(
            destination=cls.pashupati,
            external_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Pashupatinath_Temple-2020.jpg/1280px-Pashupatinath_Temple-2020.jpg",
            alt_text="Pashupatinath Temple Kathmandu",
            is_cover=True,
            verification_status=DestinationImage.ImageStatus.APPROVED,
            is_verified=True,
            source=DestinationImage.Source.WIKIMEDIA,
            source_url="https://commons.wikimedia.org/wiki/File:Pashupatinath_Temple-2020.jpg",
        )

        cls.client = APIClient()

    def test_curated_itineraries_list_returns_200(self):
        resp = self.client.get("/api/v1/curated-itineraries/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("count", data)
        self.assertIn("results", data)
        self.assertGreaterEqual(data["count"], 10)

    def test_curated_itineraries_filter_by_persona_nepali(self):
        resp = self.client.get("/api/v1/curated-itineraries/?persona=nepali")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for item in data["results"]:
            self.assertIn(item["persona"], ("nepali", "all"))

    def test_curated_itineraries_filter_by_persona_foreign(self):
        resp = self.client.get("/api/v1/curated-itineraries/?persona=foreign")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for item in data["results"]:
            self.assertIn(item["persona"], ("foreign", "all"))

    def test_curated_itineraries_filter_by_category(self):
        resp = self.client.get("/api/v1/curated-itineraries/?category=trekking")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for item in data["results"]:
            self.assertEqual(item["category"], "trekking")

    def test_curated_itinerary_detail_raw(self):
        resp = self.client.get("/api/v1/curated-itineraries/everest-base-camp-kala-patthar/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["slug"], "everest-base-camp-kala-patthar")
        self.assertEqual(data["days"], 14)
        self.assertIn("days_schedule", data)

    def test_curated_itinerary_planner_mode_payload(self):
        resp = self.client.get(
            "/api/v1/curated-itineraries/muktinath-lower-mustang-yatra/?mode=planner&nationality=nepali&travelers=2"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("itinerary", data)
        self.assertIn("altitude_profile", data)
        self.assertIn("permits_and_fees", data)
        self.assertIn("trip_readiness", data)
        self.assertEqual(data["nationality"], "nepali")
        self.assertEqual(data["travelers"], 2)

    def test_dual_persona_permits_difference(self):
        # Nepali national request
        resp_np = self.client.get(
            "/api/v1/curated-itineraries/annapurna-circuit-tilicho-lake/?mode=planner&nationality=nepali"
        )
        self.assertEqual(resp_np.status_code, 200)
        permits_np = resp_np.json().get("permits_and_fees")
        self.assertEqual(permits_np["nationality"], "nepali")
        # Nepali citizens do not pay TIMS
        self.assertIsNone(permits_np.get("tims"))

        # Foreign national request
        resp_fg = self.client.get(
            "/api/v1/curated-itineraries/annapurna-circuit-tilicho-lake/?mode=planner&nationality=foreign"
        )
        self.assertEqual(resp_fg.status_code, 200)
        permits_fg = resp_fg.json().get("permits_and_fees")
        self.assertEqual(permits_fg["nationality"], "foreign")

    def test_authentic_cover_image_resolution(self):
        cover = public_destination_cover(self.pashupati)
        self.assertIsNotNone(cover)
        self.assertIn("Pashupatinath_Temple", cover)

    def test_seed_curated_travel_plans_command(self):
        from django.core.management import call_command
        call_command("seed_curated_travel_plans")
        self.assertGreaterEqual(TravelPlan.objects.count(), 12)
        self.assertGreaterEqual(Itinerary.objects.count(), 12)
        self.assertGreaterEqual(MarketplaceListing.objects.count(), 12)
