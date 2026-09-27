"""Join the published main migration line with the Nepal Yatra handoff line.

Main already shipped ``0085_clear_placeholder_hospital_phones`` while the
handoff independently shipped a migration numbered 0085.  Both migrations
remain intact: the handoff migration is named
``0085_handoff_clear_missing_marker_phones`` and this no-op merge records that
both lines have been applied before later releases proceed.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("tourist", "0085_clear_placeholder_hospital_phones"),
        ("tourist", "0091_cms_cover_every_page_route"),
    ]

    operations = []
