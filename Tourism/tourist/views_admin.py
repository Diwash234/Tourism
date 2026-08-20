from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import (
    Destination, Alert, DestinationImage, VisitHistory, Favorite, Review, Rating,
    SOSAlert, SharedTrip, LocationPing, Category, Hotel,
    Hospital, PoliceStation, TravelExpenseFeedback, TravelRiskFeedback,
    DestinationAuditLog, FeedbackEvidence, UserFeedback, InfrastructureSubmission, MLTrainingRun,
    SiteSetting, BrandingAsset, CMSContentTranslation, ManagedPage, ContentSection, ManagedNavigationItem, CMSRevision, FeedbackMessage, StaffCapabilityProfile, Notification
)
from .permissions import IsAdminOrStaff
from .serializers import InfrastructureSubmissionSerializer

User = get_user_model()


def _has_capability(request, module, action="view"):
    user = request.user
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}:
        return True
    profile = getattr(user, "capability_profile", None)
    return bool(profile and profile.allows(module, action))


def _require_capability(request, module, action="view"):
    if not _has_capability(request, module, action):
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied(f"Missing {module}.{action} capability")


def _sync_destination_json(destination):
    """Atomic JSON exchange snapshot for admin-edited destinations."""
    import json
    import os
    from pathlib import Path
    path = Path(settings.BASE_DIR) / "dataset" / "data.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"destinations": {}}
    except (json.JSONDecodeError, OSError):
        existing = {"destinations": {}}
    existing.setdefault("destinations", {})[str(destination.id)] = {
        "id": destination.id, "name": destination.name, "slug": destination.slug,
        "description": destination.description, "short_description": destination.short_description,
        "city": destination.city, "district": destination.district, "province": destination.province,
        "municipality": destination.municipality, "ward_number": destination.ward_number,
        "latitude": float(destination.latitude) if destination.latitude is not None else None,
        "longitude": float(destination.longitude) if destination.longitude is not None else None,
        "status": destination.status, "updated_at": destination.updated_at.isoformat(),
        "images": [{"id": image.id, "url": image.external_url or (image.image.url if image.image else ""), "caption": image.caption, "is_cover": image.is_cover, "status": image.verification_status} for image in destination.gallery.all()[:100]],
    }
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


class AdminStatsView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        total_destinations = Destination.objects.count()
        pending_destinations = Destination.objects.filter(status=Destination.SubmissionStatus.PENDING).count()
        approved_destinations = Destination.objects.filter(status=Destination.SubmissionStatus.APPROVED).count()
        total_views = Destination.objects.aggregate(total=Sum("views_count"))["total"] or 0
        active_sos = SOSAlert.objects.filter(status=SOSAlert.Status.ACTIVE).count()
        pending_images = DestinationImage.objects.filter(
            Q(verification_status="pending") | Q(is_verified=False)
        ).count()

        return Response({
            "totalUsers": User.objects.count(),
            "touristCount": User.objects.filter(role=User.Role.TOURIST).count(),
            "staffCount": User.objects.filter(role__in=[
                User.Role.STAFF, User.Role.CONTENT_MODERATOR, User.Role.DISTRICT_MANAGER,
                User.Role.HOTEL_MANAGER, User.Role.TOURIST_POLICE
            ]).count(),
            "adminCount": User.objects.filter(role__in=[
                User.Role.ADMIN, User.Role.SUPER_ADMIN, User.Role.TOURISM_ADMIN
            ]).count(),
            "totalDestinations": total_destinations,
            "pendingDestinations": pending_destinations,
            "approvedDestinations": approved_destinations,
            "activeAlerts": Alert.objects.filter(is_active=True).count(),
            "activeEmergencies": active_sos,
            "pendingImages": pending_images,
            "totalDestinationViews": total_views,
            "totalVisitsLogged": VisitHistory.objects.count(),
            "totalExpenseReports": TravelExpenseFeedback.objects.count(),
            "totalRiskReports": TravelRiskFeedback.objects.count(),
        })


class AdminUsersView(APIView):
    """Filterable user directory. Unparameterized requests retain the legacy list shape."""
    permission_classes = [IsAdminOrStaff]

    @staticmethod
    def _row(u):
        return {
            "id": u.id, "email": u.email, "first_name": u.first_name,
            "last_name": u.last_name, "full_name": u.full_name, "bio": u.bio or "",
            "role": u.role, "managed_district": u.managed_district or "",
            "is_active": u.is_active, "is_verified": u.is_verified,
            "phone_verified": u.phone_verified, "is_staff": u.is_staff,
            "is_superuser": u.is_superuser, "city": u.city or "",
            "country": u.country or "", "auth_provider": u.auth_provider,
            "history_count": getattr(u, "history_count", 0),
            "last_login": u.last_login, "date_joined": u.date_joined,
        }

    def get(self, request):
        _require_capability(request, "users", "view")
        from django.core.paginator import Paginator
        users = User.objects.annotate(history_count=Count("history", distinct=True))
        q = request.query_params.get("q", "").strip()
        if q:
            users = users.filter(Q(email__icontains=q) | Q(first_name__icontains=q) |
                                 Q(last_name__icontains=q) | Q(city__icontains=q) |
                                 Q(managed_district__icontains=q))
        role = request.query_params.get("role", "")
        if role:
            users = users.filter(role=role)
        state = request.query_params.get("status", "")
        if state in {"active", "inactive"}:
            users = users.filter(is_active=(state == "active"))
        verified = request.query_params.get("verified", "")
        if verified in {"true", "false"}:
            users = users.filter(is_verified=(verified == "true"))
        ordering = request.query_params.get("ordering", "-date_joined")
        allowed_ordering = {"date_joined", "-date_joined", "email", "-email", "last_login", "-last_login"}
        users = users.order_by(ordering if ordering in allowed_ordering else "-date_joined")

        # Backward compatibility for the existing dashboard bootstrap call.
        if not request.query_params:
            return Response([self._row(u) for u in users])
        try:
            page_size = min(100, max(10, int(request.query_params.get("page_size", 25))))
        except (TypeError, ValueError):
            page_size = 25
        page = Paginator(users, page_size).get_page(request.query_params.get("page", 1))
        return Response({"count": page.paginator.count, "page": page.number,
                         "pages": page.paginator.num_pages,
                         "results": [self._row(u) for u in page.object_list]})

    def post(self, request):
        _require_capability(request, "users", "add")
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")
        role = request.data.get("role", User.Role.TOURIST)
        if role not in User.Role.values:
            return Response({"detail": "Invalid role."}, status=400)
        if role in {User.Role.ADMIN, User.Role.SUPER_ADMIN, User.Role.TOURISM_ADMIN} and not request.user.is_superuser:
            return Response({"detail": "Only a super administrator may create administrator accounts."}, status=403)
        if not email or len(password) < 8:
            return Response({"detail": "A valid email and password of at least 8 characters are required."}, status=400)
        if User.objects.filter(email=email).exists():
            return Response({"detail": "A user with this email already exists."}, status=400)
        staff_roles = set(User.Role.values) - {User.Role.TOURIST, User.Role.GUIDE}
        user = User.objects.create_user(email=email, password=password,
            first_name=request.data.get("first_name", "").strip(),
            last_name=request.data.get("last_name", "").strip(),
            bio=request.data.get("bio", "").strip(), role=role,
            managed_district=request.data.get("managed_district", "").strip(),
            is_staff=role in staff_roles, is_active=True, is_verified=False)
        _audit_user_change(request, user, "user.create", {}, {"role": role, "is_active": True})
        return Response({"id": user.id, "email": user.email, "role": user.role,
                         "message": "User created. Verification is still required."}, status=201)


def _audit_user_change(request, target, action, before, after):
    from audit.models import AuditLog
    AuditLog.objects.create(user=request.user, user_email=request.user.email,
        actor_role=request.user.role, category="security", severity="warning",
        source="backend", action=action, message=f"{action}: {target.email}",
        object_type="User", object_id=str(target.id), extra={"before": before, "after": after})


def _can_manage_user(actor, target, requested_role=None):
    if actor.pk == target.pk:
        return False, "You cannot change your own role or access state here."
    if target.is_superuser and not actor.is_superuser:
        return False, "Only a super administrator may manage this account."
    if requested_role in {User.Role.ADMIN, User.Role.SUPER_ADMIN, User.Role.TOURISM_ADMIN} and not actor.is_superuser:
        return False, "Only a super administrator may assign administrator roles."
    return True, ""


class UpdateUserStatusView(APIView):
    permission_classes = [IsAdminOrStaff]

    def put(self, request, id):
        _require_capability(request, "users", "change")
        user = User.objects.filter(id=id).first()
        if not user:
            return Response({"detail": "User not found."}, status=404)
        role = request.data.get("role")
        allowed, reason = _can_manage_user(request.user, user, role)
        if not allowed:
            return Response({"detail": reason}, status=403)
        if role is not None and role not in User.Role.values:
            return Response({"detail": "Invalid role."}, status=400)
        before = {"role": user.role, "is_active": user.is_active, "is_verified": user.is_verified}
        for field in ("is_active", "is_verified", "managed_district", "first_name", "last_name", "bio"):
            if field in request.data:
                setattr(user, field, request.data[field])
        if role is not None:
            user.role = role
            user.is_staff = role not in {User.Role.TOURIST, User.Role.GUIDE}
        user.save()
        after = {"role": user.role, "is_active": user.is_active, "is_verified": user.is_verified}
        _audit_user_change(request, user, "user.access.change", before, after)
        return Response({"id": user.id, "email": user.email, **after, "message": "User updated."})

    patch = put

    def delete(self, request, id):
        """Retention-safe removal: deactivate and revoke access instead of hard deleting."""
        _require_capability(request, "users", "delete")
        user = User.objects.filter(id=id).first()
        if not user:
            return Response({"detail": "User not found."}, status=404)
        allowed, reason = _can_manage_user(request.user, user)
        if not allowed:
            return Response({"detail": reason}, status=403)
        before = {"is_active": user.is_active}
        user.is_active = False
        user.save(update_fields=["is_active"])
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        OutstandingToken.objects.filter(user=user).delete()
        _audit_user_change(request, user, "user.deactivate", before, {"is_active": False, "sessions_revoked": True})
        return Response({"message": "User deactivated and access tokens revoked."})


class AdminUserTrackingView(APIView):
    """
    GET /api/v1/admin/user-tracking/
    Detailed user tracking: current coordinates, destination views,
    navigation history, and medical emergency / SOS status.
    """
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_capability(request, "users", "view")
        _require_capability(request, "safety", "view")
        users = User.objects.all().select_related("preferred_language")
        tracking_data = []

        for u in users:
            history_items = list(
                VisitHistory.objects.filter(user=u)
                .select_related("destination")
                .order_by("-viewed_at")[:10]
                .values("destination__name", "destination__slug", "destination__city", "viewed_at")
            )
            active_sos = SOSAlert.objects.filter(user=u, status=SOSAlert.Status.ACTIVE).first()
            active_trip = SharedTrip.objects.filter(user=u, is_active=True).first()

            tracking_data.append({
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "bio": u.bio or "Nepal explorer",
                "role": u.role,
                "latitude": float(u.latitude) if u.latitude is not None else None,
                "longitude": float(u.longitude) if u.longitude is not None else None,
                "city": u.city or "Unknown",
                "country": u.country or "Nepal",
                "location_source": u.location_source or "GPS",
                "view_count": u.history.count(),
                "recent_history": history_items,
                "has_medical_emergency": active_sos is not None,
                "emergency_details": {
                    "id": active_sos.id,
                    "message": active_sos.message,
                    "latitude": float(active_sos.latitude) if active_sos.latitude else None,
                    "longitude": float(active_sos.longitude) if active_sos.longitude else None,
                    "triggered_at": active_sos.triggered_at,
                } if active_sos else None,
                "is_navigating": active_trip is not None,
            })

        return Response(tracking_data)


