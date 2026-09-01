from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tourist", "0034_seed_complete_cms_catalog"),
    ]

    operations = [
        migrations.AddField(
            model_name="managedpage",
            name="seo_title",
            field=models.CharField(blank=True, help_text="Optional search-result title. Blank uses the page title.", max_length=70),
        ),
        migrations.AddField(
            model_name="managedpage",
            name="og_image_url",
            field=models.URLField(blank=True, max_length=600),
        ),
        migrations.AddField(
            model_name="managedpage",
            name="search_visible",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="contentsection",
            name="section_type",
            field=models.CharField(
                choices=[
                    ("text", "Text"),
                    ("heading", "Heading"),
                    ("image", "Image"),
                    ("gallery", "Gallery"),
                    ("cards", "Cards"),
                    ("faq", "FAQ"),
                    ("cta", "Call to action"),
                    ("map", "Map"),
                ],
                default="text",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="contentsection",
            name="is_reusable",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="destinationimage",
            name="crop_box",
            field=models.JSONField(blank=True, default=dict, help_text='Optional focal crop as {"x":0,"y":0,"w":100,"h":100} percentages.'),
        ),
    ]
