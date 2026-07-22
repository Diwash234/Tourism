from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    hotel = models.ForeignKey("tourist.Hotel", on_delete=models.CASCADE, related_name="bookings")
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="USD")
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.hotel.name} ({self.check_in} to {self.check_out})"

    def save(self, *args, **kwargs):
        if self.total_price is None and self.hotel.price_per_night:
            nights = max((self.check_out - self.check_in).days, 1)
            self.total_price = self.hotel.price_per_night * nights
        super().save(*args, **kwargs)


class HotelReview(models.Model):
    hotel = models.ForeignKey("tourist.Hotel", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hotel_reviews")
    booking = models.ForeignKey(
        Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name="review",
        help_text="Optional link to the stay this review is about",
    )
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("hotel", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.hotel.name} - {self.rating}* by {self.user.email}"