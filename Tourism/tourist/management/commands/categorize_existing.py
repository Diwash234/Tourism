"""
Recategorize generic attractions/information/artwork/blank-category
destinations into the 36-category taxonomy using keyword heuristics.
Idempotent: only touches destinations whose category is one of the
'generic' buckets (attraction, information, artwork, gallery, '').
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models import Q

from tourist.models import Destination, Category


GENERIC_SLUGS = ["attraction", "information", "artwork", "gallery", ""]

# keyword (lowercased) -> category slug
RULES = [
    # temples / pilgrimage / buddhist-sites / spiritual-wellness
    ("temple", "temples"),
    ("mandir", "temples"),
    ("stupa", "buddhist-sites"),
    ("gompa", "buddhist-sites"),
    ("monastery", "buddhist-sites"),
    ("vihar", "buddhist-sites"),
    ("gumba", "buddhist-sites"),
    ("church", "pilgrimage"),
    ("mosque", "pilgrimage"),
    ("masjid", "pilgrimage"),
    ("dham", "pilgrimage"),
    ("tirtha", "pilgrimage"),
    ("pilgrim", "pilgrimage"),
    ("muktinath", "pilgrimage"),
    ("pashupati", "pilgrimage"),
    ("manakamana", "pilgrimage"),
    ("pathibhara", "pilgrimage"),
    ("lumbini", "buddhist-sites"),
    ("boudha", "buddhist-sites"),
    ("swayambhu", "buddhist-sites"),
    ("janaki", "pilgrimage"),
    ("doleshwor", "pilgrimage"),
    ("chandragiri bhaleshwor", "pilgrimage"),
    ("ashram", "spiritual-wellness"),
    ("meditation", "spiritual-wellness"),
    ("yoga", "spiritual-wellness"),
    # heritage
    ("durbar square", "heritage"),
    ("darbar square", "heritage"),
    ("durbar", "heritage"),
    ("palace", "heritage"),
    ("museum", "museums"),
    ("heritage", "heritage"),
    ("newar", "heritage"),
    ("stone tap", "heritage"),
    ("darbar", "heritage"),
    ("dharahara", "heritage"),
    ("basantapur", "heritage"),
    ("narayanhiti", "heritage"),
    ("rani mahal", "heritage"),
    ("gorkha durbar", "heritage"),
    ("nuwakot durbar", "heritage"),
    # mountains / trekking / viewpoints / winter / natural-wonders
    ("himala", "mountains"),
    ("himal", "mountains"),
    ("peak", "mountains"),
    ("mountain", "mountains"),
    ("dada", "viewpoints"),
    ("hill station", "viewpoints"),
    ("viewpoint", "viewpoints"),
    ("view tower", "viewpoints"),
    ("poon hill", "viewpoints"),
    ("kala patthar", "viewpoints"),
    ("chandragiri", "viewpoints"),
    ("phulchowki", "viewpoints"),
    ("nagarkot", "viewpoints"),
    ("sarangkot", "viewpoints"),
    ("trek", "trekking"),
    ("base camp", "trekking"),
    ("circuit", "trekking"),
    ("pass", "trekking"),
    ("la ", "trekking"),
    ("trekking route", "trekking"),
    ("everest base camp", "trekking"),
    ("annapurna base camp", "trekking"),
    ("annapurna circuit", "trekking"),
    ("langtang valley", "trekking"),
    ("upper mustang", "trekking"),
    ("manaslu circuit", "trekking"),
    ("snow", "winter"),
    ("ski", "winter"),
    ("kalinchowk", "winter"),
    ("gosaikunda", "natural-wonders"),
    ("tilicho", "natural-wonders"),
    ("rara", "natural-wonders"),
    ("phoksundo", "natural-wonders"),
    ("gorge", "natural-wonders"),
    ("valley", "valleys"),
    ("khola valley", "valleys"),
    ("pokhara valley", "valleys"),
    ("kathmandu valley", "valleys"),
    ("hill", "hills"),
    # lakes / rivers / waterfalls / hot-springs
    ("lake", "lakes"),
    ("tal", "lakes"),
    ("pokhari", "lakes"),
    ("kunda", "lakes"),
    ("phewa", "lakes"),
    ("fewa", "lakes"),
    ("begnas", "lakes"),
    ("rara", "lakes"),
    ("gokyo", "lakes"),
    ("gosaikunda", "lakes"),
    ("tilicho", "lakes"),
    ("phoksundo", "lakes"),
    ("shey phoksundo", "lakes"),
    ("indra sarovar", "lakes"),
    ("kulekhani", "lakes"),
    ("river", "rivers"),
    ("khola", "rivers"),
    ("kosi", "rivers"),
    ("koshi", "rivers"),
    ("karnali", "rivers"),
    ("trishuli", "rivers"),
    ("gandaki", "rivers"),
    ("kaligandaki", "rivers"),
    ("narayani", "rivers"),
    ("seti", "rivers"),
    ("bhote koshi", "rivers"),
    ("sunkoshi", "rivers"),
    ("waterfall", "waterfalls"),
    ("falls", "waterfalls"),
    ("jharana", "waterfalls"),
    ("chhango", "waterfalls"),
    ("davis falls", "waterfalls"),
    ("patale chhango", "waterfalls"),
    ("hot spring", "hot-springs"),
    ("hotspring", "hot-springs"),
    ("tatopani", "hot-springs"),
    # wildlife / forests / bird-watching / national parks
    ("national park", "wildlife"),
    ("wildlife", "wildlife"),
    ("safari", "wildlife"),
    ("reserve", "wildlife"),
    ("chitwan", "wildlife"),
    ("bardiya", "wildlife"),
    ("sagarmatha national park", "wildlife"),
    ("khaptad", "wildlife"),
    ("shuklaphanta", "wildlife"),
    ("parsa wildlife", "wildlife"),
    ("koshi tappu", "bird-watching"),
    ("bird", "bird-watching"),
    ("zoo", "wildlife"),
    ("forest", "forests"),
    ("community forest", "forests"),
    ("conservation area", "eco-tourism"),
    ("rhododendron", "forests"),
    # caves
    ("cave", "caves"),
    ("gupha", "caves"),
    ("gumpha", "caves"),
    ("mahadev cave", "caves"),
    ("mahendra cave", "caves"),
    ("gupteshwor", "caves"),
    ("chamere", "caves"),
    ("halesi", "caves"),
    ("siddha cave", "caves"),
    # villages / culture / festivals / food / shopping / cities
    ("bazaar", "shopping"),
    ("bazar", "shopping"),
    ("market", "shopping"),
    ("mela", "festivals"),
    ("festival", "festivals"),
    ("jatra", "festivals"),
    ("maha shivaratri", "festivals"),
    ("dashain", "festivals"),
    ("tihar", "festivals"),
    ("indra jatra", "festivals"),
    ("ghode jatra", "festivals"),
    ("holi", "festivals"),
    ("museum", "museums"),
    ("art gallery", "museums"),
    ("food", "food-culinary"),
    ("momo", "food-culinary"),
    ("newari", "food-culinary"),
    ("thakali", "food-culinary"),
    ("restaurant", "food-culinary"),
    ("dhaba", "food-culinary"),
    ("street food", "food-culinary"),
    ("kathmandu", "cities"),
    ("pokhara", "cities"),
    ("lalitpur", "cities"),
    ("patan", "cities"),
    ("bhaktapur", "cities"),
    ("biratnagar", "cities"),
    ("birgunj", "cities"),
    ("nepalgunj", "cities"),
    ("dharan", "cities"),
    ("butwal", "cities"),
    ("hetauda", "cities"),
    ("janakpur", "cities"),
    ("bharatpur", "cities"),
    ("siddharthanagar", "cities"),
    ("bhairahawa", "cities"),
    ("dhangadhi", "cities"),
    ("tansen", "villages"),
    ("bandipur", "villages"),
    ("ghandruk", "villages"),
    ("ghale gaun", "villages"),
    ("sirubari", "villages"),
    ("dhampus", "villages"),
    ("chitlang", "villages"),
    ("village", "villages"),
    ("gaun", "villages"),
    ("homestay village", "villages"),
    ("ethnic", "culture"),
    ("tharu", "culture"),
    ("sherpa", "culture"),
    ("tamang", "culture"),
    ("gurung", "culture"),
    ("magar", "culture"),
    ("newar", "culture"),
    # adventure / air-sports / water-sports / cycling / camping
    ("paragliding", "air-sports"),
    ("zip flyer", "air-sports"),
    ("bungee", "air-sports"),
    ("skydiv", "air-sports"),
    ("ultralight", "air-sports"),
    ("cable car", "air-sports"),
    ("ropeway", "air-sports"),
    ("rafting", "water-sports"),
    ("kayak", "water-sports"),
    ("canyoning", "water-sports"),
    ("boating", "water-sports"),
    ("swimming", "water-sports"),
    ("canoe", "water-sports"),
    ("fishing", "water-sports"),
    ("bouldering", "adventure"),
    ("climbing", "adventure"),
    ("rock climb", "adventure"),
    ("mountain bike", "cycling"),
    ("cycling", "cycling"),
    ("biking", "cycling"),
    ("camping", "camping"),
    ("camp", "camping"),
    ("tents", "camping"),
    ("tea garden", "tea-coffee"),
    ("tea estate", "tea-coffee"),
    ("kanyam", "tea-coffee"),
    ("ilam", "tea-coffee"),
    ("coffee estate", "tea-coffee"),
    ("organic farm", "agriculture"),
    ("farm stay", "agriculture"),
    ("agriculture", "agriculture"),
    ("farm", "agriculture"),
    ("scenic drive", "scenic-routes"),
    ("highway", "scenic-routes"),
    ("road", "scenic-routes"),
    ("prithvi highway", "scenic-routes"),
    ("eco", "eco-tourism"),
    ("community tourism", "eco-tourism"),
    ("homestay", "eco-tourism"),
]


def match_category(name: str, desc: str) -> str | None:
    blob = f"{name} {desc}".lower()
    for kw, slug in RULES:
        if kw in blob:
            return slug
    return None


class Command(BaseCommand):
    help = "Recategorize generic attractions into the 36-category taxonomy using keyword heuristics."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=0)

    def handle(self, *args, **options):
        dry = options["dry_run"]
        limit = int(options["limit"]) or 0

        cat_cache = {c.slug: c for c in Category.objects.all()}

        qs = Destination.objects.filter(category__slug__in=GENERIC_SLUGS)
        # also include destinations whose category is the empty-string slug
        blank_qs = Destination.objects.filter(category__isnull=True)
        qs = (qs | blank_qs).distinct()

        if limit:
            qs = qs[:limit]

        moved = 0
        per_cat: dict[str, int] = {}
        unmatched = 0

        for dest in qs.iterator():
            slug = match_category(dest.name or "",
                                 f"{dest.short_description or ''} {dest.description or ''}")
            if not slug:
                unmatched += 1
                continue
            cat = cat_cache.get(slug)
            if not cat:
                self.stderr.write(f"  category slug not found: {slug}")
                continue
            if not dry:
                Destination.objects.filter(pk=dest.pk).update(category=cat)
            moved += 1
            per_cat[slug] = per_cat.get(slug, 0) + 1

        self.stdout.write(self.style.SUCCESS(
            f"{'[DRY RUN] ' if dry else ''}Recategorized {moved} generic destinations. Unmatched: {unmatched}."))
        for slug in sorted(per_cat):
            self.stdout.write(f"  {slug:25s} -> +{per_cat[slug]}")

        # Final counts for the 36 taxonomy categories
        target_slugs = ['mountains','hills','valleys','trekking','temples','buddhist-sites','heritage','lakes',
                        'rivers','waterfalls','forests','wildlife','bird-watching','caves','viewpoints','villages',
                        'culture','festivals','spiritual-wellness','adventure','air-sports','water-sports',
                        'agriculture','tea-coffee','camping','cycling','winter','hot-springs','cities','shopping',
                        'food-culinary','scenic-routes','eco-tourism','museums','natural-wonders','pilgrimage']
        self.stdout.write("\n  Final taxonomy counts:")
        for s in target_slugs:
            c = cat_cache.get(s)
            n = Destination.objects.filter(category=c).count() if c else -1
            self.stdout.write(f"   {s:25s} {n}")
