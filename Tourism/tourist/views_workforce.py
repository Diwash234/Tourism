"""Tourism Workforce platform — guide profiles, applications, verification center.

Workforce spec §2/§3/§10/§11. Reuses the single User account + role system,
the existing capability permissions, notification_delivery and audit stack.
Business-side partners (hotels, operators, transport, activities) stay in the
existing marketplace module — no duplication here.
"""
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GuideApplication, GuideProfile
from .permissions import IsAdminOrStaff
from .views_admin import _require_capability


def _profile_payload(p, include_private=False):
    data = {
        "id": p.id,
        "name": p.user.full_name,
        "headline": p.headline,
        "bio": p.bio,
        "years_experience": p.years_experience,
        "languages": p.languages,
        "specializations": p.specializations,
        "regions": p.regions,
        "base_city": p.base_city,
        "daily_rate_npr": str(p.daily_rate_npr) if p.daily_rate_npr is not None else None,
        "availability": p.availability,
        "services": p.services,
        "verification_status": p.verification_status,
        "verified_at": p.verified_at,
        "created_at": p.created_at,
    }
    if include_private:
        data.update({
            "email": p.user.email,
            "certifications": p.certifications,
            "license_number": p.license_number,
            "portfolio_urls": p.portfolio_urls,
            "verification_note": p.verification_note,
            "is_public": p.is_public,
        })
    return data


def _application_payload(a):
    return {
        "id": a.id,
        "full_name": a.full_name,
        "user_email": a.user.email,
        "phone": a.phone,
        "base_city": a.base_city,
        "experience_summary": a.experience_summary,
        "languages": a.languages,
        "skills": a.skills,
        "destinations_covered": a.destinations_covered,
        "certifications": a.certifications,
        "license_info": a.license_info,
        "document_urls": a.document_urls,
        "references": a.references,
        "expected_daily_rate_npr": str(a.expected_daily_rate_npr) if a.expected_daily_rate_npr is not None else None,
        "availability": a.availability,
        "status": a.status,
        "admin_note": a.admin_note,
        "reviewed_by": a.reviewed_by.email if a.reviewed_by else None,
        "reviewed_at": a.reviewed_at,
        "created_at": a.created_at,
    }


class GuideDirectoryView(APIView):
    """GET /api/v1/workforce/guides/ — public directory of VERIFIED public guides."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        qs = (GuideProfile.objects.filter(verification_status="verified", is_public=True)
              .select_related("user"))
        q = (request.query_params.get("q") or "").strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(Q(headline__icontains=q) | Q(bio__icontains=q) | Q(base_city__icontains=q)
                           | Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q))
        language = (request.query_params.get("language") or "").strip()
        if language:
            qs = qs.filter(languages__icontains=language)
        region = (request.query_params.get("region") or "").strip()
        if region:
            qs = qs.filter(regions__icontains=region)
        return Response({"count": qs.count(), "results": [_profile_payload(p) for p in qs[:60]]})


class GuideDetailView(APIView):
    """GET /api/v1/workforce/guides/<pk>/ — public detail; verified guides only."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        profile = (GuideProfile.objects.filter(pk=pk, verification_status="verified", is_public=True)
                   .select_related("user").first())
        if not profile:
            return Response({"detail": "Guide not found or not publicly listed."}, status=404)
        return Response(_profile_payload(profile))


class MyGuideProfileView(APIView):
    """GET/PUT /api/v1/workforce/guide-profile/ — the caller's own guide profile.

    Verification fields are server-controlled; staff can never self-verify.
    """

    permission_classes = [permissions.IsAuthenticated]
    EDITABLE = {
        "headline": (str, 160), "bio": (str, None), "base_city": (str, 120),
        "license_number": (str, 120), "verification_note": None,
    }

    def get(self, request):
        profile = GuideProfile.objects.filter(user=request.user).select_related("user").first()
        if not profile:
            return Response({"exists": False})
        return Response({"exists": True, **_profile_payload(profile, include_private=True)})

    def put(self, request):
        profile, _created = GuideProfile.objects.get_or_create(user=request.user)
        data = request.data
        for field in ("headline", "bio", "base_city", "license_number"):
            if field in data and isinstance(data[field], str):
                limit = self.EDITABLE[field][1]
                setattr(profile, field, data[field].strip()[:limit] if limit else data[field].strip())
        if isinstance(data.get("years_experience"), (int, float)):
            profile.years_experience = max(0, min(int(data["years_experience"]), 80))
        for field in ("languages", "specializations", "regions", "portfolio_urls", "services", "certifications"):
            if isinstance(data.get(field), list):
                setattr(profile, field, data[field][:40])
        if isinstance(data.get("availability"), dict):
            profile.availability = data["availability"]
        if data.get("daily_rate_npr") in (None, ""):
            profile.daily_rate_npr = None
        else:
            try:
                profile.daily_rate_npr = max(0, float(data["daily_rate_npr"]))
            except (TypeError, ValueError):
                pass
        if isinstance(data.get("is_public"), bool):
            profile.is_public = data["is_public"]
        profile.save()
        return Response(_profile_payload(profile, include_private=True))


