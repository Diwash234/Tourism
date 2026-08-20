from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import (
    Destination, Alert, DestinationImage, VisitHistory,
    SOSAlert, SharedTrip, LocationPing, Category, Hotel,
    Hospital, PoliceStation, TravelExpenseFeedback, TravelRiskFeedback,
    DestinationAuditLog, FeedbackEvidence, UserFeedback, InfrastructureSubmission, MLTrainingRun,
    SiteSetting, ManagedPage, ContentSection, ManagedNavigationItem, FeedbackMessage, StaffCapabilityProfile
)
from .permissions import IsAdminOrStaff
from .serializers import InfrastructureSubmissionSerializer

User = get_user_model()


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
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        users = User.objects.all().order_by("-date_joined")
        data = []
        for u in users:
            visits = list(
                u.history.select_related("destination")
                .order_by("-viewed_at")[:10]
                .values("destination__name", "destination__slug", "destination__city", "viewed_at")
            )
            active_sos = u.sos_alerts.filter(status=SOSAlert.Status.ACTIVE).exists()
            data.append({
                "id": u.id,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "full_name": u.full_name,
                "bio": u.bio or "Travel enthusiast exploring Nepal's Himalayas & cultural heritage.",
                "role": u.role,
                "managed_district": u.managed_district or "",
                "is_active": u.is_active,
                "is_staff": u.is_staff,
                "is_superuser": u.is_superuser,
                "latitude": float(u.latitude) if u.latitude is not None else None,
                "longitude": float(u.longitude) if u.longitude is not None else None,
                "city": u.city or "",
                "country": u.country or "Nepal",
                "location_source": u.location_source or "GPS",
                "history_count": u.history.count(),
                "travel_history": visits,
                "last_destination": visits[0]["destination__name"] if visits else None,
                "has_emergency": active_sos,
                "date_joined": u.date_joined,
            })
        return Response(data)

    def post(self, request):
        data = request.data
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        role = data.get("role", User.Role.TOURIST)
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        bio = data.get("bio", "")
        managed_district = data.get("managed_district", "")

        if not email or not password:
            return Response(
                {"detail": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_staff = role in [
            User.Role.ADMIN, User.Role.SUPER_ADMIN, User.Role.TOURISM_ADMIN,
            User.Role.STAFF, User.Role.CONTENT_MODERATOR, User.Role.DISTRICT_MANAGER
        ]

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            bio=bio,
            role=role,
            managed_district=managed_district,
            is_staff=is_staff,
            is_active=True,
            is_verified=True,
        )

        return Response({
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "message": f"User {user.email} created successfully with role {user.role}."
        }, status=status.HTTP_201_CREATED)


class UpdateUserStatusView(APIView):
    permission_classes = [IsAdminOrStaff]

    def put(self, request, id):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if "is_active" in request.data:
            user.is_active = bool(request.data["is_active"])
        if "role" in request.data:
            user.role = request.data["role"]
            if user.role in [User.Role.ADMIN, User.Role.SUPER_ADMIN, User.Role.STAFF, User.Role.CONTENT_MODERATOR]:
                user.is_staff = True
        if "managed_district" in request.data:
            user.managed_district = request.data["managed_district"]
        if "first_name" in request.data:
            user.first_name = request.data["first_name"]
        if "last_name" in request.data:
            user.last_name = request.data["last_name"]
        if "bio" in request.data:
            user.bio = request.data["bio"]

        user.save()
        return Response({
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "message": "User updated successfully."
        })

    def patch(self, request, id):
        return self.put(request, id)

    def delete(self, request, id):
        if request.user.id == id:
            return Response({"detail": "Cannot delete your own account."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=id)
            user.delete()
            return Response({"message": "User deleted successfully."})
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class AdminUserTrackingView(APIView):
    """
    GET /api/v1/admin/user-tracking/
    Detailed user tracking: current coordinates, destination views,
    navigation history, and medical emergency / SOS status.
    """
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
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
        places = Destination.objects.filter(status=Destination.SubmissionStatus.PENDING).select_related("category", "created_by")
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
        action_type = request.data.get("action", "approve")  # approve or reject
        if not id:
            id = request.data.get("id")
        try:
            place = Destination.objects.get(id=id)
        except Destination.DoesNotExist:
            return Response({"detail": "Place not found."}, status=status.HTTP_404_NOT_FOUND)

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
    """Full user details incl. verification, activity and feedback for admin."""
    permission_classes = [IsAdminOrStaff]

    def get(self, request, id):
        User = get_user_model()
        u = User.objects.filter(pk=id).first()
        if not u:
            return Response({"detail": "not found"}, status=404)
        return Response({
            "id": u.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "phone_number": u.phone_number,
            "role": u.role,
            "is_verified": u.is_verified,
            "phone_verified": getattr(u, "phone_verified", False),
            "is_active": u.is_active,
            "is_staff": u.is_staff,
            "is_superuser": u.is_superuser,
            "date_joined": u.date_joined,
            "last_login": u.last_login,
            "city": u.city,
            "country": u.country,
            "managed_district": u.managed_district,
            "feedback_count": u.feedbacks.count(),
            "feedbacks": [
                {"id": f.id, "subject": f.subject, "status": f.status,
                 "created_at": f.created_at}
                for f in u.feedbacks.all()[:10]
            ],
        })

    def patch(self, request, id):
        User = get_user_model()
        u = User.objects.filter(pk=id).first()
        if not u:
            return Response({"detail": "not found"}, status=404)
        for field in ("is_verified", "is_active", "is_staff", "role",
                      "managed_district", "first_name", "last_name"):
            if field in request.data:
                setattr(u, field, request.data[field])
        u.save()
        return Response({"message": "user updated", "id": u.id})


class AdminSendVerificationView(APIView):
    """
    Send a verification reminder / feedback email to a user. Uses the
    configured email backend (console by default in dev). Twilio SMS is used
    when TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN are set and a phone exists.
    """
    permission_classes = [IsAdminOrStaff]

    def post(self, request, id):
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
                u.is_verified = True  # mark verified once a verification message is dispatched
                u.save(update_fields=["is_verified"])
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
        return Response([{
            "id": run.id, "model_type": run.model_type, "status": run.status,
            "version": run.version, "previous_version": run.previous_version,
            "dataset_size": run.dataset_size, "newly_approved_records": run.newly_approved_records,
            "validation_metrics": run.validation_metrics, "started_at": run.started_at,
            "completed_at": run.completed_at, "requested_by": run.requested_by_id,
        } for run in MLTrainingRun.objects.all()[:100]])

    def post(self, request):
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
        profile.capabilities=request.data.get("capabilities",{})
        profile.managed_districts=request.data.get("managed_districts",[])
        profile.is_active=bool(request.data.get("is_active",True));profile.assigned_by=request.user
        try: profile.full_clean()
        except Exception as exc: return Response({"detail":str(exc)},status=400)
        profile.save();return Response({"message":"Capabilities updated","user_id":user.id})


class AdminCMSView(APIView):
    permission_classes = [IsAdminOrStaff]
    MODELS = {"settings": SiteSetting, "pages": ManagedPage, "sections": ContentSection, "navigation": ManagedNavigationItem}
    FIELDS = {
        "settings": {"key","value","description","is_public"},
        "pages": {"route","key","title","meta_description","is_enabled","status"},
        "sections": {"page_id","key","title","subtitle","body","image_url","cta_text","cta_url","icon","layout_variant","config","display_order","is_visible","status"},
        "navigation": {"location","label","route","icon","parent_id","allowed_roles","display_order","is_active"},
    }
    def get(self, request):
        resource=request.query_params.get("resource","pages"); model=self.MODELS.get(resource)
        if not model:return Response({"detail":"Unknown CMS resource"},status=400)
        rows=[]
        for obj in model.objects.all()[:300]:
            row={"id":obj.pk}
            for field in self.FIELDS[resource]:
                key=field[:-3] if field.endswith("_id") else field
                value=getattr(obj,field,getattr(obj,key,None))
                row[field]=value
            rows.append(row)
        return Response({"resource":resource,"results":rows})
    def post(self, request):
        resource=request.data.get("resource"); model=self.MODELS.get(resource)
        if not model:return Response({"detail":"Unknown CMS resource"},status=400)
        payload={k:v for k,v in request.data.items() if k in self.FIELDS[resource]}
        payload["updated_by"]=request.user
        obj=model.objects.create(**payload)
        return Response({"id":obj.pk,"message":"Created"},status=201)
    def patch(self, request):
        resource=request.data.get("resource"); model=self.MODELS.get(resource); obj=model.objects.filter(pk=request.data.get("id")).first() if model else None
        if not obj:return Response({"detail":"CMS record not found"},status=404)
        for key,value in request.data.items():
            if key in self.FIELDS[resource]:setattr(obj,key,value)
        obj.updated_by=request.user;obj.save();return Response({"id":obj.pk,"message":"Updated"})


class FeedbackListView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        qs = UserFeedback.objects.all().select_related("user")
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

    def post(self, request, id):
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
