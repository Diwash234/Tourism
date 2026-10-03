"""
Budget Computation Services

Computes destination budget profiles from price components,
aggregates verified user feedback, and triggers ML model retraining.
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from django.db.models import Q, Avg, Min, Max
from django.conf import settings
from django.utils import timezone
from .models import (
    Destination, PriceComponent, DestinationBudgetProfile,
    TravelExpenseFeedback, PriceComponentHistory
)


USD_NPR_RATE = getattr(settings, 'USD_NPR_RATE', Decimal('132.0'))


# Category mapping for budget profile computation
CATEGORY_MAP = {
    # Budget style
    "budget": {
        "transport_intercity": ["transport_intercity"],
        "transport_local": ["transport_local"],
        "accommodation": ["accommodation_budget"],
        "food": ["food_budget"],
        "entry_fees": ["entry_fee_park", "entry_fee_heritage", "entry_fee_museum", "entry_fee_other"],
        "guide_porter": ["guide_porter"],
        "permits": ["permit_trek", "permit_other"],
        "misc": ["misc"],
    },
    # Standard style
    "standard": {
        "transport_intercity": ["transport_intercity"],
        "transport_local": ["transport_local"],
        "accommodation": ["accommodation_standard"],
        "food": ["food_standard"],
        "entry_fees": ["entry_fee_park", "entry_fee_heritage", "entry_fee_museum", "entry_fee_other"],
        "guide_porter": ["guide_porter"],
        "permits": ["permit_trek", "permit_other"],
        "misc": ["misc"],
    },
    # Premium style
    "premium": {
        "transport_intercity": ["transport_intercity", "transport_flight"],
        "transport_local": ["transport_local"],
        "accommodation": ["accommodation_luxury"],
        "food": ["food_premium"],
        "entry_fees": ["entry_fee_park", "entry_fee_heritage", "entry_fee_museum", "entry_fee_other"],
        "guide_porter": ["guide_porter"],
        "permits": ["permit_trek", "permit_other"],
        "misc": ["misc"],
    },
}


def _get_applicable_components(destination, category, travel_style):
    """
    Get the best matching price component for a destination/category/style combo.
    Priority: destination-specific > district > province > national
    """
    from .models import PriceComponent

    cats = CATEGORY_MAP[travel_style].get(category, [])
    if not cats:
        return None

    today = date.today()

    # Try destination-specific first
    if destination:
        qs = PriceComponent.objects.filter(
            destination=destination,
            category__in=cats,
            is_active=True,
            is_verified=True,
            effective_from__lte=date.today()
        ).filter(
            Q(effective_until__isnull=True) | Q(effective_until__gte=date.today())
        ).order_by('-effective_from')

        comp = qs.first()
        if comp:
            return comp

    # Try district
    if destination and destination.district:
        qs = PriceComponent.objects.filter(
            district=destination.district,
            category__in=cats,
            is_active=True,
            is_verified=True,
            effective_from__lte=date.today()
        ).filter(
            Q(effective_until__isnull=True) | Q(effective_until__gte=date.today())
        ).order_by('-effective_from')

        comp = qs.first()
        if comp:
            return comp

    # Try province
    if destination and destination.province:
        qs = PriceComponent.objects.filter(
            province=destination.province,
            category__in=cats,
            is_active=True,
            is_verified=True,
            effective_from__lte=date.today()
        ).filter(
            Q(effective_until__isnull=True) | Q(effective_until__gte=date.today())
        ).order_by('-effective_from')

        comp = qs.first()
        if comp:
            return comp

    # National default
    qs = PriceComponent.objects.filter(
        province="", district="", destination__isnull=True,
        category__in=cats,
        is_active=True,
        is_verified=True,
        effective_from__lte=date.today()
    ).filter(
        Q(effective_until__isnull=True) | Q(effective_until__gte=date.today())
    ).order_by('-effective_from')

    return qs.first()


def compute_destination_budget_profile(destination):
    """
    Compute the full budget profile for a destination.
    Returns the updated DestinationBudgetProfile instance.
    """
    from .models import DestinationBudgetProfile

    # Get or create profile
    profile, created = DestinationBudgetProfile.objects.get_or_create(
        destination=destination
    )

    # Compute for each travel style
    styles = ["budget", "standard", "premium"]
    categories = [
        "transport_intercity", "transport_local", "accommodation",
        "food", "entry_fees", "guide_porter", "permits", "misc"
    ]

    components_used = []

    for style in styles:
        style_totals = {}
        for cat in categories:
            comp = _get_applicable_components(destination, cat, style)
            if comp:
                components_used.append(comp.id)
                # Convert to daily cost based on unit
                # For simplicity, assuming unit is already per-day equivalent
                # In reality, you'd multiply by quantity (e.g., km, nights)
                daily_value = comp.base_price_npr
                style_totals[cat] = daily_value
            else:
                style_totals[cat] = Decimal('0')

        # Sum for daily total
        daily_total = sum(style_totals.values(), Decimal('0'))

        # Store in profile
        for cat in categories:
            field_name = f"{cat}_npr"
            setattr(profile, field_name, style_totals[cat])

        # Daily totals per style
        if style == "budget":
            profile.budget_daily_npr = sum(style_totals.values(), Decimal('0'))
            profile.budget_daily_usd = (profile.budget_daily_npr / USD_NPR_RATE).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        elif style == "standard":
            profile.standard_daily_npr = sum(style_totals.values(), Decimal('0'))
            profile.standard_daily_usd = (profile.standard_daily_npr / USD_NPR_RATE).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        elif style == "premium":
            profile.premium_daily_npr = sum(style_totals.values(), Decimal('0'))
            profile.premium_daily_usd = (profile.premium_daily_npr / USD_NPR_RATE).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )

    # USD rate
    profile.usd_rate_used = USD_NPR_RATE

    # Components used (deduplicated)
    profile.components_used = list(set(components_used))
    profile.computation_version += 1
    profile.save()

    return profile


def recompute_all_budget_profiles():
    """Trigger recomputation for all active destinations."""
    destinations = Destination.objects.filter(
        is_active=True,
        status=Destination.SubmissionStatus.APPROVED
    )
    count = 0
    for dest in destinations:
        compute_destination_budget_profile(dest)
        count += 1
    return count


def aggregate_expense_to_components(feedback, admin_user):
    """
    Aggregate a verified TravelExpenseFeedback into PriceComponent updates.
    This is called when an admin verifies a user's expense feedback.
    """
    from .models import PriceComponent, PriceComponentHistory

    if not feedback.destination:
        return {"aggregated": 0, "message": "No destination linked"}

    dest = feedback.destination
    num_days = feedback.num_days or 1
    num_people = feedback.num_people or 1
    total_people_days = num_days * num_people

    # Calculate per-unit costs from feedback
    # These are total costs for the trip, need to convert to unit prices
    mappings = [
        # (feedback_field, category, unit, description)
        ("transport_cost", "transport_intercity", "per trip", "Transport"),
        ("local_transport_cost", "transport_local", "per day", "Local Transport"),
        ("accommodation_cost", "accommodation_standard", "per night", "Accommodation"),
        ("food_cost", "food_standard", "per day", "Food"),
        ("entry_cost", "entry_fee_other", "per entry", "Entry Fees"),
        ("guide_porter_cost", "guide_porter", "per day", "Guide/Porter"),
        ("permit_cost", "permit_other", "per permit", "Permits"),
        ("misc_cost", "misc", "per trip", "Miscellaneous"),
    ]

    aggregated_count = 0
    today = timezone.now().date()

    for field, category, unit, desc in mappings:
        total_cost = getattr(feedback, field, Decimal('0'))
        if total_cost <= 0:
            continue

        # Compute unit price
        if unit == "per night":
            unit_price = total_cost / num_days
        elif unit == "per day":
            unit_price = total_cost / num_days
        elif unit == "per trip":
            unit_price = total_cost
        else:
            unit_price = total_cost / max(1, total_people_days)

        unit_price = unit_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Find or create component
        comp, created = PriceComponent.objects.get_or_create(
            destination=feedback.destination,
            category=category,
            name=f"{dest.name} {desc} (from verified feedback)",
            defaults={
                "unit": unit,
                "base_price_npr": unit_price,
                "effective_from": date.today(),
                "source_type": PriceComponent.SourceType.USER_FEEDBACK,
                "source_reference": f"Aggregated from feedback #{feedback.id}",
                "is_verified": True,
                "verified_by": admin_user,
                "verified_at": timezone.now(),
                "is_active": True,
            }
        )

        if not created:
            # Record history
            PriceComponentHistory.objects.create(
                component=comp,
                changed_by=admin_user,
                old_price_npr=comp.base_price_npr,
                new_price_npr=unit_price,
                old_effective_until=comp.effective_until,
                new_effective_until=comp.effective_until,
                change_reason=f"Aggregated from verified feedback #{feedback.id}",
                change_source=PriceComponent.SourceType.USER_FEEDBACK
            )
            comp.base_price_npr = unit_price
            comp.verified_by = admin_user
            comp.verified_at = timezone.now()
            comp.save(update_fields=["base_price_npr", "verified_by", "verified_at", "updated_at"])

        aggregated_count += 1

    # Invalidate budget profile cache for this destination
    from .models import DestinationBudgetProfile
    try:
        profile = DestinationBudgetProfile.objects.get(destination=feedback.destination)
        profile.computation_version += 1
        profile.save(update_fields=["computation_version", "updated_at"])
    except DestinationBudgetProfile.DoesNotExist:
        pass

    # Trigger ML model retraining (async)
    _trigger_ml_retrain()

    return {
        "aggregated": aggregated_count,
        "message": f"Aggregated {aggregated_count} cost categories to price components"
    }


def _trigger_ml_retrain():
    """Trigger ML model retraining asynchronously."""
    import subprocess
    import os
    try:
        ml_dir = os.path.join(settings.BASE_DIR.parent, "ml_service")
        script = os.path.join(ml_dir, "training", "train_budget_model.py")
        if os.path.exists(script):
            subprocess.Popen(
                ["python", script],
                cwd=ml_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    except Exception:
        pass  # Non-blocking