# Data migration: freeze the CURRENT content of every published section into
# its published_snapshot. Content is copied verbatim — nothing visible changes.
# From this point on, edits to a published section are drafts until Publish.
from django.db import migrations


def _snapshot(section, blocks):
    return {
        "title": section.title,
        "subtitle": section.subtitle,
        "body": section.body,
        "image_url": section.image_url,
        "cta_text": section.cta_text,
        "cta_url": section.cta_url,
        "icon": section.icon,
        "section_type": section.section_type,
        "layout_variant": section.layout_variant,
        "config": section.config if isinstance(section.config, dict) else {},
        "display_order": section.display_order,
        "blocks": [
            {"id": b.id, "block_type": b.block_type, "title": b.title,
             "position": b.position, "data": b.data, "is_visible": True}
            for b in blocks
        ],
    }


def backfill(apps, schema_editor):
    ContentSection = apps.get_model("tourist", "ContentSection")
    ContentBlock = apps.get_model("tourist", "ContentBlock")
    for section in ContentSection.objects.filter(status="published"):
        blocks = ContentBlock.objects.filter(section=section, is_visible=True).order_by("position", "id")
        section.published_snapshot = _snapshot(section, list(blocks))
        section.save(update_fields=["published_snapshot"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("tourist", "0064_contentsection_published_snapshot")]
    operations = [migrations.RunPython(backfill, noop)]
