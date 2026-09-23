"""Partner marketplace: listings, applications, trip basket, request checkout."""
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.logging_services import log_action
from .models import Destination, MarketplaceListing, MarketplaceOrder, MarketplaceOrderItem, MarketplacePartner, User
from .permissions import IsAdminOrStaff
from .notification_delivery import queue_notification
from .views_admin import _require_capability

ORDER_TRANSITIONS = {
    MarketplaceOrder.Status.REQUESTED: {"review", "cancel"},
    MarketplaceOrder.Status.UNDER_REVIEW: {"confirm", "cancel"},
    MarketplaceOrder.Status.EXTERNAL: {"review", "confirm", "cancel"},
    MarketplaceOrder.Status.CONFIRMED: set(),
    MarketplaceOrder.Status.CANCELLED: set(),
    MarketplaceOrder.Status.DRAFT: set(),
}

CARD_KEYS = {
    "card_number", "cvv", "cvc", "pan", "cardNumber",
    "expiry", "expiration", "expiry_date", "exp_month", "exp_year",
    "card_expiry", "expiration_date", "expiryDate", "cardExpiry",
    "expirationDate", "expMonth", "expYear",
}


def _contains_card_fields(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key) in CARD_KEYS:
                return True
            if _contains_card_fields(value):
                return True
    elif isinstance(payload, list):
        return any(_contains_card_fields(item) for item in payload)
    return False


def _https_or_blank(url):
    value = str(url or "").strip()
    if not value:
        return ""
    if not value.startswith("https://"):
        raise ValueError("External URLs must use HTTPS")
    return value[:600]


def _int(value, default=1, lo=1, hi=100):
    try:
        number = int(value if value not in (None, "") else default)
    except (TypeError, ValueError):
        raise ValueError("Must be a whole number")
    return max(lo, min(hi, number))


def _money(value, default="0"):
    try:
        amount = Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Price must be a number")
    if amount < 0:
        raise ValueError("Price cannot be negative")
    return amount


def _listing_row(listing):
    dest = listing.destination
    partner = listing.partner
    return {
        "id": listing.id,
        "slug": listing.slug,
        "kind": listing.kind,
        "title": listing.title,
        "summary": listing.summary,
        "description": listing.description,
        "includes": listing.includes,
        "excludes": listing.excludes,
        "duration_days": listing.duration_days,
        "price_npr": str(listing.price_npr),
        "currency": listing.currency,
        "image_url": listing.image_url,
        "external_url": listing.external_url,
        "city": listing.city or (dest.city if dest else ""),
        "district": listing.district or (dest.district if dest else ""),
        "cancellation_policy": listing.cancellation_policy,
        "capacity": listing.capacity,
        "is_featured": listing.is_featured,
        "status": listing.status,
        "destination_id": listing.destination_id,
        "destination_name": dest.name if dest else "",
        "destination_slug": dest.slug if dest else "",
        "partner_id": partner.id,
        "partner_name": partner.name,
        "partner_kind": partner.kind,
        "updated_at": listing.updated_at,
    }


def _partner_row(partner):
    return {
        "id": partner.id, "name": partner.name, "kind": partner.kind,
        "contact_name": partner.contact_name, "email": partner.email, "phone": partner.phone,
        "website": partner.website, "city": partner.city, "district": partner.district,
        "description": partner.description, "services": partner.services,
        "license_info": partner.license_info, "logo_url": partner.logo_url,
        "status": partner.status, "commission_percent": str(partner.commission_percent),
        "listing_count": partner.listings.count(),
        "admin_note": partner.admin_note, "created_at": partner.created_at,
        "user_id": partner.user_id,
    }


def _notify_user(user, title, message, category="booking", metadata=None):
    if not user:
        return
    queue_notification(user, title, message, channel="in_app", category=category, metadata=metadata or {})


def _notify_marketplace_admins(title, message, metadata=None):
    admins = User.objects.filter(is_active=True).filter(
        Q(is_superuser=True) | Q(role__in=["admin", "super_admin", "tourism_admin"])
    )[:20]
    for admin in admins:
        _notify_user(admin, title, message, metadata=metadata)


def _link_partner_user(partner):
    if partner.user_id:
        return partner
    user = User.objects.filter(email__iexact=partner.email, is_active=True).first()
    if user:
        partner.user = user
        partner.save(update_fields=["user", "updated_at"])
    return partner


