import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    ADDED: curated from `makemigrations`' full autodetected diff for the
    tourist app, keeping only the additive half of it.

    The full diff also included 17 RemoveField calls and 11 DeleteModel
    calls (SharedTrip, SOSAlert, TrustedContact, LocationPing,
    Notification, DeviceToken, Attraction, CulturalActivity, FoodPlace,
    TravelExpenseFeedback, TravelRiskFeedback, plus several Destination
    fields) -- those would drop tables/columns holding real data
    (SOS alerts, trusted emergency contacts) with no migration plan for
    that data. Deliberately excluded here; that remains a separate,
    deliberate decision for a human to make, not something to slip in
    via this fix.

    What IS included, and why it's safe:
      - New models entirely (Itinerary, ItineraryDay, ItineraryStop,
        Restaurant, TripFeedback, TripFeedbackMedia,
        FieldVerificationReport/Photo/Task): brand new tables, can't
        conflict with or lose anything.
      - New image fields on Hospital/PoliceStation: purely additive,
        and closes a real gap noted earlier -- these models already had
        no way to attach a photo at all.
      - AlterField on best_time_to_visit / is_verified /
        verification_status: field-metadata-only changes matching
        model declarations already added in earlier migrations
        (0012, plus the DestinationImage model fix) -- no schema impact.
      - AlterField on User.role: widens the choices list to the roles
        already used elsewhere in the app (admin, staff, tourism_admin,
        etc.) -- doesn't invalidate any existing stored value.

    This directly fixes a real, confirmed bug: deleting ANY Category
    (regardless of whether it's in use) crashed with "no such table:
    tourist_itinerary_category_filter" -- Itinerary.category_filter is
    a ManyToManyField to Category that existed in models.py but whose
    table was never created, so Django's delete-cascade collector
    checked a table that didn't exist. Confirmed via a real DELETE
    request before writing this fix.
    """

    dependencies = [
        ("tourist", "0013_destination_history_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="hospital",
            name="cover_image",
            field=models.ImageField(blank=True, null=True, upload_to="hospitals/"),
        ),
        migrations.AddField(
            model_name="hospital",
            name="external_image_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="policestation",
            name="cover_image",
            field=models.ImageField(blank=True, null=True, upload_to="police_stations/"),
        ),
        migrations.AddField(
            model_name="policestation",
            name="external_image_url",
            field=models.URLField(blank=True),
        ),
        migrations.AlterField(
            model_name="destination",
            name="best_time_to_visit",
            field=models.CharField(blank=True, help_text="e.g. 'October to December, and March to April' -- can be AI-generated if left blank.", max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name="destinationimage",
            name="is_verified",
            field=models.BooleanField(default=True, help_text="Legacy moderation flag; new admin/system-added photos are auto-verified."),
        ),
        migrations.AlterField(
            model_name="destinationimage",
            name="verification_status",
            field=models.CharField(blank=True, default="approved", max_length=20),
        ),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(choices=[("tourist", "Tourist"), ("guide", "Local Guide"), ("admin", "Admin"), ("super_admin", "Super Admin"), ("tourism_admin", "Tourism Admin"), ("content_moderator", "Content Moderator"), ("district_manager", "District Manager"), ("hotel_manager", "Hotel Manager"), ("staff", "Staff"), ("tourist_police", "Tourist Police"), ("police", "Police"), ("hospital_staff", "Hospital Staff"), ("rescue_team", "Rescue Team"), ("emergency_operator", "Emergency Operator"), ("field_verifier", "Field Verifier")], default="tourist", max_length=20),
        ),
        migrations.CreateModel(
            name="FieldVerificationReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("visit_date", models.DateField()),
                ("is_place_accurate", models.BooleanField(default=True)),
                ("accuracy_notes", models.TextField(blank=True, help_text="What's wrong, if is_place_accurate is False.")),
                ("witnessed_sickness", models.BooleanField(default=False)),
                ("witnessed_accident", models.BooleanField(default=False)),
                ("witnessed_misleading_activity", models.BooleanField(default=False, help_text="Scams, overcharging, false guiding, etc.")),
                ("hazards_observed", models.JSONField(blank=True, default=list, help_text='e.g. ["avalanche_risk", "flood_risk", "landslide_risk"] -- any real-world hazard signs seen on this visit.')),
                ("transport_ease", models.CharField(blank=True, choices=[("easy", "Easy to reach"), ("moderate", "Moderately difficult"), ("difficult", "Difficult")], max_length=10)),
                ("local_helpfulness", models.CharField(blank=True, choices=[("very_helpful", "Very Helpful"), ("somewhat_helpful", "Somewhat Helpful"), ("neutral", "Neutral"), ("unhelpful", "Unhelpful")], max_length=20)),
                ("local_behavior_notes", models.TextField(blank=True, help_text="General notes on how locals greeted/treated visitors.")),
                ("general_notes", models.TextField(blank=True)),
                ("review_status", models.CharField(choices=[("pending", "Pending Review"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=10)),
                ("review_note", models.TextField(blank=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reports_reviewed", to=settings.AUTH_USER_MODEL)),
                ("submitted_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="verification_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="FieldVerificationPhoto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="field_verification/")),
                ("caption", models.CharField(blank=True, max_length=200)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("report", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="photos", to="tourist.fieldverificationreport")),
            ],
        ),
        migrations.CreateModel(
            name="FieldVerificationTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("assigned", "Assigned"), ("in_progress", "In Progress"), ("submitted", "Report Submitted"), ("reviewed", "Reviewed")], default="assigned", max_length=20)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("instructions", models.TextField(blank=True)),
                ("assigned_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tasks_assigned", to=settings.AUTH_USER_MODEL)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="verification_tasks", to=settings.AUTH_USER_MODEL)),
                ("destination", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="verification_tasks", to="tourist.destination")),
            ],
        ),
        migrations.AddField(
            model_name="fieldverificationreport",
            name="task",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="report", to="tourist.fieldverificationtask"),
        ),
        migrations.CreateModel(
            name="Itinerary",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(blank=True, help_text="e.g. 'Annapurna Circuit, June 2026'", max_length=200)),
                ("status", models.CharField(choices=[("planning", "Planning"), ("confirmed", "Confirmed"), ("in_progress", "In Progress"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="planning", max_length=20)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("num_days", models.PositiveSmallIntegerField(default=1)),
                ("total_distance_km", models.FloatField(blank=True, help_text="Filled in when the plan is generated via the route engine.", null=True)),
                ("category_filter", models.ManyToManyField(blank=True, related_name="itineraries", to="tourist.category")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="itineraries", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ItineraryDay",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("day_number", models.PositiveSmallIntegerField()),
                ("date", models.DateField(blank=True, null=True)),
                ("itinerary", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="days", to="tourist.itinerary")),
            ],
            options={
                "ordering": ["day_number"],
                "unique_together": {("itinerary", "day_number")},
            },
        ),
        migrations.CreateModel(
            name="ItineraryStop",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveSmallIntegerField(default=0, help_text="Order within the day.")),
                ("distance_from_previous_km", models.FloatField(blank=True, help_text="Route distance from the previous stop (same day) or previous day's last stop -- filled in via the route engine when the plan is generated.", null=True)),
                ("notes", models.TextField(blank=True)),
                ("is_visited", models.BooleanField(default=False)),
                ("visited_at", models.DateTimeField(blank=True, null=True)),
                ("day", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stops", to="tourist.itineraryday")),
                ("destination", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="itinerary_stops", to="tourist.destination")),
            ],
            options={
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="Restaurant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                ("cuisine_type", models.CharField(blank=True, help_text="e.g. 'Nepali', 'Newari', 'Continental', 'Multi-cuisine'", max_length=100)),
                ("price_range", models.CharField(choices=[("budget", "$ Budget"), ("mid", "$$ Mid-range"), ("upscale", "$$$ Upscale")], default="mid", max_length=10)),
                ("rating", models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("opening_hours", models.CharField(blank=True, max_length=200)),
                ("booking_url", models.URLField(blank=True, help_text="Link to book/order externally, if available.")),
                ("cover_image", models.ImageField(blank=True, null=True, upload_to="restaurants/covers/")),
                ("external_image_url", models.URLField(blank=True)),
                ("dietary_options", models.JSONField(blank=True, default=list, help_text='e.g. ["vegetarian", "vegan", "halal", "gluten_free"]')),
                ("address", models.CharField(blank=True, max_length=255)),
                ("latitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("longitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("source", models.CharField(choices=[("dataset", "Imported Dataset"), ("google_places", "Google Places"), ("foursquare", "Foursquare"), ("manual", "Manually Added")], default="dataset", max_length=20)),
                ("destination", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="restaurants", to="tourist.destination")),
            ],
            options={
                "ordering": ["-rating"],
            },
        ),
        migrations.CreateModel(
            name="TripFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("num_people", models.PositiveSmallIntegerField(default=1)),
                ("actual_total_cost", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("actual_accommodation_cost", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("actual_travel_cost", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("actual_entry_fees_cost", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("actual_food_cost", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("extra_cost", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("extra_cost_note", models.CharField(blank=True, help_text="What the extra cost was for, if any.", max_length=200)),
                ("route_rating", models.PositiveSmallIntegerField(blank=True, help_text="1-5, how good the suggested route actually was.", null=True)),
                ("route_notes", models.TextField(blank=True)),
                ("hotel_rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("hotel_notes", models.TextField(blank=True)),
                ("restaurant_rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("restaurant_notes", models.TextField(blank=True)),
                ("general_suggestion", models.TextField(blank=True, help_text="Open suggestion box -- anything else worth telling future travelers/the recommendation engine.")),
                ("itinerary", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="feedback", to="tourist.itinerary")),
                ("submitted_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="trip_feedback", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TripFeedbackMedia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("media_type", models.CharField(choices=[("image", "Image"), ("video", "Video")], max_length=10)),
                ("file", models.FileField(upload_to="trip_feedback/")),
                ("caption", models.CharField(blank=True, max_length=200)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("feedback", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="media", to="tourist.tripfeedback")),
            ],
        ),
    ]