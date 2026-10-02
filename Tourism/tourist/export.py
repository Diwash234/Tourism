"""
Data export utilities — CSV, JSON, and Excel export for API responses.
"""
import csv
import io
import json
import logging
from typing import Any, Iterable, Optional

from django.http import HttpResponse
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def export_csv(queryset, filename: str, fields: Optional[list] = None) -> HttpResponse:
    """Export a queryset as a CSV file."""
    if not queryset:
        return HttpResponse("No data to export", content_type="text/plain")

    # Determine fields from the first object if not specified
    first = queryset[0]
    if fields is None:
        if hasattr(first, "to_dict"):
            fields = list(first.to_dict().keys())
        elif hasattr(first, "__dict__"):
            fields = [k for k in first.__dict__ if not k.startswith("_")]
        else:
            fields = ["id"]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()

    for obj in queryset:
        if hasattr(obj, "to_dict"):
            row = obj.to_dict()
        elif hasattr(first, "__dict__"):
            row = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        else:
            row = {"id": obj.id}
        # Only include specified fields
        writer.writerow({k: row.get(k, "") for k in fields})

    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
    return response


def export_json(queryset, filename: str, fields: Optional[list] = None) -> HttpResponse:
    """Export a queryset as a JSON file."""
    data = []
    for obj in queryset:
        if hasattr(obj, "to_dict"):
            data.append(obj.to_dict())
        elif hasattr(obj, "__dict__"):
            data.append({k: v for k, v in obj.__dict__.items() if not k.startswith("_")})
        else:
            data.append({"id": obj.id})

    response = HttpResponse(
        json.dumps(data, indent=2, default=str),
        content_type="application/json",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}.json"'
    return response


def export_excel(queryset, filename: str, fields: Optional[list] = None) -> HttpResponse:
    """Export a queryset as an Excel file (requires openpyxl)."""
    try:
        from openpyxl import Workbook
    except ImportError:
        return HttpResponse("openpyxl is required for Excel export", content_type="text/plain")

    wb = Workbook()
    ws = wb.active
    ws.title = "Data"

    if not queryset:
        ws.append(["No data"])
    else:
        first = queryset[0]
        if fields is None:
            if hasattr(first, "to_dict"):
                fields = list(first.to_dict().keys())
            elif hasattr(first, "__dict__"):
                fields = [k for k in first.__dict__ if not k.startswith("_")]
            else:
                fields = ["id"]

        ws.append(fields)
        for obj in queryset:
            if hasattr(obj, "to_dict"):
                row = obj.to_dict()
            elif hasattr(first, "__dict__"):
                row = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
            else:
                row = {"id": obj.id}
            ws.append([row.get(k, "") for k in fields])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
    return response
