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
    from django.db.models import Avg, Count
    agg = p.reviews.aggregate(avg=Avg("rating"), count=Count("id"))
    data = {
        "id": p.id,
        "name": p.user.full_name,
        "rating_avg": round(agg["avg"], 2) if agg["avg"] else None,
        "review_count": agg["count"] or 0,
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


# ============================================================
# TOURISM JOBS MARKETPLACE (workforce spec §9)
# ============================================================

def _job_payload(job, include_stats=False):
    data = {
        "id": job.id,
        "title": job.title,
        "role_type": job.role_type,
        "role_type_label": job.get_role_type_display(),
        "description": job.description,
        "requirements": job.requirements,
        "skills": job.skills,
        "city": job.city,
        "employment_type": job.employment_type,
        "employment_type_label": job.get_employment_type_display(),
        "compensation": job.compensation,
        "start_date": job.start_date,
        "application_deadline": job.application_deadline,
        "status": job.status,
        "posted_by": job.posted_by.email if job.posted_by else None,
        "created_at": job.created_at,
    }
    if include_stats:
        data["application_count"] = job.applications.count()
    return data


def _job_application_payload(a):
    return {
        "id": a.id,
        "job_id": a.job_id,
        "job_title": a.job.title,
        "role_type": a.job.role_type,
        "user_email": a.user.email,
        "applicant_name": a.user.full_name,
        "cover_letter": a.cover_letter,
        "experience_summary": a.experience_summary,
        "skills": a.skills,
        "cv_url": a.cv_url,
        "portfolio_url": a.portfolio_url,
        "availability": a.availability,
        "status": a.status,
        "admin_note": a.admin_note,
        "reviewed_by": a.reviewed_by.email if a.reviewed_by else None,
        "reviewed_at": a.reviewed_at,
        "created_at": a.created_at,
    }


class TourismJobListView(APIView):
    """GET public open jobs; POST creates a job (marketplace capability)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .models import TourismJob
        qs = TourismJob.objects.filter(status="open")
        q = (request.query_params.get("q") or "").strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(city__icontains=q))
        role = (request.query_params.get("role_type") or "").strip()
        if role:
            qs = qs.filter(role_type=role)
        employment = (request.query_params.get("employment_type") or "").strip()
        if employment:
            qs = qs.filter(employment_type=employment)
        return Response({"count": qs.count(), "role_types": TourismJob.RoleType.choices,
                         "results": [_job_payload(j, include_stats=True) for j in qs[:60]]})

    def post(self, request):
        from .models import TourismJob
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=401)
        _require_capability(request, "marketplace", "add")
        from audit.logging_services import log_action
        title = (request.data.get("title") or "").strip()
        description = (request.data.get("description") or "").strip()
        if not title or not description:
            return Response({"detail": "title and description are required."}, status=400)
        role_type = request.data.get("role_type") or "other"
        if role_type not in TourismJob.RoleType.values:
            return Response({"detail": f"Unknown role_type '{role_type}'."}, status=400)
        job = TourismJob.objects.create(
            posted_by=request.user,
            title=title[:200],
            role_type=role_type,
            description=description,
            requirements=(request.data.get("requirements") or "").strip(),
            skills=request.data.get("skills") if isinstance(request.data.get("skills"), list) else [],
            city=(request.data.get("city") or "").strip()[:120],
            employment_type=request.data.get("employment_type") if request.data.get("employment_type") in TourismJob.EmploymentType.values else "contract",
            compensation=(request.data.get("compensation") or "").strip()[:160],
            start_date=request.data.get("start_date") or None,
            application_deadline=request.data.get("application_deadline") or None,
        )
        log_action(request=request, action="workforce.job.create", category="workforce",
                   message=f"Tourism job '{job.title}' posted", object_type="TourismJob", object_id=str(job.id))
        return Response(_job_payload(job), status=201)


class TourismJobAdminView(APIView):
    """GET all jobs incl. non-open; PATCH <id> via POST action — pause/reopen/close/fill."""

    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        from .models import TourismJob
        _require_capability(request, "marketplace", "view")
        qs = TourismJob.objects.select_related("posted_by")
        status = (request.query_params.get("status") or "").strip()
        if status:
            qs = qs.filter(status=status)
        counts = {choice: TourismJob.objects.filter(status=choice).count()
                  for choice, _label in TourismJob.Status.choices}
        counts["all"] = sum(counts.values())
        return Response({"counts": counts, "results": [_job_payload(j, include_stats=True) for j in qs[:100]]})


class TourismJobStatusView(APIView):
    """POST /api/v1/workforce/admin/jobs/<pk>/action/ — pause/reopen/close/fill/update."""

    permission_classes = [IsAdminOrStaff]
    NEXT = {"pause": "paused", "reopen": "open", "close": "closed", "fill": "filled"}

    def post(self, request, pk):
        from .models import TourismJob
        _require_capability(request, "marketplace", "change")
        from audit.logging_services import log_action
        job = TourismJob.objects.filter(pk=pk).first()
        if not job:
            return Response({"detail": "Job not found."}, status=404)
        action = (request.data.get("action") or "").strip()
        if action not in self.NEXT:
            return Response({"detail": f"Allowed actions: {', '.join(sorted(self.NEXT))}."}, status=400)
        previous = job.status
        job.status = self.NEXT[action]
        job.save(update_fields=["status", "updated_at"])
        log_action(request=request, action=f"workforce.job.{action}", category="workforce",
                   message=f"Tourism job '{job.title}': {previous} → {job.status}",
                   object_type="TourismJob", object_id=str(job.id))
        return Response(_job_payload(job, include_stats=True))


class TourismJobApplicationView(APIView):
    """POST apply to a job; GET own applications."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .models import TourismJobApplication
        qs = TourismJobApplication.objects.filter(user=request.user).select_related("job", "reviewed_by")
        return Response({"results": [_job_application_payload(a) for a in qs[:30]]})

    def post(self, request):
        from .models import TourismJob, TourismJobApplication
        from audit.logging_services import log_action
        from .notification_delivery import queue_notification
        job_id = request.data.get("job")
        cover_letter = (request.data.get("cover_letter") or "").strip()
        if not cover_letter:
            return Response({"detail": "cover_letter is required."}, status=400)
        job = TourismJob.objects.filter(pk=job_id).first()
        if not job:
            return Response({"detail": "Job not found."}, status=404)
        if job.status != "open":
            return Response({"detail": f"This job is {job.status} and no longer accepting applications."}, status=400)
        if TourismJobApplication.objects.filter(job=job, user=request.user).exists():
            return Response({"detail": "You have already applied to this job."}, status=400)
        app = TourismJobApplication.objects.create(
            job=job, user=request.user,
            cover_letter=cover_letter,
            experience_summary=(request.data.get("experience_summary") or "").strip(),
            skills=request.data.get("skills") if isinstance(request.data.get("skills"), list) else [],
            cv_url=(request.data.get("cv_url") or "").strip()[:600],
            portfolio_url=(request.data.get("portfolio_url") or "").strip()[:600],
            availability=(request.data.get("availability") or "").strip()[:160],
        )
        log_action(request=request, action="workforce.job.apply", category="workforce",
                   message=f"{request.user.email} applied to '{job.title}'",
                   object_type="TourismJobApplication", object_id=str(app.id))
        if job.posted_by and job.posted_by != request.user:
            queue_notification(job.posted_by, "New job application",
                               f"{request.user.full_name} applied to '{job.title}'.", category="workforce")
        return Response(_job_application_payload(app), status=201)


class AdminJobApplicationListView(APIView):
    """GET /api/v1/workforce/admin/job-applications/ — review queue."""

    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        from .models import TourismJobApplication
        _require_capability(request, "marketplace", "view")
        qs = TourismJobApplication.objects.select_related("job", "user", "reviewed_by")
        status = (request.query_params.get("status") or "").strip()
        if status:
            qs = qs.filter(status=status)
        job = (request.query_params.get("job") or "").strip()
        if job.isdigit():
            qs = qs.filter(job_id=int(job))
        counts = {choice: TourismJobApplication.objects.filter(status=choice).count()
                  for choice, _label in TourismJobApplication.Status.choices}
        counts["all"] = sum(counts.values())
        return Response({"counts": counts, "results": [_job_application_payload(a) for a in qs[:100]]})


class AdminJobApplicationActionView(APIView):
    """POST /api/v1/workforce/admin/job-applications/<pk>/action/ — shortlist/hire/reject."""

    permission_classes = [IsAdminOrStaff]
    NEXT = {"shortlist": "shortlisted", "hire": "hired", "reject": "rejected"}

    def post(self, request, pk):
        from .models import TourismJobApplication
        _require_capability(request, "marketplace", "change")
        from audit.logging_services import log_action
        from .notification_delivery import queue_notification
        action = (request.data.get("action") or "").strip()
        note = (request.data.get("note") or "").strip()
        if action not in self.NEXT:
            return Response({"detail": "Allowed actions: shortlist, hire, reject."}, status=400)
        if action == "reject" and not note:
            return Response({"detail": "A note is required to reject an application."}, status=400)
        app = TourismJobApplication.objects.select_related("job", "user").filter(pk=pk).first()
        if not app:
            return Response({"detail": "Application not found."}, status=404)
        previous = app.status
        app.status = self.NEXT[action]
        app.admin_note = note[:1000]
        app.reviewed_by = request.user
        app.reviewed_at = timezone.now()
        app.save(update_fields=["status", "admin_note", "reviewed_by", "reviewed_at", "updated_at"])
        queue_notification(app.user, f"Job application {self.NEXT[action]}",
                           note or f"Your application to '{app.job.title}' is now {self.NEXT[action]}.",
                           category="workforce")
        log_action(request=request, action=f"workforce.job.{action}", category="workforce",
                   message=f"Application to '{app.job.title}' by {app.user.email}: {previous} → {app.status}" + (f" ({note})" if note else ""),
                   object_type="TourismJobApplication", object_id=str(app.id))
        return Response(_job_application_payload(app))


# ============================================================
# TOURIST ↔ GUIDE BOOKINGS + REVIEWS (workforce spec §12/§13)
# ============================================================

def _booking_payload(b):
    return {
        "id": b.id,
        "status": b.status,
        "start_date": b.start_date,
        "end_date": b.end_date,
        "group_size": b.group_size,
        "message": b.message,
        "note": b.note,
        "created_at": b.created_at,
        "responded_at": b.responded_at,
        "tourist_email": b.tourist.email,
        "tourist_name": b.tourist.full_name,
        "guide_id": b.guide_profile_id,
        "guide_name": b.guide_profile.user.full_name,
        "reviewed": hasattr(b, "review"),
        "review": ({"rating": b.review.rating, "review": b.review.review, "created_at": b.review.created_at}
                   if hasattr(b, "review") else None),
    }


class GuideBookingRequestView(APIView):
    """GET own requests (as tourist or as guide); POST create a request."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .models import GuideBookingRequest, GuideProfile
        side = request.query_params.get("side") or "tourist"
        if side == "guide":
            profile = GuideProfile.objects.filter(user=request.user).first()
            if not profile:
                return Response({"detail": "You do not have a guide profile yet — apply first."}, status=404)
            qs = GuideBookingRequest.objects.filter(guide_profile=profile).select_related("tourist", "guide_profile__user")
        else:
            qs = GuideBookingRequest.objects.filter(tourist=request.user).select_related("guide_profile__user")
        return Response({"results": [_booking_payload(b) for b in qs[:30]]})

    def post(self, request):
        from .models import GuideBookingRequest, GuideProfile
        from .notification_delivery import queue_notification
        from audit.logging_services import log_action
        from datetime import date
        guide_id = request.data.get("guide_id")
        profile = GuideProfile.objects.select_related("user").filter(pk=guide_id).first()
        if not profile:
            return Response({"detail": "Guide not found."}, status=404)
        if profile.verification_status != "verified" or not profile.is_public:
            return Response({"detail": "This guide is not available for booking."}, status=400)
        if profile.user_id == request.user.id:
            return Response({"detail": "You cannot book your own guide profile."}, status=400)
        try:
            start = date.fromisoformat(str(request.data.get("start_date") or ""))
        except ValueError:
            return Response({"detail": "start_date (YYYY-MM-DD) is required."}, status=400)
        end_raw = request.data.get("end_date")
        end = None
        if end_raw:
            try:
                end = date.fromisoformat(str(end_raw))
            except ValueError:
                return Response({"detail": "end_date must be YYYY-MM-DD."}, status=400)
            if end < start:
                return Response({"detail": "end_date is before start_date."}, status=400)
        if GuideBookingRequest.objects.filter(tourist=request.user, guide_profile=profile,
                                              status__in=["requested", "accepted"]).exists():
            return Response({"detail": "You already have an active request with this guide."}, status=400)
        try:
            group_size = max(1, min(200, int(request.data.get("group_size") or 1)))
        except (TypeError, ValueError):
            group_size = 1
        booking = GuideBookingRequest.objects.create(
            tourist=request.user, guide_profile=profile,
            start_date=start, end_date=end, group_size=group_size,
            message=(request.data.get("message") or "").strip()[:2000],
        )
        queue_notification(profile.user, "New booking request",
                           f"{request.user.full_name} requested you as a guide from {start.isoformat()}.",
                           category="workforce")
        log_action(request=request, action="workforce.booking.request", category="workforce",
                   message=f"{request.user.email} requested guide {profile.user.email} from {start.isoformat()}",
                   object_type="GuideBookingRequest", object_id=str(booking.id))
        return Response(_booking_payload(booking), status=201)


class GuideBookingActionView(APIView):
    """POST /api/v1/workforce/guide-bookings/<pk>/action/ — accept/decline/complete/cancel."""

    permission_classes = [permissions.IsAuthenticated]
    GUIDE_ACTIONS = {"accept": "accepted", "decline": "declined"}

    def post(self, request, pk):
        from .models import GuideBookingRequest
        from .notification_delivery import queue_notification
        from audit.logging_services import log_action
        booking = GuideBookingRequest.objects.select_related("tourist", "guide_profile__user").filter(pk=pk).first()
        if not booking:
            return Response({"detail": "Booking request not found."}, status=404)
        action = (request.data.get("action") or "").strip()
        note = (request.data.get("note") or "").strip()
        is_guide = booking.guide_profile.user_id == request.user.id
        is_tourist = booking.tourist_id == request.user.id
        if not is_guide and not is_tourist:
            return Response({"detail": "Only the tourist or the guide may act on this request."}, status=403)
        if action in self.GUIDE_ACTIONS:
            if not is_guide:
                return Response({"detail": "Only the guide may accept or decline."}, status=403)
            if booking.status != "requested":
                return Response({"detail": f"Only pending requests can be accepted or declined (status: {booking.status})."}, status=400)
            if action == "decline" and not note:
                return Response({"detail": "A note is required to decline a request."}, status=400)
        elif action == "complete":
            if booking.status != "accepted":
                return Response({"detail": "Only accepted bookings can be marked completed."}, status=400)
        elif action == "cancel":
            if booking.status not in ("requested", "accepted"):
                return Response({"detail": "This request can no longer be cancelled."}, status=400)
        else:
            return Response({"detail": "Allowed actions: accept, decline, complete, cancel."}, status=400)
        previous = booking.status
        booking.status = {"accept": "accepted", "decline": "declined",
                          "complete": "completed", "cancel": "cancelled"}[action]
        booking.note = note[:1000] or booking.note
        booking.responded_at = timezone.now()
        booking.save(update_fields=["status", "note", "responded_at", "updated_at"])
        other = booking.tourist if is_guide else booking.guide_profile.user
        queue_notification(other, f"Booking {booking.status}",
                           note or f"Guide booking from {booking.start_date.isoformat()} is now {booking.status}.",
                           category="workforce")
        log_action(request=request, action=f"workforce.booking.{action}", category="workforce",
                   message=f"Booking {booking.id}: {previous} → {booking.status}" + (f" ({note})" if note else ""),
                   object_type="GuideBookingRequest", object_id=str(booking.id))
        return Response(_booking_payload(booking))


class GuideReviewCreateView(APIView):
    """POST /api/v1/workforce/guide-bookings/<pk>/review/ — review a completed booking."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from .models import GuideBookingRequest, GuideReview
        from .notification_delivery import queue_notification
        booking = GuideBookingRequest.objects.select_related("tourist", "guide_profile__user").filter(pk=pk).first()
        if not booking:
            return Response({"detail": "Booking request not found."}, status=404)
        if booking.tourist_id != request.user.id:
            return Response({"detail": "Only the tourist on this booking may review it."}, status=403)
        if booking.status != "completed":
            return Response({"detail": "You can review a booking once it is completed."}, status=400)
        if hasattr(booking, "review"):
            return Response({"detail": "This booking has already been reviewed."}, status=400)
        try:
            rating = int(request.data.get("rating"))
        except (TypeError, ValueError):
            return Response({"detail": "rating (1-5) is required."}, status=400)
        if not 1 <= rating <= 5:
            return Response({"detail": "rating must be between 1 and 5."}, status=400)
        review = GuideReview.objects.create(
            booking=booking, user=request.user, guide_profile=booking.guide_profile,
            rating=rating, review=(request.data.get("review") or "").strip()[:2000],
        )
        queue_notification(booking.guide_profile.user, "New guide review",
                           f"You received a {rating}★ review for the trip starting {booking.start_date.isoformat()}.",
                           category="workforce")
        return Response({"id": review.id, "rating": review.rating, "review": review.review,
                         "created_at": review.created_at}, status=201)


class GuideReviewListView(APIView):
    """GET /api/v1/workforce/guides/<pk>/reviews/ — public reviews + aggregate."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        from django.db.models import Avg, Count
        from .models import GuideProfile, GuideReview
        profile = GuideProfile.objects.filter(pk=pk).first()
        if not profile:
            return Response({"detail": "Guide not found."}, status=404)
        agg = profile.reviews.aggregate(avg=Avg("rating"), count=Count("id"))
        reviews = GuideReview.objects.filter(guide_profile=profile).select_related("user")[:20]
        return Response({
            "rating_avg": round(agg["avg"], 2) if agg["avg"] else None,
            "review_count": agg["count"] or 0,
            "results": [{"id": r.id, "rating": r.rating, "review": r.review,
                         "author": r.user.full_name, "created_at": r.created_at} for r in reviews],
        })
