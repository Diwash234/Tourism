from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tourist", "0038_cms_form_blocks"),
    ]

    operations = [
        migrations.AddField(
            model_name="destination",
            name="is_featured",
            field=models.BooleanField(
                default=False,
                help_text="Pinned by an administrator for the homepage and traveller dashboard.",
            ),
        ),
        migrations.AddIndex(
            model_name="destination",
            index=models.Index(fields=["is_featured", "is_active"], name="tourist_des_is_feat_8f1a2c_idx"),
        ),
        migrations.CreateModel(
            name="VisitorNotice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("festival", "Festival"),
                            ("closure", "Closure"),
                            ("permit", "Permit"),
                            ("seasonal", "Seasonal"),
                            ("crowd", "Crowd"),
                            ("transport", "Transport"),
                            ("info", "Information"),
                        ],
                        db_index=True,
                        default="info",
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("body", models.TextField(blank=True)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("district", models.CharField(blank=True, max_length=100)),
                ("starts_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("is_published", models.BooleanField(db_index=True, default=True)),
                (
                    "destination",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="visitor_notices",
                        to="tourist.destination",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="visitor_notices_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at"],
            },
        ),
        migrations.AddIndex(
            model_name="visitornotice",
            index=models.Index(fields=["is_published", "starts_at", "ends_at"], name="tourist_vis_is_publ_4d9e1a_idx"),
        ),
        migrations.AddIndex(
            model_name="visitornotice",
            index=models.Index(fields=["kind", "is_published"], name="tourist_vis_kind_7c2b11_idx"),
        ),
    ]