class AdminPendingPlacesView(APIView):
    """
    GET /api/v1/admin/pending-places/
    POST /api/v1/admin/pending-places/<id>/
    """
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_capability(request, "destinations", "view")
        places = Destination.objects.filter(status=Destination.SubmissionStatus.PENDING).select_related("category", "created_by")
        if request.user.role == "district_manager":
            places = places.filter(district__iexact=request.user.managed_district)
        data = []
        for p in places:
            gallery_photos = [
                img.image.url if img.image else img.external_url
                for img in p.gallery.all()
            ]
            cover_url = p.cover_image.url if p.cover_image else (gallery_photos[0] if gallery_photos else None)

            data.append({
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "category_id": p.category_id,
                "category_name": p.category.name if p.category else "Uncategorized",
                "province": p.province or "Gandaki",
                "district": p.district or "",
                "municipality": p.municipality or "",
                "ward_number": p.ward_number,
                "city": p.city or "",
                "address": p.address or "",
                "country": p.country or "Nepal",
                "latitude": float(p.latitude) if p.latitude is not None else None,
                "longitude": float(p.longitude) if p.longitude is not None else None,
                "altitude": p.altitude or "",
                "entry_fee": float(p.entry_fee) if p.entry_fee is not None else 0,
                "opening_hours": p.opening_hours or "",
                "best_time_to_visit": p.best_time_to_visit or "",
                "short_description": p.short_description or "",
                "description": p.description or "",
                "history": p.history or "",
                "nearest_hospital_info": p.nearest_hospital_info or "",
                "nearest_hotel_info": p.nearest_hotel_info or "",
                "nearest_police_info": p.nearest_police_info or "",
                "cover_image_url": cover_url,
                "gallery_urls": gallery_photos,
                "created_by": p.created_by.email if p.created_by else "Community Submitter",
                "created_at": p.created_at,
            })
        return Response(data)

    def post(self, request, id=None):
        _require_capability(request, "destinations", "approve")
        action_type = request.data.get("action", "approve")  # approve or reject
        if not id:
            id = request.data.get("id")
        try:
            place = Destination.objects.get(id=id)
        except Destination.DoesNotExist:
            return Response({"detail": "Place not found."}, status=status.HTTP_404_NOT_FOUND)
        if request.user.role == "district_manager" and (place.district or "").lower() != (request.user.managed_district or "").lower():
            return Response({"detail": "District managers may only moderate their assigned district."}, status=403)

        if action_type == "approve":
            place.status = Destination.SubmissionStatus.APPROVED
            place.is_active = True

            # Allow admin to enrich description, history, best_time, coordinates during approval
            if "name" in request.data and request.data["name"]:
                place.name = request.data["name"]
            if "description" in request.data:
                place.description = request.data["description"]
            if "short_description" in request.data:
                place.short_description = request.data["short_description"]
            if "history" in request.data:
                place.history = request.data["history"]
            if "best_time_to_visit" in request.data:
                place.best_time_to_visit = request.data["best_time_to_visit"]
            if "altitude" in request.data:
                place.altitude = request.data["altitude"]
            if "province" in request.data:
                place.province = request.data["province"]
            if "district" in request.data:
                place.district = request.data["district"]
            if "municipality" in request.data:
                place.municipality = request.data["municipality"]
            if "ward_number" in request.data and request.data["ward_number"]:
                place.ward_number = request.data["ward_number"]
            if "city" in request.data:
                place.city = request.data["city"]
            if "category_id" in request.data and request.data["category_id"]:
                place.category_id = request.data["category_id"]
            if "nearest_hospital_info" in request.data:
                place.nearest_hospital_info = request.data["nearest_hospital_info"]
            if "nearest_hotel_info" in request.data:
                place.nearest_hotel_info = request.data["nearest_hotel_info"]
            if "nearest_police_info" in request.data:
                place.nearest_police_info = request.data["nearest_police_info"]
            if "review_note" in request.data:
                place.review_note = request.data["review_note"]

            place.save()

            # Record audit log
            DestinationAuditLog.objects.create(
                destination=place,
                action=DestinationAuditLog.Action.APPROVED,
                actor=request.user if request.user.is_authenticated else None,
                note="Approved by administrator.",
                previous_status="pending",
                new_status="approved",
            )

            return Response({
                "message": f"Place '{place.name}' accepted & published live to database!",
                "id": place.id,
                "slug": place.slug,
            })
        else:
            place.status = Destination.SubmissionStatus.REJECTED
            place.review_note = request.data.get("review_note", "Does not meet submission guidelines.")
            place.save()

            DestinationAuditLog.objects.create(
                destination=place,
                action=DestinationAuditLog.Action.REJECTED,
                actor=request.user if request.user.is_authenticated else None,
                note=place.review_note,
                previous_status="pending",
                new_status="rejected",
            )

            return Response({"message": f"Place '{place.name}' rejected."})


class AdminPendingImagesView(APIView):
    """
    GET /api/v1/admin/pending-images/
    POST /api/v1/admin/pending-images/<id>/
    """
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_capability(request, "images", "view")
        images = DestinationImage.objects.filter(
            Q(verification_status="pending") | Q(is_verified=False)
        ).select_related("destination", "uploaded_by")
        data = []
        for img in images:
            img_url = img.image.url if img.image else img.external_url
            data.append({
                "id": img.id,
                "destination_id": img.destination_id,
                "destination_name": img.destination.name if img.destination else "Unknown Place",
                "image_url": img_url,
                "caption": img.caption or "",
                "source": img.source,
                "uploaded_by": img.uploaded_by.email if img.uploaded_by else "Community User",
                "verification_status": img.verification_status,
                "created_at": img.created_at,
            })
        return Response(data)

    def post(self, request, id=None):
        _require_capability(request, "images", "approve")
        if not id:
            id = request.data.get("id")
        action_type = request.data.get("action", "approve")
        try:
            img = DestinationImage.objects.get(id=id)
        except DestinationImage.DoesNotExist:
            return Response({"detail": "Image not found."}, status=status.HTTP_404_NOT_FOUND)

        if action_type == "approve":
            img.verification_status = "approved"
            img.is_verified = True
            img.save()
            return Response({"message": "Image verified and added to destination gallery & recommendations."})
        else:
            img.verification_status = "rejected"
            img.is_verified = False
            img.save()
            return Response({"message": "Image rejected."})


class AdminEmergenciesView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_capability(request, "safety", "view")
        alerts = SOSAlert.objects.all().select_related("user").order_by("-triggered_at")
        data = []
        for a in alerts:
            data.append({
                "id": a.id,
                "user_id": a.user_id,
                "user_email": a.user.email if a.user else "Anonymous",
                "user_name": a.user.full_name if a.user else "Traveler",
                "user_phone": str(a.user.phone_number) if a.user and a.user.phone_number else "",
                "latitude": float(a.latitude) if a.latitude is not None else None,
                "longitude": float(a.longitude) if a.longitude is not None else None,
                "message": a.message or "Medical / Safety Emergency Assistance Requested",
                "status": a.status,
                "triggered_at": a.triggered_at,
                "resolved_at": a.resolved_at,
            })
        return Response(data)

    def post(self, request, id=None):
        _require_capability(request, "safety", "change")
        if not id:
            id = request.data.get("id")
        try:
            alert = SOSAlert.objects.get(id=id)
            alert.status = SOSAlert.Status.RESOLVED
            alert.resolved_at = timezone.now()
            alert.save()
            return Response({"message": "Emergency marked as resolved."})
        except SOSAlert.DoesNotExist:
            return Response({"detail": "Emergency alert not found."}, status=status.HTTP_404_NOT_FOUND)


class AdminDestinationsView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        destinations = Destination.objects.all().select_related("category")
        return Response([
            {
                "id": d.id,
                "name": d.name,
                "slug": d.slug,
                "city": d.city,
                "district": d.district,
                "category": d.category.name if d.category else "",
                "status": d.status,
                "average_rating": float(d.average_rating),
                "views_count": d.views_count,
            }
            for d in destinations
        ])

    def post(self, request):
        data = request.data.copy()
        category_id = data.pop("category_id", None)
        destination = Destination.objects.create(**data)
        if category_id:
            destination.category_id = category_id
            destination.save()
        return Response({
            "id": destination.id,
            "slug": destination.slug,
            "message": "Destination created successfully"
        }, status=status.HTTP_201_CREATED)


class AdminDestinationDetailView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request, id):
        """Return full destination data, images, and edit history for admin."""
        try:
            destination = Destination.objects.get(id=id)
        except Destination.DoesNotExist:
            return Response({"detail": "Destination not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "id": destination.id,
            "name": destination.name,
            "slug": destination.slug,
            "description": destination.description,
            "short_description": destination.short_description,
            "category": getattr(destination.category, "name", None),
            "city": destination.city,
            "district": destination.district,
            "province": destination.province,
            "latitude": float(destination.latitude) if destination.latitude else None,
            "longitude": float(destination.longitude) if destination.longitude else None,
            "cover_image": _cover_of(destination),
            "gallery": [
                {
                    "id": g.id,
                    "url": g.external_url or (g.image.url if g.image else ""),
                    "caption": g.caption,
                    "is_cover": g.is_cover,
                    "source": g.source_platform or g.source,
                    "photographer": g.photographer,
                    "license": g.license_type,
                    "source_url": g.source_url,
                    "created_at": g.created_at,
                }
                for g in destination.gallery.all()[:50]
            ],
            "history": [
                {
                    "id": h.id,
                    "action": h.action,
                    "note": h.note,
                    "actor": str(h.actor) if h.actor else "system",
                    "previous_status": h.previous_status,
                    "new_status": h.new_status,
                    "created_at": h.created_at,
                }
                for h in destination.audit_log.all()[:50]
            ],
            "bookings_count": getattr(destination, "bookings", None).__class__ and destination.bookings.count() if hasattr(destination, "bookings") else 0,
            "reviews_count": destination.reviews.count() if hasattr(destination, "reviews") else 0,
            "views_count": destination.views_count,
            "created_at": destination.created_at,
            "updated_at": destination.updated_at,
        })

    def put(self, request, id):
        try:
            destination = Destination.objects.get(id=id)
        except Destination.DoesNotExist:
            return Response({"detail": "Destination not found."}, status=status.HTTP_404_NOT_FOUND)

        editable = {
            "name", "description", "short_description", "city", "district",
            "province", "latitude", "longitude", "entry_fee", "opening_hours",
            "best_time_to_visit", "history", "cultural_significance", "website",
        }
        changed = []
        for key, value in request.data.items():
            if key in editable and hasattr(destination, key):
                if getattr(destination, key) != value:
                    changed.append(key)
                setattr(destination, key, value)
        destination.save()
        _sync_destination_json(destination)
        if changed:
            DestinationAuditLog.objects.create(
                destination=destination, actor=request.user if request.user.is_authenticated else None,
                action=DestinationAuditLog.Action.EDITED,
                note=f"Admin updated fields: {', '.join(changed)}",
            )
        return Response({"message": "Destination updated successfully", "changed": changed})

    def delete(self, request, id):
        Destination.objects.filter(id=id).delete()
        return Response({"message": "Destination deleted successfully"})


