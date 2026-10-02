from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0003_hotelreview_moderated_at_hotelreview_moderated_by_and_more"),
    ]
    operations = [
        migrations.AlterField(
            model_name="booking",
            name="check_in",
            field=models.DateField(db_index=True),
        ),
        migrations.AlterField(
            model_name="booking",
            name="check_out",
            field=models.DateField(db_index=True),
        ),
    ]
