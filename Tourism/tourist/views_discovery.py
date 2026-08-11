"""
Tourism/tourist/views_discovery.py

REST API views for the Mass Destination Discovery, Deduplication & Place Intelligence System.
Supports candidate inspection, multi-signal duplicate auditing, batch execution,
and bulk approval / alias merging.
"""

from collections import defaultdict
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count
from django.utils import timezone

from .models import (
    Destination, Category, DestinationCandidate, DiscoveryJob,
    DestinationSourceField, DestinationAuditLog, User
)
from .discovery_pipeline import (
    DestinationDiscoveryPipeline,
    publish_candidate_to_destination,
    merge_candidate_as_alias
)
from .permissions import IsAdminOrStaff


class CandidatePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200


class DiscoveryHealthReportView(APIView):
    """
    GET /api/v1/admin/discovery/health-report/
    Generates full database health and deduplication audit report.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]

    def get(self, request):
        total_rows = Destination.objects.count()
        missing_coords = Destination.objects.filter(Q(latitude__isnull=True) | Q(longitude__isnull=True)).count()
        missing_muni = Destination.objects.filter(municipality__exact="").count()
        missing_dist = Destination.objects.filter(district__exact="").count()
        no_desc = Destination.objects.filter(description__exact="").count()

        # Potential duplicate groups in existing Destination table
        name_counts = defaultdict(list)
        for d in Destination.objects.values("id", "name", "district"):
            norm = d["name"].strip().lower()
            name_counts[norm].append(d)

        dup_groups = {k: v for k, v in name_counts.items() if len(v) > 1}
        dup_records_count = sum(len(v) for v in dup_groups.values())

        # Candidates staging stats
        total_candidates = DestinationCandidate.objects.count()
        cand_verified = DestinationCandidate.objects.filter(discovery_status="verified").count()
        cand_duplicates = DestinationCandidate.objects.exclude(duplicate_status="none").count()
        cand_needs_review = DestinationCandidate.objects.filter(discovery_status="needs_review").count()
        cand_published = DestinationCandidate.objects.filter(discovery_status="published").count()
        cand_rejected = DestinationCandidate.objects.filter(discovery_status="rejected").count()

        return Response({
            "database_health": {
                "current_destinations": total_rows,
                "potential_duplicate_groups": len(dup_groups),
                "records_affected_by_duplicates": dup_records_count,
                "missing_coordinates": missing_coords,
                "missing_municipality": missing_muni,
                "missing_district": missing_dist,
                "missing_description": no_desc,
                "estimated_unique_baseline": total_rows - (dup_records_count - len(dup_groups)),
            },
            "discovery_staging": {
                "total_candidates": total_candidates,
                "verified": cand_verified,
                "duplicates_caught": cand_duplicates,
                "needs_review": cand_needs_review,
                "published": cand_published,
                "rejected": cand_rejected,
            }
        })


class DiscoveryStatsView(APIView):
    """
    GET /api/v1/admin/discovery/stats/
    Quick summary statistics for the Admin Discovery Dashboard.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]

    def get(self, request):
        qs = DestinationCandidate.objects.all()
        return Response({
            "total_destinations": Destination.objects.count(),
            "total_candidates": qs.count(),
            "verified": qs.filter(discovery_status="verified").count(),
            "duplicates_caught": qs.exclude(duplicate_status="none").count(),
            "needs_review": qs.filter(discovery_status="needs_review").count(),
            "published": qs.filter(discovery_status="published").count(),
            "rejected": qs.filter(discovery_status="rejected").count(),
            "active_jobs": DiscoveryJob.objects.filter(status="running").count(),
        })


