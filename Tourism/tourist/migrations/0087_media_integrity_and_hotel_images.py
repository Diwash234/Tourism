from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("tourist", "0086_hospital_police_website")]

    operations = [
        migrations.AlterField(
            model_name="destinationimage", name="verification_status",
            field=models.CharField(choices=[("pending","Needs Review"),("approved","Approved"),("rejected","Rejected")], default="pending", max_length=20),
        ),
        migrations.AlterField(
            model_name="destinationimage", name="is_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(model_name="destinationimage", name="match_status", field=models.CharField(
            choices=[("verified_entity","Verified entity image"),("area_context","Area/context image"),("unverified","Unverified image"),("unavailable","Image unavailable")],
            db_index=True, default="unverified", max_length=24)),
        migrations.AddField(model_name="destinationimage", name="verification_note", field=models.TextField(blank=True)),
        migrations.AddField(model_name="destinationimage", name="verified_source_url", field=models.URLField(blank=True, default="", max_length=600)),
        migrations.CreateModel(
            name="HotelImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("image", models.ImageField(blank=True, null=True, upload_to="hotels/gallery/")),
                ("external_url", models.URLField(blank=True, default="", max_length=600)),
                ("source_url", models.URLField(blank=True, default="", max_length=600)),
                ("photographer", models.CharField(blank=True, default="", max_length=150)),
                ("license_type", models.CharField(blank=True, default="", max_length=100)),
                ("caption", models.CharField(blank=True, default="", max_length=200)),
                ("alt_text", models.CharField(blank=True, default="", max_length=255)),
                ("match_status", models.CharField(choices=[("verified_entity","Verified hotel image"),("area_context","Area/context image"),("unverified","Unverified image"),("unavailable","Image unavailable")], db_index=True, default="unverified", max_length=24)),
                ("verification_note", models.TextField(blank=True)),
                ("is_cover", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("superseded_at", models.DateTimeField(blank=True, null=True)),
                ("hotel", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="gallery", to="tourist.hotel")),
            ],
            options={"ordering": ["-is_cover", "-is_active", "-created_at"]},
        ),
        migrations.AddIndex(model_name="hotelimage", index=models.Index(fields=["hotel","is_active"], name="hotelimg_hotel_active_idx")),
    ]