class AdminDestinationImageView(APIView):
    """
    Admin image management for a destination:
      POST   {image_url, caption, source, photographer, license, source_url}
             -> add a new image (optionally set as cover)
      PATCH  {image_id, is_cover: true}  -> set primary image / rollback
      PATCH  {image_url}                  -> change cover image directly
      DELETE {image_id}                   -> remove an image
    Changes are written straight to the database and reflected immediately.
    """
    permission_classes = [IsAdminOrStaff]

    def _dest(self, id):
        return Destination.objects.filter(id=id).first()

    def post(self, request, id):
        destination = self._dest(id)
        if not destination:
            return Response({"detail": "Destination not found."}, status=404)
        uploaded_file = request.FILES.get("image") or request.FILES.get("file")
        image_url = (request.data.get("image_url") or request.data.get("url") or "").strip()
        if not image_url and not uploaded_file:
            return Response({"detail": "image file or image_url is required."}, status=400)

        is_cover = str(request.data.get("is_cover", "")).lower() in {"1", "true", "yes", "on"}
        if is_cover:
            destination.gallery.filter(is_cover=True).update(is_cover=False)

        img = DestinationImage.objects.create(
            destination=destination,
            external_url=image_url if image_url.startswith("http") else "",
            image=uploaded_file or (image_url if image_url and not image_url.startswith("http") else None),
            caption=(request.data.get("caption") or destination.name)[:200],
            is_cover=is_cover,
            source=DestinationImage.Source.ADMIN,
            source_url=request.data.get("source_url", "")[:500],
            source_platform=request.data.get("source", "admin")[:100],
            photographer=request.data.get("photographer", "")[:150],
            license_type=request.data.get("license", "Admin-provided")[:100],
            uploaded_by=request.user if request.user.is_authenticated else None,
            copyright_status="verified_reusable" if request.data.get("reusable") else "admin_uploaded",
            verification_status="approved",
            is_verified=True,
        )
        display_url = img.external_url or (img.image.url if img.image else "")
        if image_url and (is_cover or not destination.cover_image):
            Destination.objects.filter(pk=destination.pk).update(cover_image=image_url)

        DestinationAuditLog.objects.create(
            destination=destination, actor=request.user if request.user.is_authenticated else None,
            action=DestinationAuditLog.Action.EDITED, note=f"Admin added image {display_url[:80]}",
        )
        _sync_destination_json(destination)
        return Response({"message": "Image added", "image_id": img.id, "cover_url": display_url}, status=201)

    def patch(self, request, id):
        destination = self._dest(id)
        if not destination:
            return Response({"detail": "Destination not found."}, status=404)

        # Set an existing gallery image as cover (rollback / primary select)
        image_id = request.data.get("image_id")
        if image_id:
            img = destination.gallery.filter(id=image_id).first()
            if not img:
                return Response({"detail": "Image not found."}, status=404)
            editable = {"caption", "ordering", "verification_status", "is_verified", "alt_text"}
            changed = []
            for field in editable:
                if field in request.data:
                    setattr(img, field, request.data[field]); changed.append(field)
            make_cover = str(request.data.get("is_cover", "")).lower() in {"1", "true", "yes"}
            if make_cover:
                destination.gallery.filter(is_cover=True).exclude(id=img.id).update(is_cover=False)
                img.is_cover = True; changed.append("is_cover")
            if changed: img.save(update_fields=list(set(changed)))
            cover = img.external_url or (img.image.url if img.image else "")
            if make_cover: Destination.objects.filter(pk=destination.pk).update(cover_image=cover)
            DestinationAuditLog.objects.create(destination=destination, actor=request.user if request.user.is_authenticated else None, action=DestinationAuditLog.Action.EDITED, note=f"Admin updated image #{img.id}: {', '.join(changed)}")
            _sync_destination_json(destination)
            return Response({"message": "Image updated", "cover_url": cover, "changed": changed})

        # Directly change the cover URL
        image_url = (request.data.get("image_url") or "").strip()
        if image_url:
            Destination.objects.filter(pk=destination.pk).update(cover_image=image_url)
            return Response({"message": "Cover URL updated", "cover_url": image_url})

        return Response({"detail": "Provide image_id or image_url."}, status=400)

    def delete(self, request, id):
        destination = self._dest(id)
        if not destination:
            return Response({"detail": "Destination not found."}, status=404)
        image_id = request.data.get("image_id") or request.query_params.get("image_id")
        if not image_id:
            return Response({"detail": "image_id is required."}, status=400)
        img = destination.gallery.filter(id=image_id).first()
        if not img:
            return Response({"detail": "Image not found."}, status=404)
        was_cover = img.is_cover
        img.delete()
        if was_cover:
            next_img = destination.gallery.first()
            new_cover = next_img.external_url if next_img and next_img.external_url else ""
            if next_img:
                next_img.is_cover = True
                next_img.save(update_fields=["is_cover"])
            Destination.objects.filter(pk=destination.pk).update(cover_image=new_cover)
        return Response({"message": "Image removed"})


def _cover_of(destination):
    raw = str(destination.cover_image or "").strip()
    if raw.startswith("http"):
        return raw
    cover = destination.gallery.filter(is_cover=True).first()
    if cover and cover.external_url:
        return cover.external_url
    from . import photo_catalog
    return photo_catalog.resolve_cover_photo(destination)["url"]