class DestinationCandidateListView(APIView):
    """
    GET /api/v1/admin/discovery/candidates/
    Filterable & paginated candidate list with rich search, status, and duplicate filters.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]

    def get(self, request):
        qs = DestinationCandidate.objects.all()

        search = request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(normalized_name__icontains=search) | Q(district__icontains=search))

        status_filter = request.query_params.get("status", "").strip()
        if status_filter:
            qs = qs.filter(discovery_status=status_filter)

        duplicate_filter = request.query_params.get("duplicate_status", "").strip()
        if duplicate_filter:
            qs = qs.filter(duplicate_status=duplicate_filter)

        district_filter = request.query_params.get("district", "").strip()
        if district_filter:
            qs = qs.filter(district__icontains=district_filter)

        province_filter = request.query_params.get("province", "").strip()
        if province_filter:
            qs = qs.filter(province__icontains=province_filter)

        min_quality = request.query_params.get("min_quality")
        if min_quality:
            try:
                qs = qs.filter(quality_score__gte=float(min_quality))
            except ValueError:
                pass

        paginator = CandidatePagination()
        page = paginator.paginate_queryset(qs, request)

        results = []
        for c in page:
            matched_info = None
            if c.matched_destination:
                matched_info = {
                    "id": c.matched_destination.id,
                    "name": c.matched_destination.name,
                    "district": c.matched_destination.district,
                    "province": c.matched_destination.province,
                }

            results.append({
                "id": c.id,
                "name": c.name,
                "normalized_name": c.normalized_name,
                "alternate_names": c.alternate_names,
                "latitude": float(c.latitude) if c.latitude else None,
                "longitude": float(c.longitude) if c.longitude else None,
                "altitude": c.altitude,
                "province": c.province,
                "district": c.district,
                "municipality": c.municipality,
                "place_type": c.place_type,
                "category_name": c.category.name if c.category else c.suggested_category_name,
                "source": c.source,
                "source_url": c.source_url,
                "source_id": c.source_id,
                "confidence_score": c.confidence_score,
                "quality_score": c.quality_score,
                "discovery_status": c.discovery_status,
                "duplicate_status": c.duplicate_status,
                "duplicate_reason": c.duplicate_reason,
                "match_score": c.match_score,
                "matched_destination": matched_info,
                "evidence_data": c.evidence_data,
                "created_at": c.created_at,
            })

        return paginator.get_paginated_response(results)


class RunDiscoveryJobView(APIView):
    """
    POST /api/v1/admin/discovery/run-batch/
    Trigger discovery & deduplication batch job.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]

    def post(self, request):
        limit = int(request.data.get("limit", 2500))
        target_province = request.data.get("province", "").strip()
        target_district = request.data.get("district", "").strip()

        pipeline = DestinationDiscoveryPipeline()
        summary = pipeline.run_discovery_from_datasets(
            target_province=target_province,
            target_district=target_district,
            limit=limit,
        )

        return Response({
            "message": "Discovery batch job completed successfully",
            "summary": summary,
        }, status=status.HTTP_200_OK)


class CandidateActionView(APIView):
    """
    POST /api/v1/admin/discovery/candidates/<id>/action/
    Perform single candidate action (publish, merge_alias, reject, recheck).
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]

    def post(self, request, pk):
        try:
            candidate = DestinationCandidate.objects.get(id=pk)
        except DestinationCandidate.DoesNotExist:
            return Response({"detail": "Candidate not found"}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get("action", "").lower().strip()

        if action == "publish":
            success, msg = publish_candidate_to_destination(candidate.id, user=request.user)
            if success:
                return Response({"message": msg, "status": "published"})
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

        elif action == "merge_alias":
            target_id = request.data.get("target_destination_id") or (candidate.matched_destination.id if candidate.matched_destination else None)
            if not target_id:
                return Response({"detail": "Target destination ID is required to merge as alias"}, status=status.HTTP_400_BAD_REQUEST)
            success, msg = merge_candidate_as_alias(candidate.id, target_id, user=request.user)
            if success:
                return Response({"message": msg, "status": "merged_duplicate"})
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

        elif action == "reject":
            candidate.discovery_status = DestinationCandidate.DiscoveryStatus.REJECTED
            candidate.audit_trail.append({
                "timestamp": timezone.now().isoformat(),
                "action": "rejected",
                "performed_by": request.user.email,
                "reason": request.data.get("reason", "Rejected during admin moderation"),
            })
            candidate.save()
            return Response({"message": f"Candidate '{candidate.name}' marked as rejected", "status": "rejected"})

        return Response({"detail": f"Unknown action: '{action}'"}, status=status.HTTP_400_BAD_REQUEST)


class DiscoveryBulkActionView(APIView):
    """
    POST /api/v1/admin/discovery/bulk-action/
    Bulk publish verified, bulk merge aliases, or bulk reject selected candidates.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaff]

    def post(self, request):
        candidate_ids = request.data.get("candidate_ids", [])
        action = request.data.get("action", "").lower().strip()

        if not candidate_ids:
            return Response({"detail": "No candidate IDs provided"}, status=status.HTTP_400_BAD_REQUEST)

        processed = 0
        errors = []

        for cid in candidate_ids:
            try:
                if action == "publish":
                    success, msg = publish_candidate_to_destination(cid, user=request.user)
                    if success:
                        processed += 1
                    else:
                        errors.append(f"#{cid}: {msg}")
                elif action == "reject":
                    cand = DestinationCandidate.objects.get(id=cid)
                    cand.discovery_status = DestinationCandidate.DiscoveryStatus.REJECTED
                    cand.save()
                    processed += 1
                elif action == "merge_alias":
                    cand = DestinationCandidate.objects.get(id=cid)
                    if cand.matched_destination:
                        success, msg = merge_candidate_as_alias(cid, cand.matched_destination.id, user=request.user)
                        if success:
                            processed += 1
                        else:
                            errors.append(f"#{cid}: {msg}")
            except Exception as e:
                errors.append(f"#{cid}: {str(e)}")

        return Response({
            "message": f"Bulk action '{action}' executed",
            "processed": processed,
            "errors": errors,
        })
