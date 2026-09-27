"""Remove exact duplicate hero slides.

The public seed carried two copies of each default slide (ids 1-6 and 7-12,
same title, link, text and image), so the home carousel showed every slide
twice ("1 / 12"). Keep the lowest id of each identical group; slides that
differ in any visible field are left alone.
"""
from django.db import migrations

VISIBLE = ("title", "kicker", "subtitle", "tagline", "link_slug", "image", "image_url", "local_image", "order")


def dedupe(apps, schema_editor):
    HeroSlide = apps.get_model("tourist", "HeroSlide")
    seen = set()
    for slide in HeroSlide.objects.order_by("id"):
        key = tuple(str(getattr(slide, f) or "").strip().lower() for f in VISIBLE)
        if key in seen:
            slide.delete()
        else:
            seen.add(key)


class Migration(migrations.Migration):
    dependencies = [("tourist", "0088_page_meta_descriptions")]
    operations = [migrations.RunPython(dedupe, migrations.RunPython.noop)]
