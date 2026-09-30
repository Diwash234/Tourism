"""
Testing utilities and helpers.
"""
import json
from typing import Any, Optional

from django.test import TestCase, Client
from rest_framework.test import APIClient

from .models import User, Destination, Category


class APITestCase(TestCase):
    """Base test case with API helpers."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def authenticate(self, user: Optional[User] = None):
        """Authenticate the test client."""
        user = user or self.user
        self.client.force_authenticate(user=user)

    def get(self, url: str, **kwargs):
        return self.client.get(url, **kwargs)

    def post(self, url: str, data: Any = None, **kwargs):
        return self.client.post(url, data, **kwargs)

    def put(self, url: str, data: Any = None, **kwargs):
        return self.client.put(url, data, **kwargs)

    def delete(self, url: str, **kwargs):
        return self.client.delete(url, **kwargs)

    def assert_success(self, response):
        self.assertTrue(response.data.get("success", False))

    def assert_error(self, response, code: str):
        self.assertEqual(response.data.get("error", {}).get("code"), code)


class DestinationTestCase(APITestCase):
    """Test case with destination helpers."""

    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.destination = Destination.objects.create(
            name="Test Destination",
            slug="test-destination",
            description="A test destination",
            district="Kathmandu",
            province="Bagmati",
            latitude=27.7172,
            longitude=85.3240,
            category=self.category,
            is_published=True,
        )

    def create_destination(self, **kwargs):
        """Create a test destination with default values."""
        defaults = {
            "name": "New Destination",
            "slug": "new-destination",
            "description": "A new destination",
            "district": "Pokhara",
            "province": "Gandaki",
            "latitude": 28.2096,
            "longitude": 83.9856,
            "category": self.category,
            "is_published": True,
        }
        defaults.update(kwargs)
        return Destination.objects.create(**defaults)
