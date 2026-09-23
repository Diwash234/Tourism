from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tourist", "0040_marketplace"),
    ]

    operations = [
        migrations.AddField(
            model_name="marketplacepartner",
            name="license_info",
            field=models.CharField(blank=True, max_length=240),
        ),
        migrations.AddField(
            model_name="marketplacepartner",
            name="logo_url",
            field=models.URLField(blank=True, max_length=600),
        ),
        migrations.AddField(
            model_name="marketplacepartner",
            name="services",
            field=models.TextField(blank=True, help_text="Packages or services the partner wants to list."),
        ),
        migrations.AlterField(
            model_name="marketplacepartner",
            name="kind",
            field=models.CharField(
                choices=[
                    ("hotel", "Hotel / stay"),
                    ("homestay", "Homestay"),
                    ("operator", "Tour operator"),
                    ("guide", "Local guide"),
                    ("restaurant", "Restaurant"),
                    ("transport", "Transport"),
                    ("activity", "Activity provider"),
                    ("agency", "Travel agency"),
                    ("other", "Other"),
                ],
                default="operator",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="marketplacepartner",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("under_review", "Under review"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                    ("suspended", "Suspended"),
                ],
                db_index=True,
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="marketplaceorder",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Trip basket"),
                    ("requested", "Requested"),
                    ("under_review", "Under review"),
                    ("confirmed", "Confirmed"),
                    ("cancelled", "Cancelled"),
                    ("external", "Sent to partner site"),
                ],
                db_index=True,
                default="draft",
                max_length=20,
            ),
        ),
    ]
