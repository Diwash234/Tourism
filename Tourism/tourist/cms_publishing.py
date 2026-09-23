"""Snapshot-based draft/publish isolation for CMS sections.

The public site serves ``ContentSection.published_snapshot`` when present;
edits touch the live (draft) fields, and only an explicit Publish (or a due
scheduled publish) copies them into the snapshot. Sections that predate the
snapshot system fall back to their live fields, so existing content keeps
working untouched.
"""


def section_snapshot(section):
    """Frozen, public-safe representation of a section + its visible blocks."""
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
            for b in section.blocks.filter(is_visible=True).order_by("position", "id")
        ],
    }


def sync_published_snapshot(section):
    """Copy the current live fields into the public snapshot."""
    section.published_snapshot = section_snapshot(section)
    section.save(update_fields=["published_snapshot", "updated_at"])
    return section.published_snapshot


def publish_due_sections(now):
    """Flip scheduled sections whose time has come, refreshing snapshots."""
    from .models import ContentSection
    count = 0
    for section in ContentSection.objects.filter(status="scheduled", scheduled_publish_at__lte=now):
        section.status = "published"
        section.published_at = now
        section.scheduled_publish_at = None
        section.save(update_fields=["status", "published_at", "scheduled_publish_at", "updated_at"])
        sync_published_snapshot(section)
        count += 1
    return count
