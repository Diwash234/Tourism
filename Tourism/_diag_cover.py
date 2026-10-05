import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
django.setup()

from django.db.models import Count  # noqa: E402

from tourist.models import Destination, DestinationImage  # noqa: E402

total_rows = DestinationImage.objects.count()
print("gallery rows:", total_rows)

with_ext = DestinationImage.objects.exclude(external_url="").exclude(external_url__isnull=True)
print("gallery rows with external_url:", with_ext.count())
print("gallery rows with local file only:",
      DestinationImage.objects.filter(external_url="").count())

ext_stats = list(
    with_ext.values("external_url")
    .annotate(d=Count("destination_id", distinct=True))
    .values_list("d", flat=True)
)
print("distinct external_urls:", len(ext_stats))
print("  used by 1 destination:", sum(1 for d in ext_stats if d == 1))
print("  used by 2 destinations:", sum(1 for d in ext_stats if d == 2))
print("  used by 3+ destinations:", sum(1 for d in ext_stats if d >= 3))

shared_urls = set(
    with_ext.values("external_url")
    .annotate(d=Count("destination_id", distinct=True))
    .filter(d__gte=3)
    .values_list("external_url", flat=True)
)
print("shared (3+) external urls:", len(shared_urls))

# Per destination: does it own at least one gallery row nobody else uses?
own_rows = (
    DestinationImage.objects.exclude(external_url="").exclude(external_url__in=shared_urls)
    .values("destination_id")
    .annotate(n=Count("id"))
)
dests_with_own = {r["destination_id"] for r in own_rows if r["destination_id"]}
dests_with_local = set(
    DestinationImage.objects.filter(external_url="")
    .exclude(destination_id__isnull=True)
    .values_list("destination_id", flat=True).distinct()
)
covered = dests_with_own | dests_with_local
print("destinations with >=1 non-shared gallery row:", len(dests_with_own))
print("destinations with >=1 local-file gallery row:", len(dests_with_local))
print("destinations with ANY usable own row:", len(covered))

# cross-check against shared-cover destinations
shared_cover_dests = set(
    Destination.objects.exclude(cover_image="")
    .values("cover_image")
    .annotate(n=Count("id"))
    .filter(n__gte=3)
    .values_list("cover_image", flat=True)
)
n_shared_cover_dests = Destination.objects.filter(cover_image__in=shared_cover_dests).count()
print("destinations whose cover is shared 3+:", n_shared_cover_dests)
print("of those, with >=1 usable own gallery row:",
      Destination.objects.filter(cover_image__in=shared_cover_dests, id__in=covered).count())