def _partner_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return MarketplacePartner.objects.filter(Q(user=user) | Q(email__iexact=user.email)).order_by("-updated_at").first()


def _order_row(order):
    titles = [item.title for item in order.items.all()]
    days = max((item.listing.duration_days or 1) for item in order.items.all()) if order.items.exists() else 1
    return {
        "id": order.id, "reference": order.reference, "status": order.status,
        "status_label": order.get_status_display(),
        "payment_method": order.payment_method, "guest_name": order.guest_name,
        "guest_email": order.guest_email, "guest_phone": order.guest_phone,
        "travelers": order.travelers, "start_date": order.start_date, "notes": order.notes,
        "subtotal_npr": str(order.subtotal_npr), "total_npr": str(order.total_npr),
        "currency": order.currency, "created_at": order.created_at,
        "headline": " · ".join(titles[:3]) or "Trip request",
        "duration_days": days,
        "items": [{
            "id": item.id, "listing_id": item.listing_id, "title": item.title,
            "quantity": item.quantity, "unit_price_npr": str(item.unit_price_npr),
            "line_total_npr": str(item.line_total_npr), "travel_date": item.travel_date,
            "external_url": item.external_url, "slug": item.listing.slug,
            "duration_days": item.listing.duration_days,
        } for item in order.items.select_related("listing")],
    }


def _listing_from_payload(data, partner, user, force_status=None, allow_featured=True, default_status=None):
    title = str(data.get("title") or "").strip()
    if not title:
        raise ValueError("title is required")
    image_url = _https_or_blank(data.get("image_url"))
    external_url = _https_or_blank(data.get("external_url"))
    price = _money(data.get("price_npr"))
    duration_days = _int(data.get("duration_days"), 1, 1, 60)
    capacity = _int(data.get("capacity"), 10, 1, 200)
    dest = Destination.objects.filter(pk=data.get("destination_id")).first() if data.get("destination_id") else None
    status_value = force_status or data.get("status") or default_status or MarketplaceListing.Status.DRAFT
    if status_value not in MarketplaceListing.Status.values:
        raise ValueError("Unknown listing status")
    if status_value == MarketplaceListing.Status.PUBLISHED and partner.status != MarketplacePartner.Status.APPROVED:
        raise ValueError("Approve the partner before publishing this offer")
    kind = data.get("kind")
    if kind not in MarketplaceListing.Kind.values:
        kind = MarketplaceListing.Kind.HOTEL if partner.kind in {
            MarketplacePartner.Kind.HOTEL, MarketplacePartner.Kind.HOMESTAY,
        } else MarketplaceListing.Kind.PACKAGE
    listing = MarketplaceListing.objects.create(
        partner=partner, destination=dest, kind=kind,
        title=title[:220], summary=str(data.get("summary") or "")[:320],
        description=str(data.get("description") or "")[:8000],
        includes=str(data.get("includes") or "")[:4000],
        excludes=str(data.get("excludes") or "")[:4000],
        duration_days=duration_days, price_npr=price,
        image_url=image_url, external_url=external_url,
        city=str(data.get("city") or "")[:120],
        district=str(data.get("district") or "")[:120],
        cancellation_policy=str(data.get("cancellation_policy") or "")[:320],
        capacity=capacity,
        is_featured=bool(data.get("is_featured")) if allow_featured else False,
        status=status_value, updated_by=user,
    )
    return listing


class PublicMarketplaceView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug=None):
        if slug:
            listing = MarketplaceListing.objects.filter(slug=slug, status="published", partner__status="approved").select_related("partner", "destination").first()
            if not listing:
                return Response({"detail": "Offer not found"}, status=404)
            return Response(_listing_row(listing))
        qs = MarketplaceListing.objects.filter(status="published", partner__status="approved").select_related("partner", "destination")
        kind = (request.query_params.get("kind") or "").strip()
        if kind:
            qs = qs.filter(kind=kind)
        q = (request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(summary__icontains=q) | Q(city__icontains=q) | Q(district__icontains=q) | Q(destination__name__icontains=q))
        featured = request.query_params.get("featured")
        if featured in {"1", "true"}:
            qs = qs.filter(is_featured=True)
        dest = request.query_params.get("destination")
        if dest:
            qs = qs.filter(Q(destination__slug=dest) | Q(destination_id=dest if str(dest).isdigit() else None))
        rows = [_listing_row(item) for item in qs.order_by("-is_featured", "-updated_at")[:80]]
        return Response({"count": len(rows), "results": rows})


class PublicPartnerApplyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        name = str(request.data.get("name") or "").strip()
        email = str(request.data.get("email") or "").strip()
        if not name or not email:
            return Response({"detail": "Business name and email are required"}, status=400)
        kind = str(request.data.get("kind") or MarketplacePartner.Kind.OPERATOR)
        if kind not in MarketplacePartner.Kind.values:
            return Response({"detail": "Unknown partner type"}, status=400)
        try:
            website = _https_or_blank(request.data.get("website"))
            logo_url = _https_or_blank(request.data.get("logo_url"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        partner = MarketplacePartner.objects.create(
            name=name[:200], kind=kind, email=email[:254],
            contact_name=str(request.data.get("contact_name") or "")[:160],
            phone=str(request.data.get("phone") or "")[:40],
            website=website, city=str(request.data.get("city") or "")[:120],
            district=str(request.data.get("district") or "")[:120],
            description=str(request.data.get("description") or "")[:4000],
            services=str(request.data.get("services") or "")[:4000],
            license_info=str(request.data.get("license_info") or "")[:240],
            logo_url=logo_url,
            status=MarketplacePartner.Status.PENDING,
            user=request.user if request.user.is_authenticated else None,
        )
        _notify_marketplace_admins(
            f"Partner application: {partner.name}",
            f"{partner.name} ({partner.kind}) applied from {partner.email}. Review it in Packages & partners.",
            metadata={"partner_id": partner.id},
        )
        applicant = partner.user or User.objects.filter(email__iexact=partner.email, is_active=True).first()
        _notify_user(
            applicant, "We received your partner application",
            f"{partner.name} is pending review. You can add packages only after an administrator approves the business.",
            metadata={"partner_id": partner.id},
        )
        log_action(
            request, "partner.apply", category="admin",
            message=f"Partner application {partner.name}", obj=partner, user=applicant,
        )
        return Response({
            "id": partner.id,
            "message": "Application submitted successfully. Our team will review your application and contact you.",
            "status": partner.status,
        }, status=201)


class MarketplaceCheckoutView(APIView):
    permission_classes = [permissions.AllowAny]

    CARD_KEYS = CARD_KEYS

    def post(self, request):
        if _contains_card_fields(request.data):
            return Response({"detail": "Do not send card numbers, CVV or expiry details here. Use request-to-book or the partner HTTPS checkout."}, status=400)
        items = request.data.get("items") or []
        if not isinstance(items, list) or not items:
            return Response({"detail": "Add at least one package or offer to the trip basket"}, status=400)
        guest_name = str(request.data.get("guest_name") or "").strip()
        guest_email = str(request.data.get("guest_email") or "").strip()
        if not guest_name or not guest_email:
            return Response({"detail": "Traveller name and email are required"}, status=400)
        method = str(request.data.get("payment_method") or "request")
        if method not in MarketplaceOrder.PayMethod.values:
            return Response({"detail": "payment_method must be request or external"}, status=400)
        from django.utils.dateparse import parse_date
        try:
            travelers = max(1, min(20, int(request.data.get("travelers") or 1)))
        except (TypeError, ValueError):
            return Response({"detail": "travelers must be a number"}, status=400)
        start_raw = request.data.get("start_date") or None
        start_date = None
        if start_raw:
            start_date = parse_date(str(start_raw)[:10])
            if not start_date:
                return Response({"detail": "start_date must be YYYY-MM-DD"}, status=400)
        order = MarketplaceOrder.objects.create(
            user=request.user if request.user.is_authenticated else None,
            guest_name=guest_name[:160], guest_email=guest_email[:254],
            guest_phone=str(request.data.get("guest_phone") or "")[:40],
            travelers=travelers,
            start_date=start_date,
            notes=str(request.data.get("notes") or "")[:2000],
            payment_method=method,
            status=MarketplaceOrder.Status.EXTERNAL if method == "external" else MarketplaceOrder.Status.REQUESTED,
        )
        external_links = []
        for raw in items[:12]:
            listing = MarketplaceListing.objects.filter(pk=raw.get("listing_id"), status="published", partner__status="approved").first()
            if not listing:
                order.delete()
                return Response({"detail": "One of the selected offers is not available"}, status=400)
            try:
                qty = max(1, min(20, int(raw.get("quantity") or 1)))
            except (TypeError, ValueError):
                order.delete()
                return Response({"detail": "quantity must be a number"}, status=400)
            travel_date = None
            if raw.get("travel_date"):
                travel_date = parse_date(str(raw.get("travel_date"))[:10])
            unit = listing.price_npr
            MarketplaceOrderItem.objects.create(
                order=order, listing=listing, title=listing.title, quantity=qty,
                unit_price_npr=unit, line_total_npr=unit * qty,
                travel_date=travel_date, external_url=listing.external_url,
            )
            if listing.external_url:
                external_links.append({"title": listing.title, "url": listing.external_url})
        order.recompute()
        traveller = request.user if request.user.is_authenticated else User.objects.filter(email__iexact=guest_email).first()
        _notify_user(
            traveller, f"Trip request {order.reference}",
            f"Your booking request {order.reference} was received. Status: {order.get_status_display()}. No payment is processed on Nepal Tourism.",
            metadata={"order_id": order.id, "reference": order.reference},
        )
        partner_users = {
            item.listing.partner.user
            for item in order.items.select_related("listing__partner")
            if item.listing.partner.user_id
        }
        for partner_user in partner_users:
            _notify_user(
                partner_user, f"New trip request {order.reference}",
                f"{order.guest_name} requested {order.items.count()} offer(s). Open the partner desk to follow up.",
                metadata={"order_id": order.id, "reference": order.reference},
            )
        log_action(
            request, "order.create", category="data",
            message=f"Trip request {order.reference}", obj=order,
            extra={"status": order.status, "payment_method": order.payment_method},
        )
        return Response({
            "message": "Booking request saved. No payment is processed on Nepal Tourism. Pay later with the operator or continue on their HTTPS site.",
            "order": _order_row(order),
            "external_links": external_links,
        }, status=201)


class AdminMarketplaceView(APIView):
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        _require_capability(request, "marketplace", "view")
        resource = request.query_params.get("resource", "listings")
        q = (request.query_params.get("q") or "").strip()
        if resource == "partners":
            qs = MarketplacePartner.objects.all()
            state = request.query_params.get("status")
            if state:
                qs = qs.filter(status=state)
            if q:
                qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(city__icontains=q))
            return Response({"resource": "partners", "results": [_partner_row(row) for row in qs[:200]]})
        if resource == "orders":
            qs = MarketplaceOrder.objects.exclude(status="draft").prefetch_related("items__listing")
            if q:
                qs = qs.filter(Q(reference__icontains=q) | Q(guest_email__icontains=q) | Q(guest_name__icontains=q))
            return Response({"resource": "orders", "results": [_order_row(row) for row in qs[:200]]})
        qs = MarketplaceListing.objects.select_related("partner", "destination")
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        if request.query_params.get("kind"):
            qs = qs.filter(kind=request.query_params["kind"])
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(partner__name__icontains=q) | Q(city__icontains=q))
        return Response({"resource": "listings", "results": [_listing_row(row) for row in qs[:200]]})

    def post(self, request):
        resource = request.data.get("resource", "listings")
        if resource == "partners":
            _require_capability(request, "marketplace", "add")
            name = str(request.data.get("name") or "").strip()
            email = str(request.data.get("email") or "").strip()
            if not name or not email:
                return Response({"detail": "name and email are required"}, status=400)
            try:
                website = _https_or_blank(request.data.get("website"))
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=400)
            try:
                logo_url = _https_or_blank(request.data.get("logo_url"))
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=400)
            partner = MarketplacePartner.objects.create(
                name=name[:200], kind=request.data.get("kind") or "operator",
                email=email, contact_name=str(request.data.get("contact_name") or "")[:160],
                phone=str(request.data.get("phone") or "")[:40], website=website,
                city=str(request.data.get("city") or "")[:120],
                district=str(request.data.get("district") or "")[:120],
                description=str(request.data.get("description") or "")[:4000],
                services=str(request.data.get("services") or "")[:4000],
                license_info=str(request.data.get("license_info") or "")[:240],
                logo_url=logo_url,
                status=request.data.get("status") or "approved",
            )
            return Response({"id": partner.id, "message": "Partner saved", "record": _partner_row(partner)}, status=201)
        _require_capability(request, "marketplace", "add")
        partner = MarketplacePartner.objects.filter(pk=request.data.get("partner_id"), status="approved").first()
        if not partner:
            return Response({"detail": "Choose an approved partner"}, status=400)
        requested_status = request.data.get("status") or MarketplaceListing.Status.PUBLISHED
        if requested_status == MarketplaceListing.Status.PUBLISHED or request.data.get("is_featured"):
            _require_capability(request, "marketplace", "approve")
        try:
            listing = _listing_from_payload(
                request.data, partner, request.user,
                default_status=MarketplaceListing.Status.PUBLISHED,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        log_action(
            request, "listing.create", category="admin",
            message=f"Created listing {listing.title}", obj=listing,
            extra={"status": listing.status, "featured": listing.is_featured},
        )
        return Response({"id": listing.id, "message": "Offer saved", "record": _listing_row(listing)}, status=201)

    def patch(self, request):
        _require_capability(request, "marketplace", "change")
        resource = request.data.get("resource", "listings")
        if resource == "partners":
            partner = MarketplacePartner.objects.filter(pk=request.data.get("id")).first()
            if not partner:
                return Response({"detail": "Partner not found"}, status=404)
            action = request.data.get("action")
            if action in {"approve", "reject", "suspend", "review"}:
                _require_capability(request, "marketplace", "approve")
                partner.status = {
                    "approve": MarketplacePartner.Status.APPROVED,
                    "reject": MarketplacePartner.Status.REJECTED,
                    "suspend": MarketplacePartner.Status.SUSPENDED,
                    "review": MarketplacePartner.Status.UNDER_REVIEW,
                }[action]
                partner.reviewed_by = request.user
                partner.reviewed_at = timezone.now()
            for field in ("name", "kind", "email", "phone", "city", "district", "description", "admin_note", "contact_name"):
                if field in request.data:
                    setattr(partner, field, request.data[field])
            if "website" in request.data:
                try:
                    partner.website = _https_or_blank(request.data.get("website"))
                except ValueError as exc:
                    return Response({"detail": str(exc)}, status=400)
            if "commission_percent" in request.data:
                partner.commission_percent = _money(request.data.get("commission_percent"), "10")
            if "logo_url" in request.data:
                try:
                    partner.logo_url = _https_or_blank(request.data.get("logo_url"))
                except ValueError as exc:
                    return Response({"detail": str(exc)}, status=400)
            partner.save()
            _link_partner_user(partner)
            if action == "approve":
                _notify_user(
                    partner.user, "Your application has been approved",
                    f"{partner.name} can now add packages from the partner desk. An administrator still reviews each offer before it is public.",
                    metadata={"partner_id": partner.id},
                )
            elif action == "reject":
                _notify_user(
                    partner.user, "Your application was not approved",
                    f"{partner.name} was not approved. Check the note from the tourism desk or apply again with updated details.",
                    metadata={"partner_id": partner.id},
                )
            elif action == "review":
                _notify_user(
                    partner.user, "Your application is under review",
                    f"{partner.name} is now being reviewed by the tourism desk.",
                    metadata={"partner_id": partner.id},
                )
            elif action == "suspend":
                _notify_user(
                    partner.user, "Your partner account was suspended",
                    f"{partner.name} can no longer manage packages until an administrator restores access.",
                    metadata={"partner_id": partner.id},
                )
            if action:
                log_action(
                    request, f"partner.{action}", category="admin",
                    message=f"Partner {partner.name} → {partner.status}", obj=partner,
                    extra={"status": partner.status},
                )
            return Response({"message": "Partner updated", "record": _partner_row(partner)})
        if resource == "orders":
            order = MarketplaceOrder.objects.filter(pk=request.data.get("id")).first()
            if not order:
                return Response({"detail": "Order not found"}, status=404)
            action = request.data.get("action")
            allowed = {
                "confirm": MarketplaceOrder.Status.CONFIRMED,
                "review": MarketplaceOrder.Status.UNDER_REVIEW,
                "cancel": MarketplaceOrder.Status.CANCELLED,
            }
            if action not in allowed:
                return Response({"detail": "action must be review, confirm or cancel"}, status=400)
            if action not in ORDER_TRANSITIONS.get(order.status, set()):
                return Response(
                    {"detail": f"Cannot {action} a {order.status} request"},
                    status=400,
                )
            order.status = allowed[action]
            order.save(update_fields=["status", "updated_at"])
            traveller = order.user or User.objects.filter(email__iexact=order.guest_email).first()
            _notify_user(
                traveller, f"Trip request {order.reference}",
                f"Your request {order.reference} is now {order.get_status_display()}.",
                metadata={"order_id": order.id, "reference": order.reference, "status": order.status},
            )
            log_action(
                request, f"order.{action}", category="admin",
                message=f"Order {order.reference} → {order.status}", obj=order,
                extra={"status": order.status},
            )
            return Response({"message": f"Order {action}ed", "record": _order_row(order)})
        listing = MarketplaceListing.objects.filter(pk=request.data.get("id")).first()
        if not listing:
            return Response({"detail": "Listing not found"}, status=404)
        listing_action = request.data.get("action")
        if listing_action in {"publish", "archive"} or "is_featured" in request.data or request.data.get("status") in {
            MarketplaceListing.Status.PUBLISHED, MarketplaceListing.Status.ARCHIVED,
        }:
            _require_capability(request, "marketplace", "approve")
        published_now = False
        if listing_action == "publish":
            if listing.partner.status != MarketplacePartner.Status.APPROVED:
                return Response({"detail": "Approve the partner before publishing this offer"}, status=400)
            listing.status = MarketplaceListing.Status.PUBLISHED
            published_now = True
        elif listing_action == "archive":
            listing.status = MarketplaceListing.Status.ARCHIVED
        for field in ("title", "summary", "description", "includes", "excludes", "kind", "city", "district", "cancellation_policy", "status"):
            if field in request.data:
                setattr(listing, field, request.data[field])
        if "price_npr" in request.data:
            listing.price_npr = _money(request.data.get("price_npr"))
        if "duration_days" in request.data:
            listing.duration_days = _int(request.data["duration_days"], 1, 1, 60)
        if "capacity" in request.data:
            listing.capacity = _int(request.data["capacity"], 10, 1, 200)
        if "is_featured" in request.data:
            listing.is_featured = bool(request.data["is_featured"])
        if "destination_id" in request.data:
            listing.destination = Destination.objects.filter(pk=request.data.get("destination_id")).first()
        if "image_url" in request.data:
            listing.image_url = _https_or_blank(request.data.get("image_url"))
        if "external_url" in request.data:
            listing.external_url = _https_or_blank(request.data.get("external_url"))
        listing.updated_by = request.user
        listing.save()
        if published_now:
            _notify_user(
                listing.partner.user, "Your package is live",
                f"“{listing.title}” is now published on Nepal Tourism packages.",
                metadata={"listing_id": listing.id, "slug": listing.slug},
            )
        log_action(
            request, f"listing.{listing_action or 'update'}", category="admin",
            message=f"Updated listing {listing.title}", obj=listing,
            extra={"status": listing.status, "featured": listing.is_featured},
        )
        return Response({"message": "Offer updated", "record": _listing_row(listing)})


class PartnerDeskView(APIView):
    """Approved partners add/edit packages. They cannot publish themselves."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        partner = _partner_for_user(request.user)
        if not partner:
            return Response({
                "detail": "No partner application is linked to this account. Apply at /collaborate.",
                "partner": None,
            }, status=404)
        listings = [
            _listing_row(row)
            for row in partner.listings.select_related("destination").order_by("-updated_at")[:100]
        ]
        orders = []
        if partner.status == MarketplacePartner.Status.APPROVED:
            orders = [
                _order_row(order)
                for order in MarketplaceOrder.objects.filter(items__listing__partner=partner)
                .exclude(status=MarketplaceOrder.Status.DRAFT)
                .distinct()
                .prefetch_related("items__listing")[:50]
            ]
        return Response({
            "partner": _partner_row(partner),
            "can_manage_listings": partner.status == MarketplacePartner.Status.APPROVED,
            "listings": listings,
            "orders": orders,
            "message": (
                None if partner.status == MarketplacePartner.Status.APPROVED
                else f"Your application is {partner.get_status_display().lower()}. You can add packages after approval."
            ),
        })

    def post(self, request):
        partner = _partner_for_user(request.user)
        if not partner:
            return Response({"detail": "Apply to collaborate first"}, status=404)
        if partner.status != MarketplacePartner.Status.APPROVED:
            return Response({"detail": "Your business must be approved before you can add packages"}, status=403)
        try:
            listing = _listing_from_payload(
                request.data, partner, request.user,
                force_status=MarketplaceListing.Status.PENDING, allow_featured=False,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        _notify_marketplace_admins(
            f"New package pending: {listing.title}",
            f"{partner.name} submitted “{listing.title}”. Review it in Packages & partners before it is public.",
            metadata={"listing_id": listing.id, "partner_id": partner.id},
        )
        _notify_user(
            request.user, "Package submitted for review",
            f"“{listing.title}” is pending. An administrator must publish it before travellers can see it.",
            metadata={"listing_id": listing.id, "partner_id": partner.id},
        )
        log_action(
            request, "listing.submit", category="data",
            message=f"Partner submitted {listing.title}", obj=listing,
        )
        return Response({
            "id": listing.id,
            "message": "Package submitted for review. An administrator must publish it before travellers can see it.",
            "record": _listing_row(listing),
        }, status=201)

    def patch(self, request):
        partner = _partner_for_user(request.user)
        if not partner or partner.status != MarketplacePartner.Status.APPROVED:
            return Response({"detail": "Approved partner desk only"}, status=403)
        listing = partner.listings.filter(pk=request.data.get("id")).first()
        if not listing:
            return Response({"detail": "Listing not found"}, status=404)
        if request.data.get("action") == "publish" or request.data.get("status") == MarketplaceListing.Status.PUBLISHED:
            return Response({"detail": "An administrator must publish this offer"}, status=400)
        if request.data.get("action") == "archive" or request.data.get("status") == MarketplaceListing.Status.ARCHIVED:
            return Response({"detail": "An administrator must archive this offer"}, status=400)
        if request.data.get("is_featured") or request.data.get("action") == "feature":
            return Response({"detail": "An administrator must feature this offer"}, status=400)
        try:
            for field in ("title", "summary", "description", "includes", "excludes", "kind", "city", "district", "cancellation_policy"):
                if field in request.data:
                    setattr(listing, field, request.data[field])
            if "price_npr" in request.data:
                listing.price_npr = _money(request.data.get("price_npr"))
            if "duration_days" in request.data:
                listing.duration_days = _int(request.data["duration_days"], 1, 1, 60)
            if "capacity" in request.data:
                listing.capacity = _int(request.data["capacity"], 10, 1, 200)
            if "image_url" in request.data:
                listing.image_url = _https_or_blank(request.data.get("image_url"))
            if "external_url" in request.data:
                listing.external_url = _https_or_blank(request.data.get("external_url"))
            if "destination_id" in request.data:
                listing.destination = Destination.objects.filter(pk=request.data.get("destination_id")).first()
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        listing.is_featured = False
        if listing.status == MarketplaceListing.Status.PUBLISHED:
            listing.status = MarketplaceListing.Status.PENDING
            _notify_marketplace_admins(
                f"Package update pending: {listing.title}",
                f"{partner.name} edited a live offer. Review it before it stays public.",
                metadata={"listing_id": listing.id, "partner_id": partner.id},
            )
        elif request.data.get("action") == "archive":
            listing.status = MarketplaceListing.Status.ARCHIVED
        listing.updated_by = request.user
        listing.save()
        return Response({"message": "Offer updated", "record": _listing_row(listing)})


class MarketplaceOrderLookupView(APIView):
    """Travellers look up a request by reference + email, or list their own."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        reference = str(request.query_params.get("reference") or "").strip()
        email = str(request.query_params.get("email") or "").strip()
        if request.user.is_authenticated and not reference:
            orders = MarketplaceOrder.objects.filter(
                Q(user=request.user) | Q(guest_email__iexact=request.user.email)
            ).exclude(status=MarketplaceOrder.Status.DRAFT).prefetch_related("items__listing")[:50]
            return Response({"results": [_order_row(order) for order in orders]})
        if not reference or not email:
            return Response({"detail": "reference and email are required"}, status=400)
        order = MarketplaceOrder.objects.filter(
            reference__iexact=reference, guest_email__iexact=email,
        ).exclude(status=MarketplaceOrder.Status.DRAFT).prefetch_related("items__listing").first()
        if not order:
            return Response({"detail": "No booking request matches that reference and email"}, status=404)
        return Response({"order": _order_row(order)})
