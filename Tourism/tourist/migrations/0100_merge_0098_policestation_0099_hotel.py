from django.db import migrations


class Migration(migrations.Migration):
    """Reconcile the two parallel 0098/0099 migration branches.

    0098_policestation_district and 0099_hotel_coordinate_retrieved_at_and_more
    both describe legitimate schema changes that landed independently. This
    empty merge migration makes the migration graph a single linear leaf
    without rewriting or deleting migrations that may already be applied.
    """

    dependencies = [
        ("tourist", "0098_policestation_district"),
        ("tourist", "0099_hotel_coordinate_retrieved_at_and_more"),
    ]

    operations = []
