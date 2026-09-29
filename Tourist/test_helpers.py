"""Test helpers and utilities for the tourism platform.

Provides:
- Test data factories
- API test helpers
- Common test assertions
- Mock helpers
"""
import json
from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

from .models import (
    Destination, Category, DestinationImage, Hotel, Hospital,
    PoliceStation, Restaurant, Review, Rating, User, Language,
)

User = get_user_model()


class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_user(email="test@example.com", password="testpass123", **kwargs):
        """Create a test user."""
        return User.objects.create_user(
            email=email,
            password=password,
            first_name=kwargs.get("first_name", "Test"),
            last_name=kwargs.get("last_name", "User"),
            is_verified=kwargs.get("is_verified", True),
            role=kwargs.get("role", User.Role.TOURIST),
        )

    @staticmethod
    def create_category(name="Test Category", **kwargs):
        """Create a test category."""
        return Category.objects.create(
            name=name,
            slug=kwargs.get("slug", name.lower().replace(" ", "-")),
        )

    @staticmethod
    def create_destination(name="Test Destination", **kwargs):
        """Create a test destination."""
        category = kwargs.get("category") or TestDataFactory.create_category()
        return Destination.objects.create(
            name=name,
            slug=kwargs.get("slug", name.lower().replace(" ", "-")),
            category=category,
            description=kwargs.get("description", "A beautiful test destination"),
            latitude=kwargs.get("latitude", 27.7172),
            longitude=kwargs.get("longitude", 85.3240),
            city=kwargs.get("city", "Kathmandu"),
            district=kwargs.get("district", "Kathmandu"),
            province=kwargs.get("province", "Bagmati"),
            status=kwargs.get("status", Destination.SubmissionStatus.APPROVED),
            is_active=kwargs.get("is_active", True),
        )

    @staticmethod
    def create_destination_image(destination, **kwargs):
        """Create a test destination image."""
        return DestinationImage.objects.create(
            destination=destination,
            external_url=kwargs.get("external_url", "https://example.com/image.jpg"),
            is_cover=kwargs.get("is_cover", True),
            source=kwargs.get("source", DestinationImage.Source.ADMIN),
        )

    @staticmethod
    def create_hotel(destination, name="Test Hotel", **kwargs):
        """Create a test hotel."""
        return Hotel.objects.create(
            destination=destination,
            name=name,
            price_per_night=kwargs.get("price_per_night", 100),
            booking_status=kwargs.get("booking_status", Hotel.BookingStatus.AVAILABLE),
        )

    @staticmethod
    def create_review(destination, user, comment="Great place!", **kwargs):
        """Create a test review."""
        return Review.objects.create(
            destination=destination,
            user=user,
            comment=comment,
            moderation_status=kwargs.get("moderation_status", "approved"),
        )

    @staticmethod
    def create_rating(destination, user, value=5, **kwargs):
        """Create a test rating."""
        return Rating.objects.create(
            destination=destination,
            user=user,
            value=value,
        )


class APITestCase(APITestCase):
    """Base API test case with common helpers."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user = TestDataFactory.create_user()
        self.admin = TestDataFactory.create_user(
            email="admin@example.com",
            role=User.Role.ADMIN,
        )

    def authenticate(self, user=None):
        """Authenticate the test client."""
        user = user or self.user
        self.client.force_authenticate(user=user)

    def create_and_authenticate(self, **kwargs):
        """Create a user and authenticate."""
        user = TestDataFactory.create_user(**kwargs)
        self.authenticate(user)
        return user

    def assert_response_status(self, response, expected_status):
        """Assert response status code."""
        self.assertEqual(
            response.status_code,
            expected_status,
            f"Expected status {expected_status}, got {response.status_code}: {response.content}"
        )

    def assert_paginated_response(self, response):
        """Assert response is paginated."""
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)


class MockExternalAPIs:
    """Context manager to mock external API calls."""

    def __init__(self):
        self.patches = []

    def __enter__(self):
        # Mock requests
        self.patches.append(patch('tourist.utils.requests.get'))
        self.patches.append(patch('tourist.utils.requests.post'))

        # Start all patches
        for p in self.patches:
            p.start()

        return self

    def __exit__(self, *args):
        for p in self.patches:
            p.stop()

    def mock_response(self, status_code=200, json_data=None):
        """Configure mock response."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {}
        for p in self.patches:
            p.return_value.get.return_value = mock_response
            p.return_value.post.return_value = mock_response


class PerformanceTestCase(TestCase):
    """Test case with performance assertions."""

    def assert_query_count(self, expected_count, func, *args, **kwargs):
        """Assert a function executes a specific number of queries."""
        from django.db import connection
        from django.test.utils import override_settings

        with override_settings(DEBUG=True):
            initial_count = len(connection.queries)
            func(*args, **kwargs)
            actual_count = len(connection.queries) - initial_count

        self.assertEqual(
            actual_count,
            expected_count,
            f"Expected {expected_count} queries, got {actual_count}"
        )

    def assert_execution_time(self, max_seconds, func, *args, **kwargs):
        """Assert a function executes within a time limit."""
        import time
        start = time.time()
        func(*args, **kwargs)
        duration = time.time() - start
        self.assertLess(
            duration,
            max_seconds,
            f"Function took {duration:.2f}s, expected < {max_seconds}s"
        )
