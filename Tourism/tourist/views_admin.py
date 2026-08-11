from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import (
    Destination, Alert, DestinationImage, VisitHistory,
    SOSAlert, SharedTrip, LocationPing, Category, Hotel,
    Hospital, PoliceStation, TravelExpenseFeedback, TravelRiskFeedback,
    DestinationAuditLog
)
from .permissions import IsAdminOrStaff

User = get_user_model()


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

    def put(self, request, id):
        try:
            destination = Destination.objects.get(id=id)
        except Destination.DoesNotExist:
            return Response({"detail": "Destination not found."}, status=status.HTTP_404_NOT_FOUND)

        for key, value in request.data.items():
            if hasattr(destination, key):
                setattr(destination, key, value)
        destination.save()
        return Response({"message": "Destination updated successfully"})

    def delete(self, request, id):
        Destination.objects.filter(id=id).delete()
        return Response({"message": "Destination deleted successfully"})


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
