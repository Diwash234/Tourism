from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tourist", "0086_hospital_police_website"),
    ]

    operations = [
        migrations.AddField(
            model_name="hotel",
            name="website",
            field=models.URLField(blank=True, default=""),
        ),
    ]
