from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tourist", "0085_clear_placeholder_hospital_phones")]

    operations = [
        migrations.AddField(
            model_name="hospital",
            name="website",
            field=models.URLField(blank=True, max_length=600),
        ),
        migrations.AddField(
            model_name="policestation",
            name="website",
            field=models.URLField(blank=True, max_length=600),
        ),
        migrations.AddField(
            model_name="osmessentialservice",
            name="website",
            field=models.URLField(blank=True, max_length=600),
        ),
    ]
