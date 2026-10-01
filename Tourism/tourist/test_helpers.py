"""
Test helpers and factories for the Tourism API.
"""
import json
from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APIClient

from .models import User, Category, Destination, Review, TravelPlan


class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_user(email=None, role='tourist', is_verified=True, **kwargs):
        """Create a test user."""
        if email is None:
            email = f"test_{timezone.now().timestamp()}@example.com"
        return User.objects.create_user(
            email=email,
            password='testpass123',
            first_name='Test',
            last_name='User',
            role=role,
            is_verified=is_verified,
            **kwargs
        )

    @staticmethod
    def create_category(name=None, **kwargs):
        """Create a test category."""
        if name is None:
            name = f"Category {timezone.now().timestamp()}"
        return Category.objects.create(name=name, **kwargs)

    @staticmethod
    def create_destination(name=None, category=None, is_published=True, **kwargs):
        """Create a test destination."""
        if name is None:
            name = f"Destination {timezone.now().timestamp()}"
        if category is None:
            category = TestDataFactory.create_category()
        return Destination.objects.create(
            name=name,
            slug=name.lower().replace(' ', '-'),
            description='Test destination description',
            category=category,
            district='Kathmandu',
            province='Bagmati',
            latitude=27.7172,
            longitude=85.3240,
            is_published=is_published,
            **kwargs
        )

    @staticmethod
    def create_review(user=None, destination=None, rating=5, **kwargs):
        """Create a test review."""
        if user is None:
            user = TestDataFactory.create_user()
        if destination is None:
            destination = TestDataFactory.create_destination()
        return Review.objects.create(
            user=user,
            destination=destination,
            rating=rating,
            comment='Test review comment',
            is_approved=True,
            **kwargs
        )

    @staticmethod
    def create_travel_plan(user=None, **kwargs):
        """Create a test travel plan."""
        if user is None:
            user = TestDataFactory.create_user()
        return TravelPlan.objects.create(
            user=user,
            name='Test Travel Plan',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            **kwargs
        )


class APITestHelper:
    """Helper for API tests."""

    def __init__(self):
        self.client = APIClient()

    def authenticate(self, user):
        """Authenticate the test client."""
        self.client.force_authenticate(user=user)

    def get(self, url, **kwargs):
        """Make a GET request."""
        return self.client.get(url, **kwargs)

    def post(self, url, data=None, **kwargs):
        """Make a POST request."""
        return self.client.post(url, data, **kwargs)

    def put(self, url, data=None, **kwargs):
        """Make a PUT request."""
        return self.client.put(url, data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        """Make a PATCH request."""
        return self.client.patch(url, data, **kwargs)

    def delete(self, url, **kwargs):
        """Make a DELETE request."""
        return self.client.delete(url, **kwargs)

    def assert_status(self, response, expected_status):
        """Assert response status code."""
        assert response.status_code == expected_status, \
            f"Expected status {expected_status}, got {response.status_code}: {response.content}"

    def assert_json_contains(self, response, key):
        """Assert JSON response contains key."""
        data = json.loads(response.content)
        assert key in data, f"Expected key '{key}' in response: {data}"
