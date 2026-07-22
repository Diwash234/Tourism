from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tourist.models import User, Category, Destination, Hotel
from .models import HotelAssignment, AdminTask


class AdminPanelTests(APITestCase):
    def setUp(self):
        self.super_admin = User.objects.create_superuser(email="super@example.com", password="SuperPass123!")
        self.staff_admin = User.objects.create_user(
            email="staff@example.com", password="StaffPass123!", is_staff=True, is_verified=True
        )
        self.other_staff = User.objects.create_user(
            email="other@example.com", password="OtherPass123!", is_staff=True, is_verified=True
        )
        category = Category.objects.create(name="Lakes")
        destination = Destination.objects.create(
            name="Begnas Lake", category=category, description="x", latitude=28.15, longitude=84.05,
            created_by=self.super_admin,
        )
        self.hotel = Hotel.objects.create(destination=destination, name="Lakeside Inn", price_per_night=50)

    def test_only_super_admin_can_assign_hotel(self):
        self.client.force_authenticate(user=self.staff_admin)
        response = self.client.post(reverse("hotel-assignment-list"), {
            "hotel": self.hotel.id, "admin": self.staff_admin.id,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(reverse("hotel-assignment-list"), {
            "hotel": self.hotel.id, "admin": self.staff_admin.id,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_staff_admin_only_sees_own_assignments(self):
        HotelAssignment.objects.create(hotel=self.hotel, admin=self.staff_admin, assigned_by=self.super_admin)

        self.client.force_authenticate(user=self.other_staff)
        response = self.client.get(reverse("hotel-assignment-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

        self.client.force_authenticate(user=self.staff_admin)
        response = self.client.get(reverse("hotel-assignment-list"))
        self.assertEqual(response.data["count"], 1)

    def test_super_admin_can_create_task_for_staff(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(reverse("admin-task-list"), {
            "title": "Update hotel photos", "assigned_to": self.staff_admin.id,
            "related_hotel": self.hotel.id, "priority": "high",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["assigned_by_email"], self.super_admin.email)

    def test_staff_admin_cannot_assign_task_to_others(self):
        self.client.force_authenticate(user=self.staff_admin)
        response = self.client.post(reverse("admin-task-list"), {
            "title": "Sneaky task", "assigned_to": self.other_staff.id,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_admin_can_update_own_task_status(self):
        task = AdminTask.objects.create(title="Check reviews", assigned_to=self.staff_admin, assigned_by=self.super_admin)
        self.client.force_authenticate(user=self.staff_admin)
        response = self.client.patch(reverse("admin-task-detail", kwargs={"pk": task.id}), {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")
        self.assertIsNotNone(task.completed_at)

    def test_my_hotels_view(self):
        HotelAssignment.objects.create(hotel=self.hotel, admin=self.staff_admin, assigned_by=self.super_admin)
        self.client.force_authenticate(user=self.staff_admin)
        response = self.client.get(reverse("admin-panel-my-hotels"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Lakeside Inn")

    def test_dashboard_summary(self):
        AdminTask.objects.create(title="A", assigned_to=self.staff_admin, assigned_by=self.super_admin, status="pending")
        self.client.force_authenticate(user=self.staff_admin)
        response = self.client.get(reverse("admin-panel-dashboard-summary"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pending_tasks"], 1)
        self.assertFalse(response.data["is_super_admin"])