"""
High-level orchestration for the AI Nepal image pipeline.

Workflow:
  Destination metadata
    -> build_prompt(...)
    -> provider.generate(...)
    -> download / store image
    -> pHash + duplicate check
    -> score (quality / authenticity / match)
    -> embedding (CLIP/TF-IDF)
    -> save DestinationImage (approved or needs_review)
    -> record ImageGenerationJob
"""
from __future__ import annotations
import base64
import logging
from typing import List, Optional

from django.db import transaction
from django.utils import timezone

from tourist.models import (
    Destination, DestinationImage, ImageEmbedding, ImageGenerationJob,
    ImageTag,
)

from .prompts import build_prompt
from .providers.base import get_provider
from .validation.scoring import score_candidate, THRESHOLDS
from .validation.dedup import compute_phash, is_near_duplicate
from .embeddings.clip_embed import embed_image, embed_text
from .storage import backend as storage_mod

logger = logging.getLogger(__name__)

# Camera/season/time variations to generate diverse images per destination.
VARIATIONS = [
    ("autumn", "sunrise", "landscape"),
    ("autumn", "day", "aerial"),
    ("spring", "day", "trekking"),
    ("winter", "sunset", "cultural"),
    ("summer", "day", "street"),
    ("spring", "sunrise", "architectural"),
]


def _fetch_image_bytes(generated) -> Optional[bytes]:
    if generated.b64:
        try:
            return base64.b64decode(generated.b64)
        except Exception:  # noqa: BLE001
            return None
    if generated.url:
        stored = storage_mod.store_from_url(generated.url)
        return stored
    return None


@transaction.atomic
def generate_for_destination(destination: Destination, num_images: int = 4,
                             provider_name: Optional[str] = None,
                             variations=None, requested_by=None,
                             force: bool = False) -> ImageGenerationJob:
    """Generate, validate and store images for one destination."""
    provider = get_provider(provider_name)
    job = ImageGenerationJob.objects.create(
        destination=destination,
        provider=provider.name,
        model=getattr(provider, "kwargs", {}).get("model", ""),
        prompt="",  # filled per-variation below
        num_images=num_images,
        status=ImageGenerationJob.Status.RUNNING,
        requested_by=requested_by,
    )

    existing_hashes = list(
        DestinationImage.objects.filter(destination=destination)
        .exclude(phash="").values_list("phash", flat=True)
    )
    created = []
    variations = variations or VARIATIONS[: max(1, num_images)]

    try:
        for season, tod, camera in variations:
            if len(created) >= num_images:
                break
            pres = build_prompt(destination, season=season, time_of_day=tod, camera_style=camera)
            job.prompt = pres.prompt
            job.negative_prompt = pres.negative_prompt
            job.season = season
            job.time_of_day = tod
            job.camera_style = camera

            try:
                results = provider.generate(
                    pres.prompt, negative_prompt=pres.negative_prompt,
                    n=1, size="1024x1024",
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("provider %s failed for %s: %s", provider.name, destination.name, exc)
                job.error_message = str(exc)
                continue

            for gen in results:
                stored = None
                phash = None
                image_bytes = None

                if gen.b64:
                    image_bytes = base64.b64decode(gen.b64)
                    try:
                        stored = storage_mod.get_storage().save(image_bytes, ext="webp")
                    except Exception:  # noqa: BLE001
                        stored = None
                elif gen.url:
                    stored = storage_mod.store_from_url(gen.url)
                    if stored:
                        # need bytes for hashing/embedding
                        import requests
                        try:
                            image_bytes = requests.get(gen.url, timeout=60).content
                        except Exception:  # noqa: BLE001
                            image_bytes = None

                if image_bytes:
                    phash = compute_phash(image_bytes)

                dup = is_near_duplicate(phash, existing_hashes) if phash else False
                scores = score_candidate(
                    destination, pres.prompt, is_duplicate=dup,
                    image_bytes=image_bytes,
                )

                image = DestinationImage(
                    destination=destination,
                    source=DestinationImage.Source.AI_GENERATED,
                    source_platform=f"ai:{provider.name}:{gen.model}",
                    external_url=(stored.url if stored else gen.url),
                    thumbnail_url=stored.thumbnail_url if stored else "",
                    caption=f"{destination.name} — {season} {tod} {camera}",
                    generation_provider=provider.name,
                    generation_model=gen.model,
                    generation_prompt=pres.prompt,
                    negative_prompt=pres.negative_prompt,
                    generation_seed=gen.seed,
                    generation_job=job,
                    phash=phash or "",
                    **scores.as_dict(),
                    verification_status=(
                        DestinationImage.ImageStatus.APPROVED
                        if (scores.accepted() and not dup) or force
                        else DestinationImage.ImageStatus.PENDING
                    ),
                    is_verified=scores.accepted() and not dup,
                    copyright_status="ai_generated",
                    license_type="AI Generated — editorial use; not a photograph of a real event",
                )
                image.save()
                existing_hashes.append(phash or "")
                created.append(image)

                # visual + text embeddings for search
                _embed_image_record(image, destination, image_bytes)

                # tags
                for tag in [season, tod, camera, "ai_generated", destination.province or ""]:
                    if tag:
                        ImageTag.objects.get_or_create(image=image, tag=tag.strip().lower())

        job.status = ImageGenerationJob.Status.SUCCEEDED if created else ImageGenerationJob.Status.FAILED
        if created:
            # set first approved as cover if none
            if not destination.cover_image:
                first = next((c for c in created if c.is_verified), created[0])
                first.is_cover = True
                first.save(update_fields=["is_cover"])
                Destination.objects.filter(pk=destination.pk).update(cover_image=first.external_url)
        job.completed_at = timezone.now()
        job.save()
    except Exception as exc:  # noqa: BLE001
        job.status = ImageGenerationJob.Status.FAILED
        job.error_message = str(exc)
        job.save()
        logger.exception("generation job failed")
        raise

    return job


def _embed_image_record(image: DestinationImage, destination: Destination, image_bytes: Optional[bytes]):
    try:
        vec = embed_image(image_bytes) if image_bytes else None
        if vec:
            ImageEmbedding.objects.update_or_create(
                image=image,
                defaults={"vector": vec, "content_type": "image",
                          "embedding_model": "clip-ViT-B-32", "dimensions": len(vec)},
            )
        # destination text embedding (upsert once)
        if not ImageEmbedding.objects.filter(destination=destination).exists():
            tvec = embed_text(
                f"{destination.name} Nepal {destination.province or ''} "
                f"{destination.category.name if destination.category_id else ''} "
                f"{destination.description or ''}"
            )
            ImageEmbedding.objects.create(
                destination=destination, content_type="destination",
                vector=tvec, embedding_model="clip-ViT-B-32", dimensions=len(tvec),
            )
    except Exception as exc:  # noqa: BLE001
        logger.debug("embedding skipped: %s", exc)


def generate_batch(destination_ids=None, num_per_destination=4, **kwargs):
    """Generate for many destinations. If destination_ids is None, do all featured places."""
    qs = Destination.objects.filter(is_active=True)
    if destination_ids:
        qs = qs.filter(id__in=destination_ids)
    jobs = []
    for dest in qs.iterator(chunk_size=100):
        # skip places that already have enough approved AI images
        have = dest.gallery.filter(source=DestinationImage.Source.AI_GENERATED,
                                   verification_status=DestinationImage.ImageStatus.APPROVED).count()
        if have >= num_per_destination:
            continue
        jobs.append(generate_for_destination(dest, num_images=num_per_destination - have, **kwargs))
    return jobs