class AdminAlertsView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        alerts = Alert.objects.all().order_by("-created_at")
        return Response([
            {
                "id": a.id,
                "title": a.title,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "description": a.description,
                "city": a.city,
                "is_active": a.is_active,
                "created_at": a.created_at,
            }
            for a in alerts
        ])

    def post(self, request):
        alert = Alert.objects.create(**request.data)
        return Response({"id": alert.id, "message": "Alert created successfully"}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# User details + verification / feedback
# ---------------------------------------------------------------------------
class AdminUsersDetailView(APIView):
    """Security-conscious user profile, activity summary and role history."""
    permission_classes = [IsAdminOrStaff]

    def get(self, request, id):
        _require_capability(request, "users", "view")
        u = User.objects.filter(pk=id).first()
        if not u:
            return Response({"detail": "not found"}, status=404)
        from audit.models import AuditLog
        role_history = AuditLog.objects.filter(
            object_type="User", object_id=str(u.id), action__startswith="user."
        )[:20]
        visits = u.history.select_related("destination").order_by("-viewed_at")[:10]
        return Response({
            "id": u.id, "email": u.email, "full_name": u.full_name,
            "first_name": u.first_name, "last_name": u.last_name, "bio": u.bio,
            "phone_number": str(u.phone_number or ""), "role": u.role,
            "is_verified": u.is_verified, "phone_verified": u.phone_verified,
            "is_active": u.is_active, "is_staff": u.is_staff,
            "is_superuser": u.is_superuser, "auth_provider": u.auth_provider,
            "date_joined": u.date_joined, "last_login": u.last_login,
            "city": u.city, "country": u.country, "managed_district": u.managed_district,
            "activity": {"visits": u.history.count(), "favorites": u.favorites.count(),
                         "reviews": u.reviews.count(), "feedback": u.feedbacks.count(),
                         "emergencies": u.sos_alerts.count()},
            "recent_visits": [{"destination": v.destination.name, "slug": v.destination.slug,
                               "viewed_at": v.viewed_at} for v in visits],
            "role_history": [{"action": x.action, "timestamp": x.timestamp,
                              "actor": x.user_email, "changes": x.extra} for x in role_history],
        })

    def patch(self, request, id):
        return UpdateUserStatusView().put(request, id)


class AdminUserAccessActionView(APIView):
    permission_classes = [IsAdminOrStaff]

    def post(self, request, id):
        _require_capability(request, "users", "change")
        u = User.objects.filter(pk=id).first()
        if not u:
            return Response({"detail": "not found"}, status=404)
        allowed, reason = _can_manage_user(request.user, u)
        if not allowed:
            return Response({"detail": reason}, status=403)
        action = request.data.get("action")
        if action == "revoke_sessions":
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
            count, _ = OutstandingToken.objects.filter(user=u).delete()
            _audit_user_change(request, u, "user.sessions.revoke", {}, {"tokens_removed": count})
            return Response({"message": "All recorded refresh sessions were revoked.", "tokens_removed": count})
        if action in {"verify", "unverify"}:
            before = {"is_verified": u.is_verified}
            u.is_verified = action == "verify"
            u.save(update_fields=["is_verified"])
            _audit_user_change(request, u, f"user.{action}", before, {"is_verified": u.is_verified})
            return Response({"message": "Verification updated.", "is_verified": u.is_verified})
        return Response({"detail": "Unsupported action."}, status=400)


class AdminSendVerificationView(APIView):
    """Send a verification reminder through configured channels."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request, id):
        _require_capability(request, "users", "change")
        from django.core.mail import send_mail
        from django.conf import settings as djsettings
        User = get_user_model()
        u = User.objects.filter(pk=id).first()
        if not u:
            return Response({"detail": "not found"}, status=404)

        message = request.data.get(
            "message",
            f"Hello {u.first_name or u.email}, please verify your email "
            f"to access all features of Nepal Tourism Platform."
        )
        subject = request.data.get("subject", "Please verify your account")
        channel = request.data.get("channel", "email")  # email | sms

        sent = []
        if channel in ("email", "both") and u.email:
            try:
                send_mail(subject, message, djsettings.DEFAULT_FROM_EMAIL, [u.email],
                          fail_silently=False)
                sent.append("email")
            except Exception as exc:  # noqa: BLE001
                return Response({"detail": f"email failed: {exc}"}, status=502)

        if channel in ("sms", "both") and u.phone_number:
            try:
                from twilio.rest import Client  # type: ignore
                sid = getattr(djsettings, "TWILIO_ACCOUNT_SID", "")
                token = getattr(djsettings, "TWILIO_AUTH_TOKEN", "")
                from_ = getattr(djsettings, "TWILIO_PHONE_NUMBER", "")
                if sid and token:
                    Client(sid, token).messages.create(
                        to=u.phone_number, from_=from_, body=message[:1600])
                    sent.append("sms")
            except Exception as exc:  # noqa: BLE001
                return Response({"detail": f"sms failed: {exc}"}, status=502)

        return Response({"message": f"sent via {', '.join(sent) or 'none'}",
                         "channels": sent, "is_verified": u.is_verified})


class InfrastructureModerationView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request, id=None):
        _require_capability(request, "destinations", "view")
        qs = InfrastructureSubmission.objects.select_related("submitted_by", "destination", "reviewed_by")
        requested_status = request.query_params.get("status")
        if requested_status:
            qs = qs.filter(status=requested_status)
        if id:
            item = qs.filter(pk=id).first()
            if not item:
                return Response({"detail": "Submission not found."}, status=404)
            return Response(InfrastructureSubmissionSerializer(item, context={"request": request}).data)
        return Response(InfrastructureSubmissionSerializer(qs[:300], many=True, context={"request": request}).data)

    def post(self, request, id=None):
        _require_capability(request, "destinations", "approve")
        item = InfrastructureSubmission.objects.filter(pk=id).first()
        if not item:
            return Response({"detail": "Submission not found."}, status=404)
        action = request.data.get("action")
        note = request.data.get("admin_note", "")
        if action == "approve":
            try:
                from .community_data_service import publish_submission
                publish_submission(item, request.user, note)
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=400)
        elif action in {"reject", "needs_changes"}:
            item.status = "rejected" if action == "reject" else "needs_changes"
            item.admin_note = note
            item.reviewed_by = request.user
            item.reviewed_at = timezone.now()
            item.save()
        else:
            return Response({"detail": "action must be approve, reject, or needs_changes"}, status=400)
        return Response(InfrastructureSubmissionSerializer(item, context={"request": request}).data)


class MLDataPipelineView(APIView):
    """Approve feedback, synchronize CSVs, and optionally run whitelisted trainers."""
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_capability(request, "datasets", "view")
        return Response([{
            "id": run.id, "model_type": run.model_type, "status": run.status,
            "version": run.version, "previous_version": run.previous_version,
            "dataset_size": run.dataset_size, "newly_approved_records": run.newly_approved_records,
            "validation_metrics": run.validation_metrics, "started_at": run.started_at,
            "completed_at": run.completed_at, "requested_by": run.requested_by_id,
        } for run in MLTrainingRun.objects.all()[:100]])

    def post(self, request):
        _require_capability(request, "datasets", "train" if request.data.get("train") else "export")
        import subprocess
        import sys
        from pathlib import Path
        from .community_data_service import export_verified_ml_feedback

        record_type = request.data.get("record_type")
        record_id = request.data.get("record_id")
        if record_type and record_id:
            if record_type == "budget":
                record = TravelExpenseFeedback.objects.filter(pk=record_id).first()
                if not record:
                    return Response({"detail": "Budget feedback not found."}, status=404)
                record.is_employee_verified = True
                record.save(update_fields=["is_employee_verified", "updated_at"])
            elif record_type == "risk":
                record = TravelRiskFeedback.objects.filter(pk=record_id).first()
                if not record:
                    return Response({"detail": "Risk feedback not found."}, status=404)
                record.is_admin_verified = True
                record.reviewed_by = request.user
                record.reviewed_at = timezone.now()
                record.save(update_fields=["is_admin_verified", "reviewed_by", "reviewed_at", "updated_at"])
            else:
                return Response({"detail": "record_type must be budget or risk."}, status=400)

        exported = export_verified_ml_feedback()
        results = {}
        if bool(request.data.get("train", False)):
            root = Path(settings.BASE_DIR).parent
            commands = {
                "budget": [sys.executable, "training/train_budget_model.py"],
                "risk": [sys.executable, "training/train_risk_model.py"],
                "recommendation": [sys.executable, "training/train_recommendation_model.py"],
                "destination": [sys.executable, "training/train_destination_model.py"],
                "hotel": [sys.executable, "training/train_destination_model.py"],
                "route": [sys.executable, "training/build_route_graph.py"],
            }
            requested = request.data.get("models") or list(commands)
            for model_name in requested:
                if model_name not in commands:
                    continue
                previous = MLTrainingRun.objects.filter(model_type=model_name, status="succeeded").first()
                version = f"{model_name}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                dataset_size = (
                    TravelExpenseFeedback.objects.filter(is_employee_verified=True).count() if model_name == "budget"
                    else TravelRiskFeedback.objects.filter(is_admin_verified=True).count() if model_name == "risk"
                    else Destination.objects.filter(is_active=True, status="approved").count()
                )
                training_run = MLTrainingRun.objects.create(
                    model_type=model_name, status="running", version=version,
                    previous_version=previous.version if previous else "", dataset_size=dataset_size,
                    newly_approved_records=InfrastructureSubmission.objects.filter(status="approved").count(),
                    requested_by=request.user, started_at=timezone.now(),
                )
                try:
                    process = subprocess.run(
                        commands[model_name], cwd=root / "ml_service", capture_output=True,
                        text=True, timeout=180, check=False,
                    )
                    success = process.returncode == 0
                    output = (process.stdout or process.stderr)[-1200:]
                    results[model_name] = {"success": success, "version": version, "output": output}
                    training_run.status = "succeeded" if success else "failed"
                    training_run.output_log = output
                    training_run.validation_metrics = {"process_return_code": process.returncode}
                    training_run.completed_at = timezone.now()
                    training_run.save()
                except (subprocess.TimeoutExpired, OSError) as exc:
                    results[model_name] = {"success": False, "version": version, "output": str(exc)}
                    training_run.status = "failed"
                    training_run.output_log = str(exc)
                    training_run.completed_at = timezone.now()
                    training_run.save()
        return Response({"exported": exported, "training": results, "message": "Only admin-verified rows were exported."})


class AdminDataExplorerView(APIView):
    """Searchable, paginated read view across admin-owned application models."""
    permission_classes = [IsAdminOrStaff]

    RESOURCES = {
        "destinations": ("tourist.Destination", ["name","slug","city","district","province","status"]),
        "destination_features": ("tourist.DestinationFeatureProfile", ["destination__name","difficulty","budget_level","source_type"]),
        "destination_images": ("tourist.DestinationImage", ["destination__name","caption","external_url","source","verification_status"]),
        "destination_translations": ("tourist.DestinationTranslation", ["destination__name","name","language__name"]),
        "categories": ("tourist.Category", ["name","slug"]),
        "languages": ("tourist.Language", ["name","code"]),
        "hotels": ("tourist.Hotel", ["name","destination__name","address","phone"]),
        "bookings": ("booking.Booking", ["user__email","hotel__name","status"]),
        "hotel_reviews": ("booking.HotelReview", ["user__email","hotel__name","comment"]),
        "reviews": ("tourist.Review", ["destination__name","user__email","comment"]),
        "ratings": ("tourist.Rating", ["destination__name","user__email"]),
        "favorites": ("tourist.Favorite", ["destination__name","user__email"]),
        "visit_history": ("tourist.VisitHistory", ["destination__name","user__email"]),
        "family_links": ("tourist.FamilyLink", ["requester__email","member__email","relationship","status"]),
        "email_tokens": ("tourist.EmailVerificationToken", ["user__email"]),
        "alerts": ("tourist.Alert", ["title","description","city","district","source"]),
        "current_hazards": ("tourist.CurrentHazard", ["destination__name","title","source_name","severity"]),
        "emergency_contacts": ("tourist.EmergencyContact", ["name","city","address","phone_number"]),
        "osm_services": ("tourist.OSMEssentialService", ["name","category","address","phone"]),
        "osm_places": ("tourist.OSMTourismPlace", ["name","category","address"]),
        "budgets": ("tourist.Budget", ["user__email","title","category","currency"]),
        "feedback": ("tourist.UserFeedback", ["user__email","name","email","subject","message","category"]),
        "feedback_evidence": ("tourist.FeedbackEvidence", ["feedback__subject","caption","media_type"]),
        "audit_logs": ("audit.AuditLog", ["action","message","object_type","user_email","endpoint"]),
        "error_events": ("audit.ErrorEvent", ["error_type","error_message","endpoint","component"]),
    }

    def get(self, request):
        from django.apps import apps
        from django.db.models import Q
        from django.forms.models import model_to_dict
        resource = request.query_params.get("resource", "destinations")
        module_map = {"destinations":"destinations","destination_features":"destinations","destination_images":"images","destination_translations":"content","categories":"destinations","languages":"content","hotels":"hotels","bookings":"hotels","hotel_reviews":"reviews","reviews":"reviews","ratings":"reviews","favorites":"users","visit_history":"users","family_links":"users","email_tokens":"users","alerts":"safety","current_hazards":"safety","emergency_contacts":"safety","osm_services":"safety","osm_places":"destinations","budgets":"budget","feedback":"feedback","feedback_evidence":"feedback","audit_logs":"audit","error_events":"audit"}
        user = request.user
        if not (user.is_superuser or user.role in {"admin","super_admin","tourism_admin"}):
            profile = getattr(user, "capability_profile", None)
            if not profile or not profile.allows(module_map.get(resource, "settings"), "view"):
                return Response({"detail": "Staff capability denied."}, status=403)
        if resource not in self.RESOURCES:
            return Response({"detail": "Unknown resource."}, status=400)
        label, search_fields = self.RESOURCES[resource]
        model = apps.get_model(label)
        qs = model.objects.all().order_by("-pk")
        query = request.query_params.get("q", "").strip()
        if query:
            search = Q()
            for field in search_fields:
                search |= Q(**{f"{field}__icontains": query})
            qs = qs.filter(search)
        count = qs.count()
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = max(10, min(100, int(request.query_params.get("page_size", 25))))
        except (TypeError, ValueError):
            return Response({"detail": "Invalid pagination."}, status=400)
        start = (page - 1) * page_size
        rows = []
        for obj in qs[start:start + page_size]:
            raw = model_to_dict(obj)
            row = {"id": obj.pk, "record": str(obj)}
            for key, value in raw.items():
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                elif hasattr(value, "name"):
                    value = value.name
                elif isinstance(value, (list, tuple, set)):
                    value = ", ".join(map(str, value))
                row[key] = value
            rows.append(row)
        preferred = ["id","record"]
        if rows:
            preferred += [key for key in rows[0].keys() if key not in preferred][:10]
        total_pages = max(1, (count + page_size - 1) // page_size)
        return Response({"resource": resource, "count": count, "page": page, "page_size": page_size, "total_pages": total_pages, "columns": preferred, "results": rows})


class StaffWorkspaceView(APIView):
    """Capability and assignment scoped operational queues for staff users."""
    permission_classes = [IsAdminOrStaff]

    def _districts(self, user):
        profile = getattr(user, "capability_profile", None)
        districts = list(profile.managed_districts or []) if profile else []
        if user.managed_district and user.managed_district not in districts:
            districts.append(user.managed_district)
        return [value.strip() for value in districts if value and value.strip()]

    def _scope_destinations(self, queryset, user, prefix=""):
        districts = self._districts(user)
        if districts:
            return queryset.filter(**{f"{prefix}district__in": districts})
        return queryset

    def get(self, request):
        module = request.query_params.get("module", "dashboard")
        if module != "dashboard":
            _require_capability(request, module, "view")
        user = request.user
        profile = getattr(user, "capability_profile", None)
        capabilities = {key: value for key, value in (profile.capabilities if profile and profile.is_active else {}).items()}
        if user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}:
            capabilities = {key: ["*"] for key in StaffCapabilityProfile.MODULES}
        from admin_panel.models import AdminTask, HotelAssignment
        tasks = AdminTask.objects.filter(assigned_to=user).select_related("related_hotel").order_by("-priority", "due_date")
        today = timezone.now().date()
        task_rows = [{"id": row.id, "title": row.title, "description": row.description,
            "status": row.status, "priority": row.priority, "due_date": row.due_date,
            "hotel": row.related_hotel.name if row.related_hotel else None} for row in tasks[:50]]
        base = {"module": module, "capabilities": capabilities, "managed_districts": self._districts(user),
                "tasks": task_rows, "task_summary": {"pending": tasks.filter(status="pending").count(),
                "in_progress": tasks.filter(status="in_progress").count(), "completed": tasks.filter(status="completed").count(),
                "overdue": tasks.filter(due_date__lt=today).exclude(status__in=["completed", "cancelled"]).count()}}
        rows = []
        if module == "dashboard":
            queue_counts = {}
            if _has_capability(request, "destinations", "view"):
                queue_counts["destinations"] = self._scope_destinations(Destination.objects.filter(status="pending"), user).count()
            if _has_capability(request, "images", "view"):
                queue_counts["images"] = self._scope_destinations(DestinationImage.objects.filter(verification_status="pending"), user, "destination__").count()
            if _has_capability(request, "reviews", "view"):
                queue_counts["reviews"] = self._scope_destinations(Review.objects.filter(moderation_status="pending"), user, "destination__").count()
            if _has_capability(request, "safety", "view"):
                queue_counts["safety"] = self._scope_destinations(CurrentHazard.objects.filter(is_active=True, verified=False), user, "destination__").count()
            if _has_capability(request, "feedback", "view"):
                queue_counts["feedback"] = UserFeedback.objects.filter(Q(assigned_to=user) | Q(assigned_to__isnull=True)).exclude(status__in=["resolved", "closed", "archived"]).count()
            base["queue_counts"] = queue_counts
        elif module == "destinations":
            queryset = self._scope_destinations(Destination.objects.filter(status="pending").select_related("created_by"), user)
            rows = [{"id": x.id, "title": x.name, "subtitle": x.district or x.city, "status": x.status,
                     "description": x.short_description or x.description[:240], "created_at": x.created_at} for x in queryset[:100]]
        elif module == "images":
            queryset = self._scope_destinations(DestinationImage.objects.filter(verification_status="pending").select_related("destination"), user, "destination__")
            rows = [{"id": x.id, "title": x.destination.name, "subtitle": x.caption or x.source,
                     "status": x.verification_status, "image_url": x.external_url or (x.image.url if x.image else ""), "created_at": x.created_at} for x in queryset[:100]]
        elif module == "budget":
            queryset = self._scope_destinations(TravelExpenseFeedback.objects.select_related("destination", "user"), user, "destination__")
            rows = [{"id": x.id, "title": x.destination_name, "subtitle": f"{x.num_days} days · {x.num_people} people",
                     "status": "verified" if x.is_employee_verified else "submitted", "amount": x.total_cost, "created_at": x.created_at} for x in queryset[:100]]
        elif module == "safety":
            queryset = self._scope_destinations(CurrentHazard.objects.filter(is_active=True).select_related("destination"), user, "destination__")
            rows = [{"id": x.id, "title": x.title, "subtitle": x.destination.name, "status": "verified" if x.verified else "unverified",
                     "severity": x.severity, "description": x.description, "created_at": x.created_at} for x in queryset[:100]]
        elif module == "reviews":
            from booking.models import HotelReview
            queryset = self._scope_destinations(Review.objects.filter(moderation_status="pending").select_related("destination", "user"), user, "destination__")
            rows = [{"id": x.id, "type": "destination", "title": x.destination.name, "subtitle": x.user.email,
                     "status": x.moderation_status, "description": x.comment, "created_at": x.created_at} for x in queryset[:100]]
            hotel_reviews = HotelReview.objects.filter(moderation_status="pending").select_related("hotel__destination", "user")
            assigned_hotel_ids = list(HotelAssignment.objects.filter(admin=user).values_list("hotel_id", flat=True))
            if user.role == "hotel_manager" or assigned_hotel_ids:
                hotel_reviews = hotel_reviews.filter(hotel_id__in=assigned_hotel_ids)
            else:
                hotel_reviews = self._scope_destinations(hotel_reviews, user, "hotel__destination__")
            rows.extend({"id": x.id, "type": "hotel", "title": x.hotel.name, "subtitle": x.user.email,
                         "status": x.moderation_status, "description": x.comment, "amount": x.rating,
                         "created_at": x.created_at} for x in hotel_reviews[:100])
            rows.sort(key=lambda row: row["created_at"], reverse=True)
            rows = rows[:100]
        elif module == "hotels":
            hotel_ids = HotelAssignment.objects.filter(admin=user).values_list("hotel_id", flat=True)
            queryset = Hotel.objects.filter(id__in=hotel_ids).select_related("destination") if not user.is_superuser else Hotel.objects.select_related("destination")
            rows = [{"id": x.id, "title": x.name, "subtitle": x.destination.name, "status": x.booking_status,
                     "description": x.address, "amount": x.price_per_night} for x in queryset[:100]]
        elif module == "content":
            queryset = ContentSection.objects.filter(status__in=["draft", "scheduled"]).select_related("page")
            rows = [{"id": x.id, "title": x.title or x.key, "subtitle": x.page.title, "status": x.status,
                     "description": x.body[:240], "created_at": x.created_at} for x in queryset[:100]]
        elif module == "feedback":
            queryset = UserFeedback.objects.filter(Q(assigned_to=user) | Q(assigned_to__isnull=True)).exclude(status__in=["archived"])
            rows = [{"id": x.id, "title": x.subject, "subtitle": x.email, "status": x.status,
                     "description": x.message[:240], "priority": x.priority, "created_at": x.created_at} for x in queryset[:100]]
        base["results"] = rows
        return Response(base)

    def post(self, request):
        module = request.data.get("module")
        action = request.data.get("action")
        object_id = request.data.get("id")
        if module == "tasks":
            from admin_panel.models import AdminTask
            task = AdminTask.objects.filter(pk=object_id, assigned_to=request.user).first()
            if not task or action not in {"in_progress", "completed"}:
                return Response({"detail": "Invalid task action"}, status=400)
            task.status = action
            task.completed_at = timezone.now() if action == "completed" else None
            task.save(update_fields=["status", "completed_at", "updated_at"])
            return Response({"message": "Task status updated", "status": task.status})
        required = "approve" if action in {"approve", "reject"} else "change"
        _require_capability(request, module, required)
        districts = self._districts(request.user)
        if module == "destinations":
            obj = Destination.objects.filter(pk=object_id, status="pending").first()
            if not obj or (districts and obj.district not in districts):
                return Response({"detail": "Record is outside your assigned queue"}, status=404)
            obj.status = "approved" if action == "approve" else "rejected"; obj.is_active = action == "approve"; obj.save(update_fields=["status", "is_active", "updated_at"])
        elif module == "images":
            obj = DestinationImage.objects.select_related("destination").filter(pk=object_id).first()
            if not obj or (districts and obj.destination.district not in districts):
                return Response({"detail": "Record is outside your assigned queue"}, status=404)
            obj.verification_status = "approved" if action == "approve" else "rejected"; obj.is_verified = action == "approve"; obj.save(update_fields=["verification_status", "is_verified"])
        elif module == "reviews":
            review_type = request.data.get("type", "destination")
            if review_type == "hotel":
                from booking.models import HotelReview
                from admin_panel.models import HotelAssignment
                obj = HotelReview.objects.select_related("hotel__destination").filter(pk=object_id).first()
                assigned = obj and HotelAssignment.objects.filter(admin=request.user, hotel=obj.hotel).exists()
                has_assignments = HotelAssignment.objects.filter(admin=request.user).exists()
                in_district = obj and (not districts or obj.hotel.destination.district in districts)
                allowed = assigned if request.user.role == "hotel_manager" or has_assignments else in_district
                if not obj or not allowed:
                    return Response({"detail": "Record is outside your assigned queue"}, status=404)
                obj.moderation_status = "approved" if action == "approve" else "flagged"; obj.moderated_by = request.user; obj.moderated_at = timezone.now(); obj.save(update_fields=["moderation_status", "moderated_by", "moderated_at"])
            else:
                obj = Review.objects.select_related("destination").filter(pk=object_id).first()
                if not obj or (districts and obj.destination.district not in districts):
                    return Response({"detail": "Record is outside your assigned queue"}, status=404)
                obj.moderation_status = "approved" if action == "approve" else "flagged"; obj.is_flagged = action != "approve"; obj.moderated_by = request.user; obj.moderated_at = timezone.now(); obj.save(update_fields=["moderation_status", "is_flagged", "moderated_by", "moderated_at", "updated_at"])
        else:
            return Response({"detail": "Unsupported workspace action"}, status=400)
        from audit.models import AuditLog
        AuditLog.objects.create(user=request.user, user_email=request.user.email, actor_role=request.user.role,
            category="moderation", severity="info", source="backend", action=f"staff.{module}.{action}",
            message=f"Staff {action} on {module} #{object_id}", object_type=type(obj).__name__, object_id=str(object_id),
            extra={"managed_districts": districts})
        return Response({"message": f"{action.title()} complete"})


class StaffCapabilityManagementView(APIView):
    permission_classes = [IsAdminOrStaff]
    def _admin(self, request):
        return request.user.is_superuser or request.user.role in {"admin","super_admin","tourism_admin"}
    def get(self, request):
        if not self._admin(request): return Response({"detail":"Admin only"},status=403)
        staff=User.objects.filter(role__in=["staff","guide","content_moderator","district_manager","hotel_manager","tourist_police","hospital_staff","rescue_team","emergency_operator"]).order_by("email")
        return Response({"modules":StaffCapabilityProfile.MODULES,"actions":StaffCapabilityProfile.ACTIONS,"results":[{"user_id":u.id,"email":u.email,"name":u.full_name,"role":u.role,"capabilities":getattr(getattr(u,"capability_profile",None),"capabilities",{}),"managed_districts":getattr(getattr(u,"capability_profile",None),"managed_districts",[]),"is_active":getattr(getattr(u,"capability_profile",None),"is_active",False)} for u in staff]})
    def put(self, request):
        if not self._admin(request): return Response({"detail":"Admin only"},status=403)
        user=User.objects.filter(pk=request.data.get("user_id")).first()
        if not user or user.role in {"admin","super_admin","tourism_admin"}: return Response({"detail":"Invalid staff user"},status=400)
        profile,_=StaffCapabilityProfile.objects.get_or_create(user=user)
        old = {"capabilities": profile.capabilities, "managed_districts": profile.managed_districts, "is_active": profile.is_active}
        profile.capabilities=request.data.get("capabilities",{})
        districts = request.data.get("managed_districts", [])
        if not isinstance(districts, list) or any(not isinstance(value, str) or len(value.strip()) > 100 for value in districts):
            return Response({"detail": "Managed districts must be a list of valid district names"}, status=400)
        profile.managed_districts=list(dict.fromkeys(value.strip() for value in districts if value.strip()))
        profile.is_active=bool(request.data.get("is_active",True));profile.assigned_by=request.user
        try: profile.full_clean()
        except Exception as exc: return Response({"detail":str(exc)},status=400)
        profile.save()
        from audit.models import AuditLog
        AuditLog.objects.create(user=request.user, user_email=request.user.email, actor_role=request.user.role,
            category="security", severity="warning", source="backend", action="staff.capabilities.update",
            message=f"Updated staff workspace assignment for {user.email}", object_type="StaffCapabilityProfile",
            object_id=str(profile.id), extra={"before": old, "after": {"capabilities": profile.capabilities,
            "managed_districts": profile.managed_districts, "is_active": profile.is_active}})
        return Response({"message":"Capabilities updated","user_id":user.id})


class AdminBrandingView(APIView):
    """Safe branding assets and allowlisted theme presets; never accepts CSS or scripts."""
    permission_classes = [IsAdminOrStaff]
    PRESETS = {
        "himalayan": {"primary_color": "#0B3D91", "secondary_color": "#F59E0B", "background_color": "#F8FAFC", "surface_color": "#FFFFFF", "border_radius": "rounded", "density": "comfortable", "sidebar_style": "dark"},
        "heritage": {"primary_color": "#8B1E3F", "secondary_color": "#D97706", "background_color": "#FFFBEB", "surface_color": "#FFFFFF", "border_radius": "soft", "density": "comfortable", "sidebar_style": "heritage"},
        "forest": {"primary_color": "#166534", "secondary_color": "#C2410C", "background_color": "#F0FDF4", "surface_color": "#FFFFFF", "border_radius": "rounded", "density": "compact", "sidebar_style": "dark"},
    }
    TEXT_FIELDS = {"site_title", "tagline", "footer_text", "contact_email", "contact_phone"}
    SOCIAL_FIELDS = {"facebook_url", "instagram_url", "twitter_url", "youtube_url"}

    def _setting(self):
        return SiteSetting.objects.get_or_create(key="branding", defaults={"value": {}, "description": "Public platform branding", "is_public": True})[0]

    def get(self, request):
        _require_capability(request, "settings", "view")
        setting = self._setting()
        assets = {asset.kind: {"id": asset.id, "url": asset.file.url, "alt_text": asset.alt_text,
            "width": asset.width, "height": asset.height, "file_size": asset.file_size,
            "updated_at": asset.updated_at} for asset in BrandingAsset.objects.all()}
        return Response({"setting_id": setting.id, "branding": setting.value, "assets": assets, "presets": self.PRESETS})

    def patch(self, request):
        _require_capability(request, "settings", "change")
        import re
        setting = self._setting(); before = dict(setting.value or {})
        data = request.data.get("branding") or {}
        if not isinstance(data, dict):
            return Response({"detail": "Branding must be structured data"}, status=400)
        unknown = set(data) - self.TEXT_FIELDS - self.SOCIAL_FIELDS - {"theme_preset"}
        if unknown:
            return Response({"detail": f"Unsupported branding fields: {', '.join(sorted(unknown))}"}, status=400)
        preset = data.get("theme_preset", before.get("theme_preset", "himalayan"))
        if preset not in self.PRESETS:
            return Response({"detail": "Unknown theme preset"}, status=400)
        for field in self.SOCIAL_FIELDS:
            value = str(data.get(field, "")).strip()
            if value and not re.fullmatch(r"https://[^\s]{3,500}", value):
                return Response({"detail": f"{field} must be a secure https URL"}, status=400)
        for field in self.TEXT_FIELDS:
            if field in data and len(str(data[field])) > (1000 if field == "footer_text" else 240):
                return Response({"detail": f"{field} is too long"}, status=400)
        value = {**before, **{key: str(val).strip() for key, val in data.items() if key != "theme_preset"},
                 **self.PRESETS[preset], "theme_preset": preset}
        setting.value = value; setting.is_public = True; setting.updated_by = request.user; setting.save()
        self._audit(request, "branding.settings.update", before, value)
        return Response({"message": "Branding published", "branding": value})

    def post(self, request):
        _require_capability(request, "settings", "change")
        from PIL import Image
        kind = request.data.get("kind"); uploaded = request.FILES.get("file")
        if kind not in {"logo", "favicon"} or not uploaded:
            return Response({"detail": "Logo or favicon image is required"}, status=400)
        if uploaded.size > 2 * 1024 * 1024:
            return Response({"detail": "Branding images must be 2 MB or smaller"}, status=400)
        try:
            image = Image.open(uploaded); image.verify(); uploaded.seek(0)
            image = Image.open(uploaded); width, height = image.size; image_format = image.format
        except Exception:
            return Response({"detail": "File is not a valid image"}, status=400)
        allowed = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp", "ICO": "image/x-icon"}
        if image_format not in allowed or width < 16 or height < 16 or width > 4096 or height > 4096:
            return Response({"detail": "Use PNG, JPEG, WebP or ICO between 16 and 4096 pixels"}, status=400)
        if kind == "favicon" and (width != height or width > 512):
            return Response({"detail": "Favicon must be square and no larger than 512 pixels"}, status=400)
        uploaded.name = f"{kind}.{'jpg' if image_format == 'JPEG' else image_format.lower()}"
        old = BrandingAsset.objects.filter(kind=kind).first()
        if old and old.file:
            old.file.delete(save=False)
        asset, _ = BrandingAsset.objects.update_or_create(kind=kind, defaults={"file": uploaded,
            "alt_text": str(request.data.get("alt_text", ""))[:160], "mime_type": allowed[image_format],
            "file_size": uploaded.size, "width": width, "height": height, "updated_by": request.user})
        setting = self._setting(); value = dict(setting.value or {}); value[f"{kind}_url"] = asset.file.url
        if kind == "logo": value["logo_alt"] = asset.alt_text
        setting.value = value; setting.updated_by = request.user; setting.save()
        self._audit(request, f"branding.{kind}.upload", {}, {"asset_id": asset.id, "url": asset.file.url})
        return Response({"message": f"{kind.title()} uploaded", "asset": {"id": asset.id, "url": asset.file.url,
            "width": width, "height": height, "file_size": uploaded.size}}, status=201)

    def delete(self, request):
        _require_capability(request, "settings", "delete")
        kind = request.data.get("kind"); asset = BrandingAsset.objects.filter(kind=kind).first()
        if not asset:
            return Response({"detail": "Branding asset not found"}, status=404)
        if asset.file: asset.file.delete(save=False)
        asset.delete(); setting = self._setting(); value = dict(setting.value or {}); value.pop(f"{kind}_url", None)
        if kind == "logo": value.pop("logo_alt", None)
        setting.value = value; setting.updated_by = request.user; setting.save()
        self._audit(request, f"branding.{kind}.remove", {}, {})
        return Response({"message": f"{kind.title()} removed"})

    def _audit(self, request, action, before, after):
        from audit.models import AuditLog
        AuditLog.objects.create(user=request.user, user_email=request.user.email, actor_role=request.user.role,
            category="admin", severity="info", source="backend", action=action, message=action.replace(".", " ").title(),
            object_type="SiteSetting", object_id="branding", extra={"before": before, "after": after})


class AdminCMSView(APIView):
    """Versioned CMS workflow: draft, preview, schedule, publish and rollback."""
    permission_classes = [IsAdminOrStaff]
    MODELS = {"settings": SiteSetting, "pages": ManagedPage, "sections": ContentSection, "navigation": ManagedNavigationItem, "translations": CMSContentTranslation}
    FIELDS = {
        "settings": {"key", "value", "description", "is_public"},
        "pages": {"route", "key", "title", "meta_description", "is_enabled", "status", "scheduled_publish_at", "published_at"},
        "sections": {"page_id", "key", "title", "subtitle", "body", "image_url", "cta_text", "cta_url", "icon", "layout_variant", "config", "display_order", "is_visible", "status", "scheduled_publish_at", "published_at"},
        "navigation": {"location", "label", "route", "icon", "parent_id", "allowed_roles", "display_order", "is_active"},
        "translations": {"target_resource", "object_id", "language_code", "content"},
    }

    def _validate_payload(self, resource, payload):
        import re
        if resource in {"pages", "navigation"} and payload.get("route") and not str(payload["route"]).startswith("/"):
            raise ValueError("Only validated internal routes beginning with / are allowed")
        if resource == "sections" and payload.get("cta_url") and not str(payload["cta_url"]).startswith("/"):
            raise ValueError("CTA links must be validated internal routes beginning with /")
        if resource == "settings" and payload.get("key") == "branding":
            value = payload.get("value") or {}
            for field in ("primary_color", "secondary_color"):
                if value.get(field) and not re.fullmatch(r"#[0-9a-fA-F]{6}", str(value[field])):
                    raise ValueError(f"{field} must be a six-digit hex color")
        if resource in {"navigation", "sections"} and payload.get("icon") and not re.fullmatch(r"[A-Za-z0-9_-]{0,50}", str(payload["icon"])):
            raise ValueError("Invalid icon identifier")
        if resource == "translations":
            target = payload.get("target_resource")
            language = str(payload.get("language_code", ""))
            content = payload.get("content")
            allowed = {"pages": {"title", "meta_description"}, "sections": {"title", "subtitle", "body", "cta_text"}, "navigation": {"label"}}
            if target not in allowed or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Z]{2})?", language):
                raise ValueError("Translation target or language code is invalid")
            if not isinstance(content, dict) or set(content) - allowed[target] or any(not isinstance(value, str) for value in content.values()):
                raise ValueError("Translation contains unsupported fields")
            model = {"pages": ManagedPage, "sections": ContentSection, "navigation": ManagedNavigationItem}[target]
            if not model.objects.filter(pk=payload.get("object_id")).exists():
                raise ValueError("Translation target does not exist")

    def _row(self, resource, obj):
        row = {"id": obj.pk, "updated_at": getattr(obj, "updated_at", None)}
        for field in self.FIELDS[resource]:
            key = field[:-3] if field.endswith("_id") else field
            row[field] = getattr(obj, field, getattr(obj, key, None))
        return row

    def _snapshot(self, resource, obj):
        import json
        from django.core.serializers.json import DjangoJSONEncoder
        return json.loads(json.dumps(self._row(resource, obj), cls=DjangoJSONEncoder))

    def _revision(self, resource, obj, user, action):
        from django.db.models import Max
        number = (CMSRevision.objects.filter(resource=resource, object_id=obj.pk).aggregate(n=Max("revision_number"))["n"] or 0) + 1
        return CMSRevision.objects.create(resource=resource, object_id=obj.pk, revision_number=number,
            snapshot=self._snapshot(resource, obj), action=action, created_by=user)

    def _publish_due(self):
        now = timezone.now()
        for model in (ManagedPage, ContentSection):
            model.objects.filter(status="scheduled", scheduled_publish_at__lte=now).update(
                status="published", published_at=now, scheduled_publish_at=None)

    def get(self, request):
        _require_capability(request, "content", "view")
        self._publish_due()
        resource = request.query_params.get("resource", "pages")
        model = self.MODELS.get(resource)
        if not model:
            return Response({"detail": "Unknown CMS resource"}, status=400)
        object_id = request.query_params.get("id")
        if request.query_params.get("history") in {"1", "true"}:
            revisions = CMSRevision.objects.filter(resource=resource, object_id=object_id).select_related("created_by")[:100]
            return Response({"results": [{"id": r.id, "revision_number": r.revision_number,
                "action": r.action, "created_at": r.created_at,
                "created_by": r.created_by.email if r.created_by else None,
                "snapshot": r.snapshot} for r in revisions]})
        if request.query_params.get("preview") in {"1", "true"}:
            obj = model.objects.filter(pk=object_id).first()
            if not obj:
                return Response({"detail": "CMS record not found"}, status=404)
            data = self._row(resource, obj)
            if resource == "pages":
                data["sections"] = [self._row("sections", section) for section in obj.sections.all()]
            return Response({"preview": data, "notice": "Administrative preview; draft content is not public."})
        queryset = model.objects.all()
        if resource == "sections" and request.query_params.get("page_id"):
            queryset = queryset.filter(page_id=request.query_params["page_id"])
        return Response({"resource": resource, "results": [self._row(resource, obj) for obj in queryset[:500]]})

    def post(self, request):
        _require_capability(request, "content", "add")
        resource = request.data.get("resource")
        model = self.MODELS.get(resource)
        if not model:
            return Response({"detail": "Unknown CMS resource"}, status=400)
        payload = {k: v for k, v in request.data.items() if k in self.FIELDS[resource]}
        if resource in {"pages", "sections"} and "status" not in payload:
            payload["status"] = "draft"
        try:
            self._validate_payload(resource, payload)
            if resource in {"pages", "sections"} and payload.get("status") not in {"draft", "scheduled", "published"}:
                raise ValueError("Invalid publication status")
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        if resource == "navigation" and payload.get("parent_id"):
            parent = ManagedNavigationItem.objects.filter(pk=payload["parent_id"]).first()
            if not parent or parent.location != payload.get("location"):
                return Response({"detail": "Navigation parent must exist in the same location"}, status=400)
        if hasattr(model, "updated_by"):
            payload["updated_by"] = request.user
        from django.core.exceptions import ValidationError
        try:
            obj = model(**payload)
            obj.full_clean()
            obj.save()
        except ValidationError as exc:
            return Response({"detail": "; ".join(exc.messages)}, status=400)
        self._revision(resource, obj, request.user, "create")
        return Response({"id": obj.pk, "message": "Draft created" if resource in {"pages", "sections"} else "Created"}, status=201)

    def patch(self, request):
        _require_capability(request, "content", "change")
        resource = request.data.get("resource")
        model = self.MODELS.get(resource)
        obj = model.objects.filter(pk=request.data.get("id")).first() if model else None
        if not obj:
            return Response({"detail": "CMS record not found"}, status=404)
        action = request.data.get("action", "update")
        # Seed a baseline for records that predate revision tracking, so the
        # first edit can always be safely undone.
        if not CMSRevision.objects.filter(resource=resource, object_id=obj.pk).exists():
            self._revision(resource, obj, request.user, "create")
        if action == "rollback":
            revision = CMSRevision.objects.filter(pk=request.data.get("revision_id"), resource=resource, object_id=obj.pk).first()
            if not revision:
                return Response({"detail": "Revision not found for this record"}, status=404)
            payload = {k: v for k, v in revision.snapshot.items() if k in self.FIELDS[resource]}
            payload.pop("published_at", None)
            payload.pop("scheduled_publish_at", None)
            action_name = "rollback"
        elif action in {"publish", "unpublish", "schedule"}:
            if resource not in {"pages", "sections"}:
                return Response({"detail": "Publication workflow applies to pages and sections"}, status=400)
            if action == "schedule":
                from django.utils.dateparse import parse_datetime
                scheduled = parse_datetime(str(request.data.get("scheduled_publish_at", "")))
                if scheduled and timezone.is_naive(scheduled):
                    scheduled = timezone.make_aware(scheduled)
                if not scheduled or scheduled <= timezone.now():
                    return Response({"detail": "Choose a valid future publication time"}, status=400)
                payload = {"status": "scheduled", "scheduled_publish_at": scheduled, "published_at": None}
            elif action == "publish":
                payload = {"status": "published", "published_at": timezone.now(), "scheduled_publish_at": None}
            else:
                payload = {"status": "draft", "scheduled_publish_at": None}
            action_name = action
        else:
            payload = {k: v for k, v in request.data.items() if k in self.FIELDS[resource]}
            action_name = "update"
        validation_payload = payload
        if resource == "translations":
            validation_payload = {**self._snapshot(resource, obj), **payload}
        try:
            self._validate_payload(resource, validation_payload)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        if resource == "navigation" and "parent_id" in payload:
            parent = ManagedNavigationItem.objects.filter(pk=payload.get("parent_id")).first() if payload.get("parent_id") else None
            if parent and parent.location != payload.get("location", obj.location):
                return Response({"detail": "Navigation parent must be in the same location"}, status=400)
            cursor = parent
            while cursor:
                if cursor.pk == obj.pk:
                    return Response({"detail": "Navigation hierarchy cannot contain cycles"}, status=400)
                cursor = cursor.parent
        old_values = self._snapshot(resource, obj)
        for key, value in payload.items():
            setattr(obj, key, value)
        if hasattr(obj, "updated_by"):
            obj.updated_by = request.user
        from django.core.exceptions import ValidationError
        try:
            obj.full_clean()
            obj.save()
        except ValidationError as exc:
            return Response({"detail": "; ".join(exc.messages)}, status=400)
        revision = self._revision(resource, obj, request.user, action_name)
        from audit.models import AuditLog
        AuditLog.objects.create(user=request.user, user_email=request.user.email, category="admin", severity="info",
            source="backend", action=f"cms.{resource}.{action_name}", message=f"{action_name.title()} {resource} #{obj.pk}",
            object_type=model.__name__, object_id=str(obj.pk), extra={"before": old_values, "revision": revision.revision_number})
        return Response({"id": obj.pk, "message": action_name.title() + " complete", "revision_number": revision.revision_number,
                         "record": self._row(resource, obj)})


class AdminReviewModerationView(APIView):
    """Unified, retention-safe moderation queue for destination and hotel reviews."""
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_capability(request, "reviews", "view")
        from booking.models import HotelReview
        kind = request.query_params.get("type", "all")
        state = request.query_params.get("status", "pending")
        q = (request.query_params.get("q") or "").strip()
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            size = min(100, max(10, int(request.query_params.get("page_size", 25))))
        except ValueError:
            return Response({"detail": "Invalid pagination"}, status=400)
        destination = Review.objects.select_related("destination", "user")
        hotels = HotelReview.objects.select_related("hotel", "user")
        if state != "all":
            destination = destination.filter(moderation_status=state)
            hotels = hotels.filter(moderation_status=state)
        if q:
            destination = destination.filter(Q(comment__icontains=q) | Q(user__email__icontains=q) | Q(destination__name__icontains=q))
            hotels = hotels.filter(Q(comment__icontains=q) | Q(user__email__icontains=q) | Q(hotel__name__icontains=q))
        destination_count = destination.count() if kind in {"all", "destination"} else 0
        hotel_count = hotels.count() if kind in {"all", "hotel"} else 0
        end = page * size
        rows = []
        if kind in {"all", "destination"}:
            rows.extend({"id": row.id, "type": "destination", "subject": row.destination.name,
                "user": row.user.email, "rating": None, "comment": row.comment,
                "status": row.moderation_status, "is_flagged": row.is_flagged,
                "moderation_note": row.moderation_note, "created_at": row.created_at,
                "moderated_at": row.moderated_at} for row in destination.order_by("-created_at")[:end])
        if kind in {"all", "hotel"}:
            rows.extend({"id": row.id, "type": "hotel", "subject": row.hotel.name,
                "user": row.user.email, "rating": row.rating, "comment": row.comment,
                "status": row.moderation_status, "is_flagged": row.moderation_status == "flagged",
                "moderation_note": row.moderation_note, "created_at": row.created_at,
                "moderated_at": row.moderated_at} for row in hotels.order_by("-created_at")[:end])
        rows.sort(key=lambda row: row["created_at"], reverse=True)
        count = destination_count + hotel_count
        start = (page - 1) * size
        return Response({"count": count, "page": page, "pages": max(1, (count + size - 1) // size),
                         "results": rows[start:end], "counts": {"destination": destination_count, "hotel": hotel_count}})

    def patch(self, request):
        action = request.data.get("action")
        capability = {"approve": "approve", "flag": "change", "restore": "change", "archive": "delete"}.get(action)
        if not capability:
            return Response({"detail": "Unsupported moderation action"}, status=400)
        _require_capability(request, "reviews", capability)
        kind = request.data.get("type")
        ids = request.data.get("ids") or ([request.data.get("id")] if request.data.get("id") else [])
        ids = list(dict.fromkeys(ids))[:100]
        if kind not in {"destination", "hotel"} or not ids:
            return Response({"detail": "Review type and one or more IDs are required"}, status=400)
        from booking.models import HotelReview
        model = Review if kind == "destination" else HotelReview
        target_status = {"approve": "approved", "flag": "flagged", "archive": "archived", "restore": "pending"}[action]
        updates = {"moderation_status": target_status, "moderation_note": (request.data.get("note") or "").strip(),
                   "moderated_by": request.user, "moderated_at": timezone.now()}
        if kind == "destination":
            updates["is_flagged"] = action == "flag"
        updated = model.objects.filter(id__in=ids).update(**updates)
        from audit.models import AuditLog
        AuditLog.objects.create(user=request.user, user_email=request.user.email, actor_role=request.user.role,
            category="moderation", severity="warning" if action in {"flag", "archive"} else "info", source="backend",
            action=f"reviews.{action}", message=f"{action.title()} {updated} {kind} review(s)",
            object_type=model.__name__, extra={"ids": ids, "note": updates["moderation_note"], "status": target_status})
        return Response({"message": f"{updated} review(s) {action}d", "updated": updated, "status": target_status})


class AdminNotificationManagementView(APIView):
    permission_classes = [IsAdminOrStaff]
    def get(self, request):
        _require_capability(request, "settings", "view")
        qs=Notification.objects.select_related("user").order_by("-created_at")[:200]
        return Response([{"id":n.id,"user":n.user.email,"title":n.title,"message":n.message,"channel":n.channel,"is_read":n.is_read,"is_sent":n.is_sent,"created_at":n.created_at} for n in qs])
    def post(self, request):
        _require_capability(request, "settings", "add")
        title=(request.data.get("title") or "").strip(); message=(request.data.get("message") or "").strip()
        if not title or not message:return Response({"detail":"title and message are required"},status=400)
        role=request.data.get("role"); users=User.objects.filter(is_active=True); users=users.filter(role=role) if role else users
        rows=[Notification(user=u,title=title[:200],message=message,channel="in_app") for u in users]
        Notification.objects.bulk_create(rows,batch_size=500)
        from audit.models import AuditLog
        AuditLog.objects.create(user=request.user,user_email=request.user.email,category="admin",severity="info",source="backend",action="notification.broadcast",message=f"Broadcast '{title}' to {len(rows)} users",object_type="Notification",extra={"role":role,"recipient_count":len(rows)})
        return Response({"message":"Broadcast created","recipient_count":len(rows)},status=201)


class AdminReportsView(APIView):
    permission_classes=[IsAdminOrStaff]
    def get(self,request):
        _require_capability(request,"audit","view")
        from django.db.models import Count,Sum
        from django.db.models.functions import TruncMonth
        from django.utils.dateparse import parse_date
        from booking.models import Booking,HotelReview
        start=parse_date(request.query_params.get("from",""));end=parse_date(request.query_params.get("to",""))
        bookings=Booking.objects.all();feedback=UserFeedback.objects.all();visits=VisitHistory.objects.all()
        if start: bookings=bookings.filter(created_at__date__gte=start);feedback=feedback.filter(created_at__date__gte=start);visits=visits.filter(viewed_at__date__gte=start)
        if end: bookings=bookings.filter(created_at__date__lte=end);feedback=feedback.filter(created_at__date__lte=end);visits=visits.filter(viewed_at__date__lte=end)
        trend=lambda qs,field:list(qs.annotate(month=TruncMonth(field)).values("month").annotate(count=Count("id")).order_by("month"))
        from audit.models import AuditLog
        staff_activity=list(AuditLog.objects.exclude(user__isnull=True).values("user_email").annotate(actions=Count("id")).order_by("-actions")[:10])
        payload={"range":{"from":start,"to":end},"staff_activity":staff_activity,"users":{"total":User.objects.count(),"active":User.objects.filter(is_active=True).count(),"inactive":User.objects.filter(is_active=False).count(),"staff":User.objects.filter(is_staff=True).count()},"destinations":{"total":Destination.objects.count(),"active":Destination.objects.filter(is_active=True).count(),"pending":Destination.objects.filter(status="pending").count(),"top_viewed":list(Destination.objects.order_by("-views_count").values("id","name","views_count")[:10])},"hotels":{"total":Hotel.objects.count(),"bookings":bookings.count(),"booking_value":bookings.aggregate(total=Sum("total_price"))["total"] or 0,"reviews":HotelReview.objects.count()},"content":{"images":DestinationImage.objects.count(),"feedback":feedback.count(),"open_feedback":feedback.exclude(status__in=["resolved","closed","archived"]).count(),"alerts":Alert.objects.filter(is_active=True).count()},"activity":{"visits":visits.count(),"favorites":Favorite.objects.count(),"reviews":Review.objects.count(),"ratings":Rating.objects.count()},"trends":{"bookings":trend(bookings,"created_at"),"feedback":trend(feedback,"created_at"),"visits":trend(visits,"viewed_at")}}
        if request.query_params.get("format") == "csv":
            import csv
            from django.http import HttpResponse
            response=HttpResponse(content_type="text/csv");response["Content-Disposition"]='attachment; filename="tourism-report.csv"'
            writer=csv.writer(response);writer.writerow(["group","metric","value"])
            for group,values in payload.items():
                if isinstance(values,dict):
                    for metric,value in values.items():
                        if not isinstance(value,(list,dict)):writer.writerow([group,metric,value])
            return response
        return Response(payload)


class AdminDatasetManagerView(APIView):
    permission_classes = [IsAdminOrStaff]
    DATASETS = {
        "destinations": "dataset/destinations_clean.csv",
        "risk": "dataset/risk_features.csv",
        "budget": "dataset/travel_cost_cleaned.csv",
        "hospitals": "dataset/hospital_cleaned.csv",
        "police": "dataset/police_station_cleaned.csv",
        "community_services": "dataset/community_services.csv",
        "community_routes": "dataset/community_routes.csv",
    }
    def get(self, request):
        _require_capability(request,"datasets","view")
        import csv
        from pathlib import Path
        key=request.query_params.get("dataset")
        if not key:
            rows=[]
            for name,relative in self.DATASETS.items():
                path=Path(settings.BASE_DIR)/relative
                rows.append({"key":name,"path":relative,"exists":path.exists(),"size_bytes":path.stat().st_size if path.exists() else 0,"modified_at":path.stat().st_mtime if path.exists() else None})
            return Response({"datasets":rows})
        if key not in self.DATASETS:return Response({"detail":"Unknown dataset"},status=400)
        path=Path(settings.BASE_DIR)/self.DATASETS[key]
        if not path.exists():return Response({"detail":"Dataset file not found"},status=404)
        if request.query_params.get("download") in {"1","true","yes"}:
            from django.http import FileResponse
            return FileResponse(path.open("rb"),as_attachment=True,filename=path.name)
        try:page=max(1,int(request.query_params.get("page",1)));size=max(10,min(100,int(request.query_params.get("page_size",25))))
        except ValueError:return Response({"detail":"Invalid pagination"},status=400)
        with path.open(newline="",encoding="utf-8-sig") as handle:
            reader=csv.DictReader(handle);all_rows=list(reader);headers=reader.fieldnames or []
        start=(page-1)*size
        return Response({"dataset":key,"headers":headers,"count":len(all_rows),"page":page,"total_pages":max(1,(len(all_rows)+size-1)//size),"results":all_rows[start:start+size]})
    def post(self,request):
        _require_capability(request,"datasets","add")
        import csv,io,uuid
        from pathlib import Path
        key=request.data.get("dataset");uploaded=request.FILES.get("file")
        if key not in self.DATASETS or not uploaded:return Response({"detail":"Valid dataset and CSV file are required"},status=400)
        if uploaded.size>10*1024*1024 or not uploaded.name.lower().endswith(".csv"):return Response({"detail":"CSV must be 10 MB or smaller"},status=400)
        try:text=uploaded.read().decode("utf-8-sig");reader=csv.DictReader(io.StringIO(text));headers=reader.fieldnames or [];rows=list(reader)
        except Exception as exc:return Response({"detail":f"CSV parse failed: {exc}"},status=400)
        current=Path(settings.BASE_DIR)/self.DATASETS[key]
        with current.open(newline="",encoding="utf-8-sig") as handle:expected=csv.DictReader(handle).fieldnames or []
        missing=[field for field in expected if field not in headers];extra=[field for field in headers if field not in expected]
        errors=[]
        for index,row in enumerate(rows[:1000],2):
            if not any(str(value).strip() for value in row.values()):errors.append({"row":index,"error":"Empty row"})
        if missing:return Response({"valid":False,"missing_headers":missing,"extra_headers":extra,"errors":errors[:100]},status=400)
        staging=Path(settings.BASE_DIR)/"dataset"/"staging";staging.mkdir(parents=True,exist_ok=True);token=f"{key}-{uuid.uuid4().hex}.csv";(staging/token).write_text(text,encoding="utf-8")
        return Response({"valid":True,"token":token,"dataset":key,"row_count":len(rows),"headers":headers,"extra_headers":extra,"errors":errors[:100]},status=201)
    def put(self,request):
        _require_capability(request,"datasets","change")
        import os,shutil
        from pathlib import Path
        token=Path(str(request.data.get("token","")).strip()).name;key=request.data.get("dataset")
        if key not in self.DATASETS or not token.startswith(f"{key}-"):return Response({"detail":"Invalid staged import"},status=400)
        staged=Path(settings.BASE_DIR)/"dataset"/"staging"/token;target=Path(settings.BASE_DIR)/self.DATASETS[key]
        if not staged.exists():return Response({"detail":"Staged file not found"},status=404)
        backup=target.with_suffix(f".backup-{timezone.now().strftime('%Y%m%d%H%M%S')}.csv");shutil.copy2(target,backup);os.replace(staged,target)
        from audit.models import AuditLog
        AuditLog.objects.create(user=request.user,user_email=request.user.email,category="data",severity="warning",source="backend",action="dataset.import",message=f"Imported {key} dataset",object_type="Dataset",object_id=key,extra={"backup":str(backup.name)})
        return Response({"message":"Dataset imported","dataset":key,"backup":backup.name})


class AdminMediaLibraryView(APIView):
    permission_classes = [IsAdminOrStaff]
    def get(self, request):
        _require_capability(request,"images","view")
        qs=DestinationImage.objects.select_related("destination","uploaded_by").order_by("-created_at")
        q=request.query_params.get("q","");status_filter=request.query_params.get("status");source=request.query_params.get("source")
        if q: qs=qs.filter(Q(destination__name__icontains=q)|Q(caption__icontains=q)|Q(external_url__icontains=q))
        if status_filter: qs=qs.filter(verification_status=status_filter)
        if source: qs=qs.filter(source=source)
        page=max(1,int(request.query_params.get("page",1)));size=30;count=qs.count();items=[]
        for image in qs[(page-1)*size:page*size]:
            url=image.external_url or (image.image.url if image.image else "")
            items.append({"id":image.id,"destination_id":image.destination_id,"destination":image.destination.name,"url":url,"caption":image.caption,"source":image.source,"source_url":image.source_url,"license":image.license_type,"photographer":image.photographer,"status":image.verification_status,"is_cover":image.is_cover,"ordering":image.ordering,"created_at":image.created_at})
        return Response({"count":count,"page":page,"total_pages":max(1,(count+size-1)//size),"results":items})
    def patch(self, request):
        _require_capability(request,"images","change")
        ids=request.data.get("ids") or []
        action=request.data.get("action")
        if ids and action in {"approve","reject"}:
            updated=DestinationImage.objects.filter(id__in=ids).update(verification_status="approved" if action=="approve" else "rejected",is_verified=action=="approve")
            return Response({"message":f"Bulk {action} complete","updated":updated})
        image=DestinationImage.objects.filter(pk=request.data.get("id")).first()
        if not image:return Response({"detail":"Image not found"},status=404)
        for field in ("caption","alt_text","ordering","verification_status","is_verified"):
            if field in request.data:setattr(image,field,request.data[field])
        image.save();return Response({"message":"Media updated","id":image.id})
    def delete(self, request):
        _require_capability(request,"images","delete")
        image=DestinationImage.objects.select_related("destination").filter(pk=request.data.get("id")).first()
        if not image:return Response({"detail":"Image not found"},status=404)
        destination=image.destination;was_cover=image.is_cover;image.delete()
        if was_cover:
            replacement=destination.gallery.exclude(verification_status="rejected").order_by("ordering","id").first()
            if replacement:
                replacement.is_cover=True;replacement.save(update_fields=["is_cover"])
        return Response({"message":"Media deleted","replacement_cover_id":replacement.id if was_cover and replacement else None})


class AdminGlobalSearchView(APIView):
    permission_classes = [IsAdminOrStaff]
    def get(self, request):
        q=(request.query_params.get("q") or "").strip()
        if len(q)<2:return Response({"detail":"Enter at least 2 characters"},status=400)
        from django.db.models import Q
        results=[]
        def add(module,kind,queryset,label):
            if not _has_capability(request,module,"view"):return
            for obj in queryset[:8]:results.append({"type":kind,"id":obj.pk,"label":label(obj),"module":module})
        add("destinations","destination",Destination.objects.filter(Q(name__icontains=q)|Q(city__icontains=q)|Q(district__icontains=q)),lambda x:f"{x.name} · {x.district or x.city or 'Nepal'}")
        add("users","user",User.objects.filter(Q(email__icontains=q)|Q(first_name__icontains=q)|Q(last_name__icontains=q)),lambda x:f"{x.full_name} · {x.email}")
        add("hotels","hotel",Hotel.objects.filter(Q(name__icontains=q)|Q(address__icontains=q)),lambda x:f"{x.name} · {x.address}")
        add("feedback","feedback",UserFeedback.objects.filter(Q(subject__icontains=q)|Q(message__icontains=q)|Q(email__icontains=q)),lambda x:f"{x.subject} · {x.status}")
        add("safety","alert",Alert.objects.filter(Q(title__icontains=q)|Q(description__icontains=q)|Q(city__icontains=q)),lambda x:f"{x.title} · {x.severity}")
        return Response({"query":q,"count":len(results),"results":results})


class FeedbackListView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_capability(request, "feedback", "view")
        qs = UserFeedback.objects.all().select_related("user", "assigned_to")
        status = request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return Response([{
            "id": f.id,
            "user_id": f.user_id,
            "name": f.name or (f.user.get_full_name() if f.user else ""),
            "email": f.email or (f.user.email if f.user else ""),
            "subject": f.subject,
            "message": f.message,
            "category": f.category,
            "status": f.status,
            "priority": f.priority,
            "assigned_to": f.assigned_to_id,
            "assigned_to_email": f.assigned_to.email if f.assigned_to else None,
            "closed_at": f.closed_at,
            "admin_reply": f.admin_reply,
            "messages": [{"id":m.id,"sender":m.sender.email if m.sender else "visitor","body":m.body,"is_internal":m.is_internal,"created_at":m.created_at} for m in f.messages.all()],
            "evidence": [{
                "id": evidence.id, "media_type": evidence.media_type,
                "url": request.build_absolute_uri(evidence.file.url),
                "caption": evidence.caption, "is_verified": evidence.is_verified,
            } for evidence in f.evidence.all()],
            "created_at": f.created_at,
        } for f in qs[:200]])


class FeedbackReplyView(APIView):
    permission_classes = [IsAdminOrStaff]

    def patch(self, request, id):
        _require_capability(request, "feedback", "change")
        f=UserFeedback.objects.filter(pk=id).first()
        if not f:return Response({"detail":"not found"},status=404)
        if "status" in request.data:
            allowed={choice[0] for choice in UserFeedback.Status.choices}
            if request.data["status"] not in allowed:return Response({"detail":"Invalid status"},status=400)
            f.status=request.data["status"]
            if f.status in {"closed","resolved"}:f.closed_at=timezone.now()
        if "priority" in request.data:f.priority=request.data["priority"]
        if "assigned_to" in request.data:f.assigned_to_id=request.data["assigned_to"] or None
        f.save();return Response({"message":"Thread updated","id":f.id,"status":f.status})

    def post(self, request, id):
        _require_capability(request, "feedback", "change")
        from django.utils import timezone
        f = UserFeedback.objects.filter(pk=id).first()
        if not f:
            return Response({"detail": "not found"}, status=404)
        reply = request.data.get("reply", "")
        if not reply:
            return Response({"detail":"reply is required"},status=400)
        FeedbackMessage.objects.create(feedback=f,sender=request.user,body=reply,is_internal=bool(request.data.get("is_internal",False)))
        f.admin_reply = reply
        f.status = UserFeedback.Status.REPLIED
        f.replied_by = request.user if request.user.is_authenticated else None
        f.replied_at = timezone.now()
        f.save()
        if f.user and not request.data.get("is_internal",False):
            Notification.objects.create(user=f.user,title=f"Reply: {f.subject}"[:200],message=reply,channel="in_app")
        return Response({"message": "reply saved", "id": f.id})


class PublicFeedbackCreateView(APIView):
    """Public 'Contact / communicate with admin' endpoint (login optional)."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        if not data.get("subject") or not data.get("message"):
            return Response({"detail": "subject and message are required"}, status=400)
        fb = UserFeedback.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=data.get("name", ""),
            email=data.get("email", ""),
            subject=data["subject"][:200],
            message=data["message"],
            category=data.get("category", "general"),
        )
        FeedbackMessage.objects.create(feedback=fb, sender=request.user if request.user.is_authenticated else None, body=data["message"], is_internal=False)
        files = request.FILES.getlist("evidence")
        for uploaded in files[:8]:
            FeedbackEvidence.objects.create(
                feedback=fb,
                media_type="video" if (uploaded.content_type or "").startswith("video/") else "image",
                file=uploaded, caption=data.get("evidence_caption", ""),
            )
        return Response({"id": fb.id, "message": "feedback received", "evidence_count": min(len(files), 8)}, status=201)


