# import uuid

# from django.conf import settings
# from django.db import models
# from django.utils import timezone
# from phonenumber_field.modelfields import PhoneNumberField


# class TrustedContact(models.Model):
#     """
#     A person a user has designated to receive safety alerts / shared trip
#     access. Doesn't need their own account -- identified by email or
#     phone, contacted directly when needed (SOS, trip share links).
#     """
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trusted_contacts")
#     name = models.CharField(max_length=150)
#     relationship = models.CharField(max_length=100, blank=True, help_text="e.g. 'Parent', 'Spouse', 'Friend'")
#     email = models.EmailField(blank=True)
#     phone_number = PhoneNumberField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ["-created_at"]

#     def __str__(self):
#         return f"{self.name} ({self.relationship or 'contact'}) for {self.user}"


# class SharedTrip(models.Model):
#     """
#     A live location share the user has explicitly turned on. The
#     `share_token` is what a TrustedContact uses to view it -- no account
#     needed on their end, just the (unguessable, revocable) link.
#     """
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shared_trips")
#     share_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
#     label = models.CharField(max_length=150, blank=True, help_text="e.g. 'Annapurna trek, Day 3'")
#     is_active = models.BooleanField(default=True)
#     started_at = models.DateTimeField(auto_now_add=True)
#     expires_at = models.DateTimeField(help_text="Auto-expires -- a share link should never stay valid forever.")
#     trusted_contacts = models.ManyToManyField(TrustedContact, related_name="shared_trips", blank=True)

#     class Meta:
#         ordering = ["-started_at"]

#     def is_valid(self):
#         return self.is_active and timezone.now() < self.expires_at

#     def __str__(self):
#         return f"{self.label or 'Trip'} ({self.user}) -- {'active' if self.is_valid() else 'expired/ended'}"


# class LocationPing(models.Model):
#     """
#     One GPS position update during an active SharedTrip. Polling-based
#     (the trusted contact's view re-fetches the latest ping every N
#     seconds) rather than WebSocket push -- simpler to build correctly
#     first; true real-time (Django Channels) is a bigger, separate
#     addition if genuinely needed later.
#     """
#     trip = models.ForeignKey(SharedTrip, on_delete=models.CASCADE, related_name="pings")
#     latitude = models.DecimalField(max_digits=9, decimal_places=6)
#     longitude = models.DecimalField(max_digits=9, decimal_places=6)
#     recorded_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ["-recorded_at"]


# class SOSAlert(models.Model):
#     """
#     An emergency trigger during a trip (shared or not). Kept separate
#     from SharedTrip so an SOS can be raised even with no active share --
#     the trip FK is optional for that reason.
#     """
#     class Status(models.TextChoices):
#         ACTIVE = "active", "Active"
#         RESOLVED = "resolved", "Resolved"
#         FALSE_ALARM = "false_alarm", "False Alarm"

#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sos_alerts")
#     trip = models.ForeignKey(SharedTrip, on_delete=models.SET_NULL, null=True, blank=True, related_name="sos_alerts")
#     latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
#     longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
#     message = models.TextField(blank=True)
#     status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
#     triggered_at = models.DateTimeField(auto_now_add=True)
#     resolved_at = models.DateTimeField(null=True, blank=True)
#     notified_contacts = models.ManyToManyField(TrustedContact, related_name="sos_alerts", blank=True)

#     class Meta:
#         ordering = ["-triggered_at"]

#     def __str__(self):
#         return f"SOS from {self.user} ({self.status})"