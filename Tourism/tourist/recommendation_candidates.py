"""Candidate selection for destination recommendations.

Kept in its own module for the same reason as ``budget_baseline``: the
recommendation behaviour must not depend on which copy of ``views_ml.py``
survives a refactor.

The bug this fixes: when a traveller's filters (province / category / interest)
matched fewer places than ``top_n``, the view used to throw every filter away
and re-query the globally top-rated destinations. Two travellers with different
interests therefore received byte-identical recommendations, which is exactly
the "different categories, same recommendations" report.

Filters are now relaxed one dimension at a time, least-loss first, and the
dimensions that were relaxed are reported so the response can say so out loud
instead of quietly returning a generic list.
"""

from django.db.models import Q

#: How many candidates are sent to the ranking engine. Bounds payload size and
#: network latency; 100 is plenty for a top-5/top-12 response.
MAX_CANDIDATES = 100

#: (label, (use_province, use_category, use_interest)) in the order they are
#: surrendered. "all filters" is the last resort and is always reported.
RELAXATION_ORDER = (
    ("province", (False, True, True)),
    ("interest", (True, True, False)),
    ("category", (True, False, True)),
    ("all filters", (False, False, False)),
)

CANDIDATE_FIELDS = (
    "id", "name", "slug", "type", "city", "district",
    "province", "latitude", "longitude", "average_rating",
)


def _build(queryset, *, province, category, interest,
           use_province, use_category, use_interest, limit):
    """Filter `queryset` by whichever dimensions are still switched on."""
    if use_province and province:
        queryset = queryset.filter(province__iexact=province)
    if use_category and category:
        # Match by name OR slug: the UI sends either, and a name-only match
        # silently ignored every slug a visitor picked.
        queryset = queryset.filter(
            Q(category__name__icontains=category) |
            Q(category__slug__icontains=category)
        )
    if use_interest and interest:
        queryset = queryset.filter(
            Q(name__icontains=interest) |
            Q(type__icontains=interest) |
            Q(description__icontains=interest) |
            Q(short_description__icontains=interest) |
            Q(cultural_significance__icontains=interest) |
            Q(category__name__icontains=interest) |
            Q(category__slug__icontains=interest)
        )
    return list(
        queryset.order_by("-is_featured", "-average_rating", "-views_count")
        .values(*CANDIDATE_FIELDS)[:limit]
    )


def select_recommendation_candidates(destination_model, *, province="", category="",
                                    interest="", top_n=5):
    """Return ``(rows, relaxations)`` for the recommendation engine.

    `rows` are dicts of CANDIDATE_FIELDS; `relaxations` lists the labels of the
    filters that had to be surrendered to reach `top_n` candidates.
    """
    top_n = max(1, int(top_n or 1))
    limit = max(MAX_CANDIDATES, top_n)

    def fetch(use_province, use_category, use_interest):
        base = destination_model.publicly_visible().exclude(
            latitude__isnull=True
        ).exclude(longitude__isnull=True)
        return _build(
            base,
            province=province, category=category, interest=interest,
            use_province=use_province, use_category=use_category,
            use_interest=use_interest, limit=limit,
        )

    relaxations = []
    rows = fetch(True, True, True)

    for label, flags in RELAXATION_ORDER:
        if len(rows) >= top_n:
            break
        relaxed = fetch(*flags)
        # Only accept a relaxation that actually widens the pool.
        if len(relaxed) > len(rows):
            relaxations.append(label)
            rows = relaxed

    return rows, relaxations


def diversify_destinations(candidates, *, top_n):
    """Prefer places that add a new category AND a new district.

    The previous condition ORed in ``len(chosen) < top_n``, which stays true for
    the whole loop, so it never rejected a repeat and every user received the
    same top-rated run. Now duplicates are deferred and only used to fill the
    quota once the diverse candidates are exhausted.
    """
    top_n = max(1, int(top_n or 1))
    seen_categories, seen_districts = set(), set()
    chosen, deferred = [], []

    for dest in candidates:
        category_id = getattr(dest, "category_id", None)
        district = getattr(dest, "district", "") or getattr(dest, "city", "")
        is_new = (category_id not in seen_categories) and (district not in seen_districts)
        if is_new or not (category_id or district):
            chosen.append(dest)
            if category_id:
                seen_categories.add(category_id)
            if district:
                seen_districts.add(district)
        else:
            deferred.append(dest)
        if len(chosen) >= top_n:
            break

    for dest in deferred:
        if len(chosen) >= top_n:
            break
        chosen.append(dest)

    return chosen
