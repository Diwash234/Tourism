from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tourist.models import User, Category, Destination, Hotel
from admin_panel.models import HotelAssignment
from .models import Booking, HotelReview


class BookingTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin@example.com", password="AdminPass123!")
        self.tourist = User.objects.create_user(email="tourist@example.com", password="TouristPass123!", is_verified=True)
        self.hotel_manager = User.objects.create_user(
            email="manager@example.com", password="ManagerPass123!", is_staff=True, is_verified=True
        )
        category = Category.objects.create(name="Lakes")
        destination = Destination.objects.create(
            name="Phewa Lake", category=category, description="x", latitude=28.21, longitude=83.96,
            created_by=self.admin,
        )
        self.hotel = Hotel.objects.create(destination=destination, name="Lakeview Hotel", price_per_night=40)
        HotelAssignment.objects.create(hotel=self.hotel, admin=self.hotel_manager, assigned_by=self.admin)

    def test_tourist_can_create_booking_with_auto_calculated_price(self):
        self.client.force_authenticate(user=self.tourist)
        response = self.client.post(reverse("booking-list"), {
            "hotel": self.hotel.id,
            "check_in": date.today() + timedelta(days=5),
            "check_out": date.today() + timedelta(days=8),
            "guests": 2,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data["total_price"]), 120.0)  # 3 nights * 40
        self.assertEqual(response.data["status"], "pending")

    def test_checkout_before_checkin_rejected(self):
        self.client.force_authenticate(user=self.tourist)
        response = self.client.post(reverse("booking-list"), {
            "hotel": self.hotel.id,
            "check_in": date.today() + timedelta(days=5),
            "check_out": date.today() + timedelta(days=2),
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tourist_only_sees_own_bookings(self):
        other_tourist = User.objects.create_user(email="other@example.com", password="OtherPass123!", is_verified=True)
        Booking.objects.create(user=other_tourist, hotel=self.hotel, check_in=date.today(), check_out=date.today() + timedelta(days=1))

        self.client.force_authenticate(user=self.tourist)
        response = self.client.get(reverse("booking-list"))
        self.assertEqual(response.data["count"], 0)

    def test_hotel_manager_can_confirm_booking(self):
        booking = Booking.objects.create(
            user=self.tourist, hotel=self.hotel, check_in=date.today(), check_out=date.today() + timedelta(days=2)
        )
        self.client.force_authenticate(user=self.hotel_manager)
        response = self.client.post(reverse("booking-confirm", kwargs={"pk": booking.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "confirmed")

    def test_unrelated_staff_cannot_confirm_booking(self):
        unrelated_staff = User.objects.create_user(
            email="unrelated@example.com", password="Pass123!", is_staff=True, is_verified=True
        )
        booking = Booking.objects.create(
            user=self.tourist, hotel=self.hotel, check_in=date.today(), check_out=date.today() + timedelta(days=2)
        )
        self.client.force_authenticate(user=unrelated_staff)
        response = self.client.post(reverse("booking-confirm", kwargs={"pk": booking.id}))
        # 404, not 403: the booking isn't in this staff member's queryset at
        # all (not their own booking, not a hotel they manage), so it's
        # correctly treated as "doesn't exist for you" rather than leaking
        # that a booking with this id exists.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_tourist_can_cancel_own_booking(self):
        booking = Booking.objects.create(
            user=self.tourist, hotel=self.hotel, check_in=date.today(), check_out=date.today() + timedelta(days=2)
        )
        self.client.force_authenticate(user=self.tourist)
        response = self.client.post(reverse("booking-cancel", kwargs={"pk": booking.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")

    def test_hotel_review_duplicate_rejected(self):
        self.client.force_authenticate(user=self.tourist)
        self.client.post(reverse("hotel-review-list"), {"hotel": self.hotel.id, "rating": 5, "comment": "Great stay"})
        response = self.client.post(reverse("hotel-review-list"), {"hotel": self.hotel.id, "rating": 3})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)