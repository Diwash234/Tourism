"""
Management command to run performance tests.
"""
import time
from django.core.management.base import BaseCommand
from django.test import TestCase
from rest_framework.test import APIClient

from tourist.models import User, Destination, Category


class Command(BaseCommand):
    help = "Run performance tests"

    def handle(self, *args, **options):
        self.stdout.write("Running performance tests...")

        # Test 1: User creation performance
        start = time.time()
        for i in range(100):
            User.objects.create_user(
                email=f"perf_test_{i}@example.com",
                password='testpass123'
            )
        elapsed = time.time() - start
        self.stdout.write(f"  User creation (100): {elapsed:.3f}s")

        # Test 2: Destination list performance
        start = time.time()
        for _ in range(100):
            list(Destination.objects.all()[:10])
        elapsed = time.time() - start
        self.stdout.write(f"  Destination list (100 queries): {elapsed:.3f}s")

        # Test 3: API response time
        client = APIClient()
        start = time.time()
        for _ in range(50):
            client.get('/api/v1/destinations/')
        elapsed = time.time() - start
        self.stdout.write(f"  API destinations (50 requests): {elapsed:.3f}s")

        self.stdout.write(self.style.SUCCESS("Performance tests completed"))
