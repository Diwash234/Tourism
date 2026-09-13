from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tourist", "0041_marketplace_partner_desk"),
    ]

    operations = [
        migrations.AddField(
            model_name="hospital",
            name="is_archived",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="policestation",
            name="is_archived",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="osmessentialservice",
            name="is_archived",
            field=models.BooleanField(default=False),
        ),
    ]
