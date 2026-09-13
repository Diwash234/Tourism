from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tourist", "0037_page_cms_media_and_videos"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contentsection",
            name="section_type",
            field=models.CharField(
                choices=[
                    ("text", "Text"), ("heading", "Heading"), ("image", "Image"), ("gallery", "Gallery"),
                    ("cards", "Cards"), ("faq", "FAQ"), ("cta", "Call to action"), ("map", "Map"),
                    ("video", "Video"), ("audio", "Audio"), ("marquee", "Marquee"),
                    ("animation", "Animation"), ("media", "Media"), ("form", "Form"),
                    ("table", "Table"), ("figure", "Figure"), ("testimonials", "Testimonials"),
                    ("contact", "Contact"), ("breadcrumbs", "Breadcrumbs"), ("search", "Search"),
                ],
                default="text",
                max_length=30,
            ),
        ),
    ]
