"""
REST API for the AI Nepal image dataset platform.

Endpoints:
  GET  /api/ai-images/destinations/            list destinations
  GET  /api/ai-images/destinations/<id>/       destination detail
  GET  /api/ai-images/destinations/<id>/images list images (with scores)
  POST /api/ai-images/generate/                generate images for a destination (admin)
  POST /api/ai-images/images/<id>/validate/    re-score / validate
  POST /api/ai-images/images/<id>/match/       image-to-destination match
  POST /api/ai-images/images/<id>/moderate/    approve / reject
  GET  /api/ai-images/search/?q=...            semantic + metadata search
  GET  /api/ai-images/jobs/                    generation jobs
"""
from __future__ import annotations
from django.db.models import Q, Count
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from tourist.models import (
    Destination, DestinationImage, ImageGenerationJob, ImageEmbedding, ImageTag,
)
from tourist.permissions import IsAdminOrStaff
from .pipeline import generate_for_destination
from .validation.scoring import score_candidate, THRESHOLDS
from .embeddings.clip_embed import embed_text, cosine


def _operator_can(request, action="view"):
    """Keep the public AI-image surface read-only and capability-scoped."""
    from tourist.views_admin import _has_capability
    return _has_capability(request, "images", action)


def _require_operator(request, action):
    from rest_framework.exceptions import PermissionDenied
    if not _operator_can(request, action):
        raise PermissionDenied(f"Missing images.{action} capability")


def _scope_destinations(request, queryset):
    from tourist.views_admin import _is_platform_admin, _scope_destination_queryset
    if _operator_can(request) and not _is_platform_admin(request.user):
        return _scope_destination_queryset(queryset, request.user)
    return queryset


def _safe_image_url(image):
    if image.external_url:
        return image.external_url
    try:
        return image.image.url if image.image else ""
    except (ValueError, AttributeError):
        return ""


def _img_dict(img: DestinationImage) -> dict:
    return {
        "id": img.id,
        "url": _safe_image_url(img),
        "thumbnail_url": img.thumbnail_url,
        "caption": img.caption,
        "source": img.source,
        "provider": img.generation_provider,
        "model": img.generation_model,
        "prompt": img.generation_prompt,
        "is_cover": img.is_cover,
        "quality_score": img.quality_score,
        "realism_score": img.realism_score,
        "authenticity_score": img.authenticity_score,
        "destination_match_score": img.destination_match_score,
        "duplicate_score": img.duplicate_score,
        "overall_score": img.overall_score,
        "status": img.verification_status,
        "tags": [t.tag for t in img.tags.all()],
        "created_at": img.created_at,
    }


def _dest_dict(d: Destination) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "slug": d.slug,
        "province": d.province,
        "district": d.district,
        "category": d.category.name if d.category_id else None,
        "latitude": float(d.latitude) if d.latitude else None,
        "longitude": float(d.longitude) if d.longitude else None,
        "description": (d.description or "")[:400],
        "cover_image": str(d.cover_image) if d.cover_image else None,
        "image_count": d.gallery.filter(
            verification_status=DestinationImage.ImageStatus.APPROVED,
            is_verified=True,
        ).count(),
    }


class DestinationListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        qs = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
        ).select_related("category")
        q = request.query_params.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(district__icontains=q) | Q(province__icontains=q))
        qs = _scope_destinations(request, qs).order_by("name")
        count = qs.count()
        qs = qs[:200]
        return Response({"results": [_dest_dict(d) for d in qs], "count": count})


class DestinationDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        d = Destination.objects.filter(
            pk=pk, is_active=True, status=Destination.SubmissionStatus.APPROVED,
        ).select_related("category").first()
        if not d:
            return Response({"detail": "not found"}, status=404)
        if _operator_can(request) and getattr(request.user, "is_authenticated", False):
            from tourist.views_admin import _is_platform_admin, _require_destination_access
            if not _is_platform_admin(request.user):
                try:
                    _require_destination_access(request, d, "images", "view")
                except Exception:
                    return Response({"detail": "not found"}, status=404)
        data = _dest_dict(d)
        images = d.gallery.all()
        if not _operator_can(request):
            images = images.filter(
                verification_status=DestinationImage.ImageStatus.APPROVED,
                is_verified=True,
            )
        data["images"] = [_img_dict(i) for i in images.order_by("-is_cover", "-overall_score", "-created_at")[:100]]
        return Response(data)


class DestinationImagesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        d = Destination.objects.filter(
            pk=pk, is_active=True, status=Destination.SubmissionStatus.APPROVED,
        ).first()
        if not d:
            return Response({"detail": "not found"}, status=404)
        if _operator_can(request) and getattr(request.user, "is_authenticated", False):
            from tourist.views_admin import _is_platform_admin
            if not _is_platform_admin(request.user):
                try:
                    from tourist.views_admin import _require_destination_access
                    _require_destination_access(request, d, "images", "view")
                except Exception:
                    return Response({"detail": "not found"}, status=404)
        imgs = d.gallery.all()
        if not _operator_can(request):
            imgs = imgs.filter(
                verification_status=DestinationImage.ImageStatus.APPROVED,
                is_verified=True,
            )
        imgs = imgs.order_by("-is_cover", "-overall_score", "-created_at")
        return Response({"destination": d.name, "count": imgs.count(),
                         "images": [_img_dict(i) for i in imgs]})


class GenerateImagesView(APIView):
    """Admin/staff only: trigger AI generation for a destination."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        _require_operator(request, "add")
        dest_id = request.data.get("destination_id")
        try:
            num = max(1, min(20, int(request.data.get("num_images", 4))))
        except (TypeError, ValueError):
            return Response({"detail": "num_images must be between 1 and 20."}, status=400)
        provider = request.data.get("provider")
        force = bool(request.data.get("force", False))
        d = Destination.objects.filter(pk=dest_id).first()
        if not d:
            return Response({"detail": "destination not found"}, status=404)
        from tourist.views_admin import _is_platform_admin, _require_destination_access
        if not _is_platform_admin(request.user):
            _require_destination_access(request, d, "images", "add")
        if force and not _operator_can(request, "approve"):
            return Response({"detail": "force approval requires images.approve capability."}, status=403)
        job = generate_for_destination(
            d, num_images=num, provider_name=provider,
            requested_by=request.user if request.user.is_authenticated else None,
            force=force,
        )
        return Response({
            "job_id": job.id, "status": job.status,
            "created": job.outputs.count(),
            "error": job.error_message,
        }, status=status.HTTP_201_CREATED if job.status == "succeeded" else status.HTTP_202_ACCEPTED)


class ImageModerateView(APIView):
    permission_classes = [IsAdminOrStaff]

    def post(self, request, pk):
        _require_operator(request, "approve")
        img = DestinationImage.objects.filter(pk=pk).select_related("destination").first()
        if not img:
            return Response({"detail": "not found"}, status=404)
        from tourist.views_admin import _is_platform_admin, _require_destination_access
        if not _is_platform_admin(request.user):
            _require_destination_access(request, img.destination, "images", "approve")
        action = request.data.get("action")  # approve | reject
        if action == "approve":
            img.verification_status = DestinationImage.ImageStatus.APPROVED
            img.is_verified = True
        elif action == "reject":
            img.verification_status = DestinationImage.ImageStatus.REJECTED
            img.is_verified = False
            img.is_cover = False
        else:
            return Response({"detail": "action must be approve or reject"}, status=400)
        img.save()
        from tourist.views_admin import _recompute_destination_cover
        _recompute_destination_cover(img.destination)
        from audit.models import AuditLog
        AuditLog.objects.create(
            user=request.user, user_email=request.user.email,
            actor_role=getattr(request.user, "role", ""), category="media",
            severity="warning" if action == "reject" else "info", source="backend",
            action=f"image.{action}", message=f"{action.title()} image #{img.pk}",
            object_type="DestinationImage", object_id=str(img.pk),
            extra={"destination_id": img.destination_id},
        )
        return Response(_img_dict(img))


class ImageValidateView(APIView):
    """Re-run scoring (e.g. after prompt/metadata edit)."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request, pk):
        _require_operator(request, "change")
        img = DestinationImage.objects.filter(pk=pk).select_related("destination").first()
        if not img:
            return Response({"detail": "not found"}, status=404)
        from tourist.views_admin import _is_platform_admin, _require_destination_access
        if not _is_platform_admin(request.user):
            _require_destination_access(request, img.destination, "images", "change")
        scores = score_candidate(img.destination, img.generation_prompt)
        for k, v in scores.as_dict().items():
            setattr(img, k, v)
        img.save()
        from audit.models import AuditLog
        AuditLog.objects.create(
            user=request.user, user_email=request.user.email,
            actor_role=getattr(request.user, "role", ""), category="media",
            severity="info", source="backend", action="image.validate",
            message=f"Validated image #{img.pk}", object_type="DestinationImage",
            object_id=str(img.pk), extra={"destination_id": img.destination_id},
        )
        return Response(_img_dict(img))


