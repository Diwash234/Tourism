"""
Advanced search with autocomplete, suggestions, and faceted search.
"""
from django.db.models import Q, Count
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Destination, Category


class SearchAutocompleteView(APIView):
    """
    GET /api/v1/search/autocomplete/?q=pok

    Returns matching destinations, categories, and districts for autocomplete.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response({"suggestions": []})

        # Search destinations
        destinations = Destination.objects.filter(
            Q(name__icontains=query) | Q(district__icontains=query),
            is_published=True,
        ).values("id", "name", "slug", "district")[:5]

        # Search categories
        categories = Category.objects.filter(
            name__icontains=query,
        ).values("id", "name", "slug")[:3]

        # Search districts
        districts = Destination.objects.filter(
            district__icontains=query,
            is_published=True,
        ).values("district").distinct()[:3]

        suggestions = []
        for d in destinations:
            suggestions.append({
                "type": "destination",
                "id": d["id"],
                "name": d["name"],
                "slug": d["slug"],
                "district": d["district"],
            })
        for c in categories:
            suggestions.append({
                "type": "category",
                "id": c["id"],
                "name": c["name"],
                "slug": c["slug"],
            })
        for d in districts:
            suggestions.append({
                "type": "district",
                "name": d["district"],
            })

        return Response({"suggestions": suggestions})


class FacetedSearchView(APIView):
    """
    GET /api/v1/search/faceted/?q=pok&category=lake&district=Kathmandu

    Returns search results with facet counts for filtering.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        category = request.query_params.get("category", "").strip()
        district = request.query_params.get("district", "").strip()
        province = request.query_params.get("province", "").strip()

        # Base queryset
        queryset = Destination.objects.filter(is_published=True)

        # Apply filters
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(district__icontains=query)
            )
        if category:
            queryset = queryset.filter(category__slug__iexact=category)
        if district:
            queryset = queryset.filter(district__iexact=district)
        if province:
            queryset = queryset.filter(province__iexact=province)

        # Get facet counts
        category_facets = queryset.values("category__name").annotate(
            count=Count("id")
        ).order_by("-count")[:10]

        district_facets = queryset.values("district").annotate(
            count=Count("id")
        ).order_by("-count")[:10]

        province_facets = queryset.values("province").annotate(
            count=Count("id")
        ).order_by("-count")[:10]

        # Paginate results
        from .pagination import StandardResultsPagination
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request)

        from .serializers import DestinationListSerializer
        serializer = DestinationListSerializer(page, many=True, context={"request": request})

        return paginator.get_paginated_response({
            "results": serializer.data,
            "facets": {
                "categories": [{"name": f["category__name"], "count": f["count"]} for f in category_facets],
                "districts": [{"name": f["district"], "count": f["count"]} for f in district_facets],
                "provinces": [{"name": f["province"], "count": f["count"]} for f in province_facets],
            },
        })