class FetchWebImagesView(APIView):
    """Admin: search free sources (Wikimedia/DDG/Openverse) for real photos
    of a destination and save them directly into the gallery/cover."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        from tourist.services.image_search.search import search_destination_images
        target = request.data.get("destination")
        num = int(request.data.get("num", 12))
        if not target:
            return Response({"detail": "destination (id, slug or name) required"}, status=400)

        dest = (Destination.objects.filter(pk=target).first() if str(target).isdigit() else None) \
            or Destination.objects.filter(slug=target).first() \
            or Destination.objects.filter(name__icontains=target).first()
        if not dest:
            return Response({"detail": "destination not found"}, status=404)

        hits = search_destination_images(dest, per_source=max(10, num), min_score=0.30)
        saved = 0
        existing = set(dest.gallery.exclude(external_url="").values_list("external_url", flat=True))
        first = True
        for hit in hits[:num]:
            if hit.url in existing:
                continue
            is_cover = first and not dest.cover_image
            img = DestinationImage.objects.create(
                destination=dest,
                external_url=hit.url,
                thumbnail_url=hit.thumbnail,
                caption=f"{dest.name} — {hit.title or hit.source}",
                source=DestinationImage.Source.WIKIMEDIA if hit.source == "wikimedia" else DestinationImage.Source.ADMIN,
                source_url=hit.source_page or "",
                source_platform=hit.source,
                photographer=hit.author[:150],
                license_type=hit.license[:100],
                copyright_status="web_search",
                is_cover=is_cover,
                destination_match_score=round(hit.match_score, 3),
                authenticity_score=0.9 if hit.source == "wikimedia" else 0.75,
                verification_status=DestinationImage.ImageStatus.APPROVED,
            )
            if is_cover:
                dest.gallery.filter(is_cover=True).exclude(id=img.id).update(is_cover=False)
                Destination.objects.filter(pk=dest.pk).update(cover_image=hit.url)
            existing.add(hit.url)
            saved += 1
            first = False
        return Response({"destination": dest.name, "found": len(hits), "saved": saved})


class DeleteImageView(APIView):
    permission_classes = [IsAdminOrStaff]

    def delete(self, request, id):
        img = DestinationImage.objects.filter(pk=id).first()
        if not img:
            return Response({"detail": "not found"}, status=404)
        was_cover = img.is_cover
        dest = img.destination
        img.delete()
        if was_cover:
            nxt = dest.gallery.first()
            if nxt:
                nxt.is_cover = True
                nxt.save(update_fields=["is_cover"])
                Destination.objects.filter(pk=dest.pk).update(cover_image=nxt.external_url or "")
        return Response({"message": "deleted", "destination": dest.name})


class GenerateAIImagesView(APIView):
    """Admin: generate AI (Flux) images for a destination in real time."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        from tourist.services.image_generation.collector import collect_for_destination
        target = request.data.get("destination")
        num = int(request.data.get("num", 12))
        if not target:
            return Response({"detail": "destination (id/slug/name) required"}, status=400)
        dest = (Destination.objects.filter(pk=target).first() if str(target).isdigit() else None) \
            or Destination.objects.filter(slug=target).first() \
            or Destination.objects.filter(name__icontains=target).first()
        if not dest:
            return Response({"detail": "destination not found"}, status=404)

        images = collect_for_destination(dest, num=num, use_ai=True, use_search=True)
        existing = set(dest.gallery.exclude(external_url="").values_list("external_url", flat=True))
        saved = 0
        for img in images:
            if img["url"] in existing:
                continue
            di = DestinationImage.objects.create(
                destination=dest,
                external_url=img["url"],
                thumbnail_url=img.get("thumbnail", img["url"]),
                caption=img.get("caption", "")[:200],
                source=DestinationImage.Source.AI_GENERATED if img["source"] == "ai_generated" else DestinationImage.Source.ADMIN,
                source_platform=img.get("source_platform", ""),
                photographer=img.get("photographer", ""),
                license_type=img.get("license", ""),
                generation_prompt=img.get("prompt", ""),
                generation_seed=img.get("seed"),
                generation_provider="flux-pollinations" if img["source"] == "ai_generated" else "",
                destination_match_score=img.get("match_score"),
                copyright_status="ai_generated" if img["source"] == "ai_generated" else "web_search",
                verification_status=DestinationImage.ImageStatus.APPROVED,
            )
            existing.add(img["url"])
            saved += 1
        # set newest AI image as cover if requested
        if request.data.get("set_cover", True):
            cover = dest.gallery.filter(source=DestinationImage.Source.AI_GENERATED).order_by("-created_at").first()
            if cover:
                dest.gallery.filter(is_cover=True).exclude(id=cover.id).update(is_cover=False)
                cover.is_cover = True
                cover.save(update_fields=["is_cover"])
                Destination.objects.filter(pk=dest.pk).update(cover_image=cover.external_url)
        return Response({"destination": dest.name, "saved": saved,
                         "cover": str(dest.cover_image)[:80],
                         "total_gallery": dest.gallery.count()})