class ImageMatchView(APIView):
    """Given an image id, return the most likely destinations by embedding."""
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        img = DestinationImage.objects.filter(pk=pk).select_related("destination").first()
        if not img or not img.embedding.exists():
            return Response({"detail": "image embedding not available"}, status=404)
        if not _operator_can(request):
            if not (img.is_verified and img.verification_status == DestinationImage.ImageStatus.APPROVED
                    and img.destination.is_active and img.destination.status == Destination.SubmissionStatus.APPROVED):
                return Response({"detail": "image embedding not available"}, status=404)
        elif getattr(request.user, "is_authenticated", False):
            from tourist.views_admin import _is_platform_admin, _require_destination_access
            if not _is_platform_admin(request.user):
                _require_destination_access(request, img.destination, "images", "view")
        vec = img.embedding.first().vector
        scored = []
        for emb in ImageEmbedding.objects.filter(content_type="destination").select_related("destination")[:5000]:
            scored.append((cosine(vec, emb.vector), emb.destination))
        scored.sort(reverse=True, key=lambda x: x[0])
        return Response({
            "query_image": img.id,
            "matches": [
                {"destination_id": d.id, "name": d.name, "score": round(s, 3)}
                for s, d in scored[:10] if d
            ],
        })


class SemanticSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if not q:
            return Response({"results": []})

        # 1. Metadata search across images AND their destinations
        public_filter = Q(
            verification_status=DestinationImage.ImageStatus.APPROVED,
            is_verified=True,
            destination__is_active=True,
            destination__status=Destination.SubmissionStatus.APPROVED,
        )
        text_ids = list(DestinationImage.objects.filter(public_filter).filter(
            Q(caption__icontains=q) | Q(source_platform__icontains=q) |
            Q(destination__name__icontains=q) | Q(destination__district__icontains=q) |
            Q(tags__tag__icontains=q)
        ).distinct().values_list("id", flat=True))

        # 2. Semantic: find destinations most similar to the query text
        qvec = embed_text(q)
        dest_scores = {}
        for emb in ImageEmbedding.objects.filter(content_type="destination").select_related("destination")[:10000]:
            s = max(0.0, cosine(qvec, emb.vector))
            if s > 0.05 and emb.destination_id:
                dest_scores[emb.destination_id] = s

        # include images from those semantically-matched destinations
        sem_ids = []
        if dest_scores:
            sem_ids = list(DestinationImage.objects.filter(
                destination_id__in=list(dest_scores.keys())[:200]
            ).values_list("id", flat=True))

        id_set = list(dict.fromkeys(text_ids + sem_ids))[:200]
        imgs = list(DestinationImage.objects.filter(public_filter, id__in=id_set).select_related("destination"))

        # 3. Rank: blend text hit + destination semantic score
        def img_score(img):
            text_hit = 0.5 if (q.lower() in (img.caption or "").lower() or
                               (img.destination and q.lower() in img.destination.name.lower())) else 0.2
            return 0.5 * text_hit + 0.5 * dest_scores.get(img.destination_id, 0.0)

        scored = sorted(((img_score(i), i) for i in imgs), key=lambda x: x[0], reverse=True)

        return Response({
            "query": q,
            "count": len(scored),
            "results": [{"score": round(s, 3), **_img_dict(i)} for s, i in scored[:40]],
        })


class JobsListView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_operator(request, "view")
        from tourist.views_admin import _is_platform_admin
        jobs = ImageGenerationJob.objects.select_related("destination")
        if not _is_platform_admin(request.user):
            jobs = jobs.filter(destination__in=_scope_destinations(request, Destination.objects.all()))
        jobs = jobs.all()[:50]
        return Response([{
            "id": j.id, "destination": j.destination.name, "provider": j.provider,
            "status": j.status, "num_images": j.num_images, "error": j.error_message,
            "created_at": j.created_at, "completed_at": j.completed_at,
            "outputs": j.outputs.count(),
        } for j in jobs])