class GuideApplicationView(APIView):
    """POST /api/v1/workforce/guide-applications/ — apply; GET — own applications."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = GuideApplication.objects.filter(user=request.user).select_related("reviewed_by")
        return Response({"results": [_application_payload(a) for a in qs[:20]]})

    def post(self, request):
        data = request.data
        full_name = (data.get("full_name") or request.user.full_name or "").strip()
        experience = (data.get("experience_summary") or "").strip()
        if not full_name or not experience:
            return Response({"detail": "full_name and experience_summary are required."}, status=400)
        open_states = {"applied", "under_review", "document_verification", "needs_info"}
        if GuideApplication.objects.filter(user=request.user, status__in=open_states).exists():
            return Response({"detail": "You already have an application in progress."}, status=400)
        app = GuideApplication.objects.create(
            user=request.user,
            full_name=full_name[:200],
            phone=(data.get("phone") or "").strip()[:40],
            base_city=(data.get("base_city") or "").strip()[:120],
            experience_summary=experience,
            languages=data.get("languages") if isinstance(data.get("languages"), list) else [],
            skills=data.get("skills") if isinstance(data.get("skills"), list) else [],
            destinations_covered=data.get("destinations_covered") if isinstance(data.get("destinations_covered"), list) else [],
            certifications=data.get("certifications") if isinstance(data.get("certifications"), list) else [],
            license_info=(data.get("license_info") or "").strip()[:240],
            document_urls=data.get("document_urls") if isinstance(data.get("document_urls"), list) else [],
            references=data.get("references") if isinstance(data.get("references"), list) else [],
            expected_daily_rate_npr=data.get("expected_daily_rate_npr") or None,
            availability=data.get("availability") if isinstance(data.get("availability"), dict) else {},
        )
        from audit.logging_services import log_action
        log_action(request=request, action="workforce.guide.apply", category="workforce",
                   message=f"Guide application submitted by {request.user.email}",
                   object_type="GuideApplication", object_id=str(app.id))
        # let reviewers know
        from .models import User
        for reviewer in User.objects.filter(is_superuser=True)[:10]:
            from .notification_delivery import queue_notification
            queue_notification(reviewer, "New guide application",
                               f"{app.full_name} applied to become a tourism guide.",
                               category="workforce")
        return Response(_application_payload(app), status=201)


class AdminGuideApplicationListView(APIView):
    """GET /api/v1/workforce/admin/applications/ — verification center queue."""

    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_capability(request, "marketplace", "view")
        qs = GuideApplication.objects.select_related("user", "reviewed_by")
        status = (request.query_params.get("status") or "").strip()
        if status:
            qs = qs.filter(status=status)
        counts = {choice: GuideApplication.objects.filter(status=choice).count()
                  for choice, _label in GuideApplication.Status.choices}
        counts["all"] = sum(counts.values())
        return Response({"counts": counts, "results": [_application_payload(a) for a in qs[:100]]})


class AdminGuideApplicationActionView(APIView):
    """POST /api/v1/workforce/admin/applications/<pk>/action/.

    review | verify_documents | needs_info | approve | reject
    Approval provisions/updates the GuideProfile as verified — the guide
    never self-verifies; every transition is notified and audited.
    """

    permission_classes = [IsAdminOrStaff]
    NEXT = {"review": "under_review", "verify_documents": "document_verification", "needs_info": "needs_info"}

    def post(self, request, pk):
        _require_capability(request, "marketplace", "change")
        from audit.logging_services import log_action
        from .notification_delivery import queue_notification

        action = (request.data.get("action") or "").strip()
        note = (request.data.get("note") or "").strip()
        if action not in {"review", "verify_documents", "needs_info", "approve", "reject"}:
            return Response({"detail": "Allowed actions: review, verify_documents, needs_info, approve, reject."}, status=400)
        app = GuideApplication.objects.select_related("user").filter(pk=pk).first()
        if not app:
            return Response({"detail": "Application not found."}, status=404)
        if action in {"needs_info", "reject"} and not note:
            return Response({"detail": f"A note is required to {action.replace('_', ' ')} an application."}, status=400)

        previous = app.status
        if action == "approve":
            if previous in {"approved", "rejected"}:
                return Response({"detail": f"Application already {previous}."}, status=400)
            app.status = "approved"
            profile, _created = GuideProfile.objects.get_or_create(user=app.user)
            profile.verification_status = "verified"
            profile.verified_at = timezone.now()
            profile.verified_by = request.user
            profile.verification_note = note[:500]
            if not profile.headline and app.skills:
                profile.headline = ", ".join(map(str, app.skills[:3]))[:160]
            if not profile.languages and app.languages:
                profile.languages = app.languages[:40]
            if not profile.regions and app.destinations_covered:
                profile.regions = app.destinations_covered[:40]
            if not profile.base_city and app.base_city:
                profile.base_city = app.base_city
            if profile.daily_rate_npr is None and app.expected_daily_rate_npr is not None:
                profile.daily_rate_npr = app.expected_daily_rate_npr
            profile.save()
            queue_notification(app.user, "Guide application approved",
                               note or "Congratulations — your guide profile is now verified and publicly listed.",
                               category="workforce")
        elif action == "reject":
            if previous in {"approved", "rejected"}:
                return Response({"detail": f"Application already {previous}."}, status=400)
            app.status = "rejected"
            queue_notification(app.user, "Guide application rejected", note, category="workforce")
        else:
            app.status = self.NEXT[action]
            if action == "needs_info":
                queue_notification(app.user, "Additional information requested", note, category="workforce")

        app.admin_note = note[:1000]
        app.reviewed_by = request.user
        app.reviewed_at = timezone.now()
        app.save(update_fields=["status", "admin_note", "reviewed_by", "reviewed_at", "updated_at"])
        log_action(request=request, action=f"workforce.guide.{action}", category="workforce",
                   message=f"Guide application {app.full_name}: {previous} → {app.status}" + (f" ({note})" if note else ""),
                   object_type="GuideApplication", object_id=str(app.id))
        return Response(_application_payload(app))


class AdminGuideProfileActionView(APIView):
    """POST /api/v1/workforce/admin/guides/<pk>/action/ — suspend / reinstate a verified guide."""

    permission_classes = [IsAdminOrStaff]

    def post(self, request, pk):
        _require_capability(request, "marketplace", "change")
        from audit.logging_services import log_action
        from .notification_delivery import queue_notification

        action = (request.data.get("action") or "").strip()
        note = (request.data.get("note") or "").strip()
        if action not in {"suspend", "reinstate"}:
            return Response({"detail": "Allowed actions: suspend, reinstate."}, status=400)
        profile = GuideProfile.objects.select_related("user").filter(pk=pk).first()
        if not profile:
            return Response({"detail": "Guide profile not found."}, status=404)
        if action == "suspend" and not note:
            return Response({"detail": "A suspension reason is required."}, status=400)
        previous = profile.verification_status
        profile.verification_status = "suspended" if action == "suspend" else "verified"
        if action == "reinstate":
            profile.verified_at = timezone.now()
            profile.verified_by = request.user
        profile.verification_note = note[:500] or profile.verification_note
        profile.save(update_fields=["verification_status", "verified_at", "verified_by", "verification_note", "updated_at"])
        queue_notification(profile.user,
                           "Guide profile suspended" if action == "suspend" else "Guide profile reinstated",
                           note or ("Your guide profile is active again." if action == "reinstate" else ""),
                           category="workforce")
        log_action(request=request, action=f"workforce.guide.{action}", category="workforce",
                   message=f"Guide profile {profile.user.email}: {previous} → {profile.verification_status}" + (f" ({note})" if note else ""),
                   object_type="GuideProfile", object_id=str(profile.id))
        return Response(_profile_payload(profile, include_private=True))
