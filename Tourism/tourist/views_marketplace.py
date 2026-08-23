"""Partner marketplace: listings, applications, trip basket, request checkout."""
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Destination, MarketplaceListing, MarketplaceOrder, MarketplaceOrderItem, MarketplacePartner
from .permissions import IsAdminOrStaff
from .views_admin import _has_capability, _require_capability


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
        "description": partner.description, "status": partner.status,
        "commission_percent": str(partner.commission_percent),
        "listing_count": partner.listings.count(),
        "admin_note": partner.admin_note, "created_at": partner.created_at,
    }


def _order_row(order):
    return {
        "id": order.id, "reference": order.reference, "status": order.status,
        "payment_method": order.payment_method, "guest_name": order.guest_name,
        "guest_email": order.guest_email, "guest_phone": order.guest_phone,
        "travelers": order.travelers, "start_date": order.start_date, "notes": order.notes,
        "subtotal_npr": str(order.subtotal_npr), "total_npr": str(order.total_npr),
        "currency": order.currency, "created_at": order.created_at,
        "items": [{
            "id": item.id, "listing_id": item.listing_id, "title": item.title,
            "quantity": item.quantity, "unit_price_npr": str(item.unit_price_npr),
            "line_total_npr": str(item.line_total_npr), "travel_date": item.travel_date,
            "external_url": item.external_url, "slug": item.listing.slug,
        } for item in order.items.select_related("listing")],
    }


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
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        partner = MarketplacePartner.objects.create(
            name=name[:200], kind=kind, email=email[:254],
            contact_name=str(request.data.get("contact_name") or "")[:160],
            phone=str(request.data.get("phone") or "")[:40],
            website=website, city=str(request.data.get("city") or "")[:120],
            district=str(request.data.get("district") or "")[:120],
            description=str(request.data.get("description") or "")[:4000],
            status=MarketplacePartner.Status.PENDING,
            user=request.user if request.user.is_authenticated else None,
        )
        return Response({"id": partner.id, "message": "Application received. An administrator will review it.", "status": partner.status}, status=201)


class MarketplaceCheckoutView(APIView):
    permission_classes = [permissions.AllowAny]

    CARD_KEYS = {"card_number", "cvv", "cvc", "pan", "cardNumber"}

    def post(self, request):
        if any(key in request.data for key in self.CARD_KEYS):
            return Response({"detail": "Do not send card numbers here. Use request-to-book or the partner HTTPS checkout."}, status=400)
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
        if request.user.is_authenticated:
            from .notification_delivery import queue_notification
            queue_notification(
                request.user, f"Trip request {order.reference}",
                f"We received your request for {order.items.count()} offer(s). Total NPR {order.total_npr}.",
                channel="in_app", category="booking", metadata={"order_id": order.id, "reference": order.reference},
            )
        return Response({
            "message": "Trip request saved. Pay with the operator or continue on their site — we never store card numbers.",
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
            partner = MarketplacePartner.objects.create(
                name=name[:200], kind=request.data.get("kind") or "operator",
                email=email, contact_name=str(request.data.get("contact_name") or "")[:160],
                phone=str(request.data.get("phone") or "")[:40], website=website,
                city=str(request.data.get("city") or "")[:120],
                district=str(request.data.get("district") or "")[:120],
                description=str(request.data.get("description") or "")[:4000],
                status=request.data.get("status") or "approved",
            )
            return Response({"id": partner.id, "message": "Partner saved", "record": _partner_row(partner)}, status=201)
        _require_capability(request, "marketplace", "add")
        partner = MarketplacePartner.objects.filter(pk=request.data.get("partner_id"), status="approved").first()
        if not partner:
            return Response({"detail": "Choose an approved partner"}, status=400)
        title = str(request.data.get("title") or "").strip()
        if not title:
            return Response({"detail": "title is required"}, status=400)
        try:
            image_url = _https_or_blank(request.data.get("image_url"))
            external_url = _https_or_blank(request.data.get("external_url"))
            price = _money(request.data.get("price_npr"))
            duration_days = _int(request.data.get("duration_days"), 1, 1, 60)
            capacity = _int(request.data.get("capacity"), 10, 1, 200)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        dest = Destination.objects.filter(pk=request.data.get("destination_id")).first() if request.data.get("destination_id") else None
        listing = MarketplaceListing.objects.create(
            partner=partner, destination=dest, kind=request.data.get("kind") or "package",
            title=title[:220], summary=str(request.data.get("summary") or "")[:320],
            description=str(request.data.get("description") or "")[:8000],
            includes=str(request.data.get("includes") or "")[:4000],
            excludes=str(request.data.get("excludes") or "")[:4000],
            duration_days=duration_days,
            price_npr=price, image_url=image_url, external_url=external_url,
            city=str(request.data.get("city") or "")[:120],
            district=str(request.data.get("district") or "")[:120],
            cancellation_policy=str(request.data.get("cancellation_policy") or "")[:320],
            capacity=capacity,
            is_featured=bool(request.data.get("is_featured")),
            status=request.data.get("status") or "published",
            updated_by=request.user,
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
            if action in {"approve", "reject", "suspend"}:
                _require_capability(request, "marketplace", "approve")
                partner.status = {"approve": "approved", "reject": "rejected", "suspend": "suspended"}[action]
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
            partner.save()
            return Response({"message": "Partner updated", "record": _partner_row(partner)})
        if resource == "orders":
            order = MarketplaceOrder.objects.filter(pk=request.data.get("id")).first()
            if not order:
                return Response({"detail": "Order not found"}, status=404)
            action = request.data.get("action")
            if action == "confirm":
                order.status = MarketplaceOrder.Status.CONFIRMED
            elif action == "cancel":
                order.status = MarketplaceOrder.Status.CANCELLED
            else:
                return Response({"detail": "action must be confirm or cancel"}, status=400)
            order.save(update_fields=["status", "updated_at"])
            return Response({"message": f"Order {action}ed", "record": _order_row(order)})
        listing = MarketplaceListing.objects.filter(pk=request.data.get("id")).first()
        if not listing:
            return Response({"detail": "Listing not found"}, status=404)
        if request.data.get("action") == "publish":
            if listing.partner.status != MarketplacePartner.Status.APPROVED:
                return Response({"detail": "Approve the partner before publishing this offer"}, status=400)
            listing.status = "published"
        elif request.data.get("action") == "archive":
            listing.status = "archived"
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
        return Response({"message": "Offer updated", "record": _listing_row(listing)})
