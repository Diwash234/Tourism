import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tourist", "0094_merge_20260930_1412"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="destination",
            name="slug",
            field=models.SlugField(blank=True, db_index=True, max_length=220, unique=True),
        ),
        migrations.AlterField(
            model_name="destination",
            name="category",
            field=models.ForeignKey(
                blank=True, db_index=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="destinations", to="tourist.category",
            ),
        ),
        migrations.AlterField(
            model_name="destination",
            name="district",
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="destination",
            name="province",
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="destinationimage",
            name="destination",
            field=models.ForeignKey(
                db_index=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="gallery", to="tourist.destination",
            ),
        ),
        migrations.AlterField(
            model_name="review",
            name="destination",
            field=models.ForeignKey(
                db_index=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="reviews", to="tourist.destination",
            ),
        ),
        migrations.CreateModel(
            name="SearchQuery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("query", models.CharField(max_length=500)),
                ("results_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("user", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                    related_name="search_queries", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"ordering": ["-created_at"], "verbose_name_plural": "Search queries"},
        ),
        migrations.CreateModel(
            name="LocationHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("latitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("longitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("accuracy_m", models.FloatField(blank=True, help_text="Device-reported accuracy in metres", null=True)),
                ("source", models.CharField(
                    choices=[("gps", "Browser GPS"), ("geoip", "GeoIP"), ("manual", "Manual")],
                    default="gps", max_length=10,
                )),
                ("recorded_at", models.DateTimeField(
                    help_text="When the device took the fix (may differ from created_at for delayed syncs)"
                )),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="location_history", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"ordering": ["-recorded_at"], "verbose_name_plural": "Location history"},
        ),
        migrations.AddIndex(
            model_name="locationhistory",
            index=models.Index(fields=["user", "recorded_at"], name="tourist_loc_user_id_8f5f0a_idx"),
        ),
        migrations.AddField(
            model_name="notificationpreference",
            name="email_notifications",
            field=models.BooleanField(default=True, help_text="Master toggle for email notifications"),
        ),
        migrations.AddField(
            model_name="notificationpreference",
            name="sms_notifications",
            field=models.BooleanField(default=True, help_text="Master toggle for SMS notifications"),
        ),
        migrations.AddField(
            model_name="notificationpreference",
            name="push_notifications",
            field=models.BooleanField(default=True, help_text="Master toggle for push notifications"),
        ),
        migrations.AddField(
            model_name="notificationpreference",
            name="marketing_emails",
            field=models.BooleanField(default=False, help_text="Receive promotional and marketing emails"),
        ),
        migrations.AddField(
            model_name="notificationpreference",
            name="weekly_digest",
            field=models.BooleanField(default=False, help_text="Receive a weekly digest of destinations and updates"),
        ),
        migrations.CreateModel(
            name="WebhookEndpoint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("url", models.URLField(max_length=500)),
                ("secret", models.CharField(blank=True, help_text="Secret for HMAC signature verification", max_length=200)),
                ("event_types", models.JSONField(default=list, help_text="List of event types to subscribe to")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="WebhookDelivery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=50)),
                ("payload", models.JSONField()),
                ("status", models.CharField(
                    choices=[("pending", "Pending"), ("success", "Success"), ("failed", "Failed"), ("retrying", "Retrying")],
                    default="pending", max_length=20,
                )),
                ("response_status", models.PositiveIntegerField(blank=True, null=True)),
                ("response_body", models.TextField(blank=True)),
                ("error_message", models.TextField(blank=True)),
                ("attempt_count", models.PositiveSmallIntegerField(default=0)),
                ("max_attempts", models.PositiveSmallIntegerField(default=3)),
                ("next_retry_at", models.DateTimeField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("webhook", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="deliveries", to="tourist.webhookendpoint",
                )),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="webhookdelivery",
            index=models.Index(fields=["status", "next_retry_at"], name="tourist_web_status_4a8b7e_idx"),
        ),
        migrations.AddIndex(
            model_name="webhookdelivery",
            index=models.Index(fields=["event_type", "created_at"], name="tourist_web_event_9e7f3b_idx"),
        ),
    ]