class DownloadAIImagesView(APIView):
    """Admin: download real AI images (actual files) for a destination."""
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        from tourist.services.image_generation.downloader import fetch_images
        target = request.data.get("destination")
        num = int(request.data.get("num", 10))
        if not target:
            return Response({"detail": "destination required"}, status=400)
        dest = (Destination.objects.filter(pk=target).first() if str(target).isdigit() else None) \
            or Destination.objects.filter(slug=target).first() \
            or Destination.objects.filter(name__icontains=target).first()
        if not dest:
            return Response({"detail": "destination not found"}, status=404)
        images = fetch_images(dest, num=num)
        saved = 0
        for img in images:
            if dest.gallery.filter(image=img["file_path"]).exists():
                continue
            di = DestinationImage.objects.create(
                destination=dest,
                image=img["file_path"],
                caption=f"{dest.name} — {img['style']}",
                source=DestinationImage.Source.AI_GENERATED,
                source_platform=f"ai:{img['provider']}:{img['style']}",
                photographer="AI generated",
                license_type="AI generated image",
                copyright_status="ai_generated",
                generation_prompt=img["prompt"],
                generation_seed=img["seed"],
                generation_provider=img["provider"],
                thumbnail_url=str(request.build_absolute_uri(settings.MEDIA_URL + img["file_path"])),
                authenticity_score=0.9,
                verification_status=DestinationImage.ImageStatus.APPROVED,
            )
            if saved == 0 and not dest.cover_image:
                dest.gallery.filter(is_cover=True).exclude(id=di.id).update(is_cover=False)
                di.is_cover = True
                di.save(update_fields=["is_cover"])
                Destination.objects.filter(pk=dest.pk).update(cover_image=img["file_path"])
            saved += 1
        return Response({"destination": dest.name, "downloaded": len(images), "saved": saved})
