"""
Backfill text/image embeddings for semantic search.

Usage:
    python manage.py backfill_embeddings
    python manage.py backfill_embeddings --images   # only images
    python manage.py backfill_embeddings --destinations  # only destination text
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from tourist.models import Destination, DestinationImage, ImageEmbedding
from tourist.services.ai_images.embeddings.clip_embed import embed_text, embed_image


class Command(BaseCommand):
    help = "Generate CLIP/TF-IDF embeddings for destinations and images."

    def add_arguments(self, parser):
        parser.add_argument("--images", action="store_true")
        parser.add_argument("--destinations", action="store_true")

    def handle(self, *args, **options):
        do_all = not (options["images"] or options["destinations"])

        if do_all or options["destinations"]:
            self.stdout.write("Embedding destination text...")
            n = 0
            for d in Destination.objects.filter(is_active=True).iterator(chunk_size=200):
                if ImageEmbedding.objects.filter(destination=d).exists():
                    continue
                text = (
                    f"{d.name} Nepal {d.province or ''} {d.district or ''} "
                    f"{d.category.name if d.category_id else ''} {d.description or ''}"
                )
                vec = embed_text(text)
                ImageEmbedding.objects.create(
                    destination=d, content_type="destination",
                    vector=vec, embedding_model="clip-ViT-B-32", dimensions=len(vec),
                )
                n += 1
                if n % 100 == 0:
                    self.stdout.write(f"  {n} destinations...")
            self.stdout.write(self.style.SUCCESS(f"Embedded {n} destinations"))

        if do_all or options["images"]:
            self.stdout.write("Embedding images (local files only)...")
            n = 0
            for img in DestinationImage.objects.exclude(image="").exclude(image__isnull=True).iterator(chunk_size=200):
                if ImageEmbedding.objects.filter(image=img).exists():
                    continue
                try:
                    with img.image.open("rb") as f:
                        vec = embed_image(f.read())
                except Exception:  # noqa: BLE001
                    vec = None
                if vec:
                    ImageEmbedding.objects.update_or_create(
                        image=img,
                        defaults={"vector": vec, "content_type": "image",
                                  "embedding_model": "clip-ViT-B-32", "dimensions": len(vec)},
                    )
                    n += 1
            self.stdout.write(self.style.SUCCESS(f"Embedded {n} images"))
