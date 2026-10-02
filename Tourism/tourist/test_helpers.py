"""
Test helpers and utilities for the Tourism API.
"""
import json

from django.test import TestCase
from rest_framework.test import APIClient

from .models import User, Category, Destination


class TourismTestCase(TestCase):
    """Base test case with common helpers."""

    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user()
        self.category = self.create_category()
        self.destination = self.create_destination()

    def create_user(self, email=None, role='tourist', **kwargs):
        """Create a test user."""
        if email is None:
            email = f"test_{self._testMethodName}@example.com"
        return User.objects.create_user(
            email=email,
            password='testpass123',
            first_name='Test',
            last_name='User',
            role=role,
            **kwargs
        )

    def create_category(self, name=None, **kwargs):
        """Create a test category."""
        if name is None:
            name = f"Category {self._testMethodName}"
        return Category.objects.create(name=name, **kwargs)

    def create_destination(self, name=None, category=None, **kwargs):
        """Create a test destination."""
        if name is None:
            name = f"Destination {self._testMethodName}"
        if category is None:
            category = self.category
        return Destination.objects.create(
            name=name,
            slug=name.lower().replace(' ', '-'),
            description='Test destination description',
            category=category,
            district='Kathmandu',
            province='Bagmati',
            latitude=27.7172,
            longitude=85.3240,
            status="approved",
            is_active=True,
            **kwargs
        )

    def authenticate(self, user=None):
        """Authenticate the test client."""
        if user is None:
            user = self.user
        self.client.force_authenticate(user=user)

    def get_json(self, url, **kwargs):
        """Make a GET request and return JSON response."""
        response = self.client.get(url, **kwargs)
        return response, json.loads(response.content)

    def post_json(self, url, data=None, **kwargs):
        """Make a POST request and return JSON response."""
        response = self.client.post(url, data, format='json', **kwargs)
        return response, json.loads(response.content)

    def put_json(self, url, data=None, **kwargs):
        """Make a PUT request and return JSON response."""
        response = self.client.put(url, data, format='json', **kwargs)
        return response, json.loads(response.content)

    def patch_json(self, url, data=None, **kwargs):
        """Make a PATCH request and return JSON response."""
        response = self.client.patch(url, data, format='json', **kwargs)
        return response, json.loads(response.content)

    def delete_json(self, url, **kwargs):
        """Make a DELETE request and return JSON response."""
        response = self.client.delete(url, **kwargs)
        return response, json.loads(response.content) if response.content else None


class AuthTestCase(TourismTestCase):
    """Test case for authentication tests."""

    def test_login_success(self):
        """Test successful login."""
        response = self.client.post('/api/v1/auth/login/', {
            'email': self.user.email,
            'password': 'testpass123'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('access', data)
        self.assertIn('refresh', data)

    def test_login_failure(self):
        """Test failed login."""
        response = self.client.post('/api/v1/auth/login/', {
            'email': self.user.email,
            'password': 'wrongpassword'
        }, format='json')
        self.assertEqual(response.status_code, 401)


class RBACTestCase(TourismTestCase):
    """Test case for RBAC tests."""

    def test_tourist_cannot_access_admin(self):
        """Test that tourists cannot access admin endpoints."""
        self.authenticate()
        response = self.client.get('/api/v1/admin/stats/')
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_admin(self):
        """Test that admins can access admin endpoints."""
        admin = self.create_user(
            email=f"admin_{self._testMethodName}@example.com",
            role='admin', is_staff=True)
        self.authenticate(admin)
        response = self.client.get('/api/v1/admin/stats/')
        self.assertIn(response.status_code, [200, 404])  # 404 if no data
