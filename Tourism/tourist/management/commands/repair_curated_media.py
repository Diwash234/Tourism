"""Repair a small, explicitly curated set of missing destination media.

This command is idempotent and conservative: it only creates a media row when
the named destination exists and has no existing usable external/local image.
Each URL carries source metadata; non-open sources are marked as attribution
required instead of being represented as freely licensed.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination, DestinationImage


MEDIA = [
    {
        "names": ["Kupinde Daha Lakes", "Kupinde Lake", "Kupinde Daha"],
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Kupinde_Lake_Salyan_Nepal.jpg/1280px-Kupinde_Lake_Salyan_Nepal.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Kupinde_Lake_Salyan_Nepal.jpg",
        "source": DestinationImage.Source.WIKIMEDIA,
        "platform": "Wikimedia Commons",
        "license": "CC BY-SA / verify attribution on source page",
        "copyright": "verified_reusable",
        "caption": "Kupinde Lake, Salyan, Nepal",
    },
    {
        "names": ["Guerilla Trek Heritage Trail", "Guerrilla Trek Heritage Trail", "Guerilla Trek"],
        "url": "https://gorkhapatraonline.com/storage/media/282946/padmarga.jpg",
        "source_url": "https://gorkhapatraonline.com/news/160538",
        "source": DestinationImage.Source.REFERENCE,
        "platform": "Gorkhapatra Online",
        "license": "Attribution required — verify reuse terms",
        "copyright": "source_attribution_required",
        "caption": "Guerilla Trekking Trail in western Nepal",
    },
    {
        "names": ["Ghandruk Gurung Stone Heritage Village"],
        "url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "source_url": "https://heavenhimalaya.com/attraction/ghandruk/",
        "source": DestinationImage.Source.UNSPLASH,
        "platform": "Unsplash / project source record",
        "license": "Verify reuse terms and attribution",
        "copyright": "source_attribution_required",
        "caption": "Ghandruk Gurung heritage village",
    },
    {
        "names": ["Barun Valley Wilderness Sanctuary"],
        "url": "https://upload.wikimedia.org/wikipedia/commons/e/ed/Barun_Valley_-_Nghe.jpg",
        "source_url": "https://en.wikipedia.org/wiki/Makalu",
        "source": DestinationImage.Source.WIKIMEDIA,
        "platform": "Wikimedia Commons",
        "license": "CC BY-SA / verify attribution on source page",
        "copyright": "verified_reusable",
        "caption": "Barun Valley, Makalu region",
    },
    {
        "names": ["Api Nampa Conservation Peak Reserve", "Api Nampa Conservation Area", "Api Nampa Alpine Conservation Area"],
        "url": "https://nepaltraveller.com/images/main/1748256469.sidetrackimageAPI.png",
        "source_url": "https://nepaltraveller.com/sidetrack/api-nampa-conservation-area",
        "source": DestinationImage.Source.REFERENCE,
        "platform": "Nepal Traveller",
        "license": "Attribution required — verify reuse terms",
        "copyright": "source_attribution_required",
        "caption": "Api Nampa Conservation Area",
    },
    {
        "names": ["Bhaktapur Durbar Square & Nyatapola Temple", "Bhaktapur Durbar Square and Nyatapola Temple"],
        "url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "source_url": "",
        "source": DestinationImage.Source.UNSPLASH,
        "platform": "Project seed source",
        "license": "Verify reuse terms and attribution",
        "copyright": "source_attribution_required",
        "caption": "Bhaktapur Durbar Square and Nyatapola Temple",
    },
]


class Command(BaseCommand):
    help = "Repair explicitly curated missing destination media without overwriting existing images."

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        missing = 0

        for item in MEDIA:
            destination = None
            for name in item["names"]:
                destination = Destination.objects.filter(name__iexact=name).first()
                if destination:
                    break
            if destination is None:
                # Also tolerate punctuation differences in imported names.
                for name in item["names"]:
                    destination = Destination.objects.filter(name__icontains=name).first()
                    if destination:
                        break

            if destination is None:
                missing += 1
                self.stdout.write(self.style.WARNING(
                    f"media repair: destination not found: {item['names'][0]}"
                ))
                continue

            has_media = destination.gallery.filter(
                verification_status__in=[
                    DestinationImage.ImageStatus.APPROVED,
                    DestinationImage.ImageStatus.PENDING,
                ],
            ).filter(
                external_url__gt="",
            ).exists() or destination.gallery.filter(image__isnull=False).exclude(image="").exists()

            if has_media:
                skipped += 1
                continue

            DestinationImage.objects.create(
                destination=destination,
                external_url=item["url"],
                source=item["source"],
                source_url=item["source_url"] or None,
                source_platform=item["platform"],
                license_type=item["license"],
                copyright_status=item["copyright"],
                image_category="attraction",
                caption=item["caption"],
                alt_text=item["caption"],
                is_cover=True,
                ordering=0,
                verification_status=DestinationImage.ImageStatus.PENDING,
            )
            created += 1
            self.stdout.write(f"media repair: added {destination.name}")

        self.stdout.write(self.style.SUCCESS(
            f"media repair complete: created={created}, skipped_existing={skipped}, not_found={missing}"
        ))
