"""
Generate AI images for Nepal tourist destinations.

Usage:
    # Generate for one destination by id or slug
    python manage.py generate_destination_images --destination pashupatinath-temple --num 4

    # Generate for all major tourist destinations (the seed list)
    python manage.py generate_destination_images --seed --num 4

    # Generate for every destination in the database
    python manage.py generate_destination_images --all --num 2

    # Use a specific provider (openai|stability|google|flux|pollinations)
    python manage.py generate_destination_images --seed --provider openai
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination
from tourist.services.ai_images.pipeline import generate_for_destination
from tourist.services.ai_images.providers.base import available_providers

# Curated seed of major Nepal tourist destinations (matched by name/slug).
SEED_DESTINATIONS = [
    "Pashupatinath", "Boudhanath", "Swayambhunath", "Kathmandu Durbar Square",
    "Patan Durbar Square", "Bhaktapur Durbar Square", "Phewa Lake", "Sarangkot",
    "Davis Falls", "World Peace Pagoda", "Begnas Lake", "Annapurna Base Camp",
    "Everest Base Camp", "Mount Everest", "Annapurna Circuit", "Poon Hill",
    "Langtang", "Manaslu", "Mustang", "Muktinath", "Chitwan National Park",
    "Lumbini", "Janakpur", "Nagarkot", "Bandipur", "Ghandruk", "Dhampus",
    "Rara Lake", "Tilicho Lake", "Gosaikunda", "Mardi Himal", "Manang",
    "Namche Bazaar", "Tengboche", "Lukla", "Sagarmatha National Park",
    "Changu Narayan", "Nyatapola", "Kirtipur", "Ilam", "Khaptad",
    "Shey Phoksundo", "Bardiya National Park", "Koshi Tappu", "Janaki Mandir",
    "Bahunthan", "Waling", "Syangja", "Pokhara",
]


class Command(BaseCommand):
    help = "Generate AI images for Nepal destinations."

    def add_arguments(self, parser):
        parser.add_argument("--destination", help="Destination id or slug")
        parser.add_argument("--num", type=int, default=4)
        parser.add_argument("--provider", default=None, help="openai|stability|google|flux|pollinations")
        parser.add_argument("--seed", action="store_true", help="Generate for the curated major-destinations seed list")
        parser.add_argument("--all", action="store_true", help="Generate for every destination")
        parser.add_argument("--force", action="store_true", help="Accept images below thresholds")
        parser.add_argument("--list-providers", action="store_true")

    def handle(self, *args, **options):
        if options["list_providers"]:
            self.stdout.write("Available/configured providers: " + ", ".join(available_providers()))
            return

        if options["destination"]:
            val = options["destination"]
            dest = Destination.objects.filter(pk=val).first() if val.isdigit() else \
                Destination.objects.filter(slug=val).first() or \
                Destination.objects.filter(name__icontains=val).first()
            if not dest:
                raise CommandError(f"Destination '{val}' not found")
            self._run(dest, options)
            return

        if options["seed"]:
            qs = []
            for name in SEED_DESTINATIONS:
                d = Destination.objects.filter(name__icontains=name).first()
                if d and d not in qs:
                    qs.append(d)
            self.stdout.write(f"Seed list matched {len(qs)} destinations")
        elif options["all"]:
            qs = list(Destination.objects.filter(is_active=True))
        else:
            self.stderr.write("Specify --destination, --seed, or --all (or --list-providers)")
            return

        for i, dest in enumerate(qs, 1):
            self.stdout.write(f"[{i}/{len(qs)}] {dest.name}")
            try:
                self._run(dest, options)
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f"  failed: {exc}")

    def _run(self, dest, options):
        job = generate_for_destination(
            dest, num_images=options["num"],
            provider_name=options["provider"], force=options["force"],
        )
        self.stdout.write(self.style.SUCCESS(
            f"  -> {job.status}: {job.outputs.count()} images"
            + (f" (error: {job.error_message[:120]})" if job.error_message else "")
        ))
