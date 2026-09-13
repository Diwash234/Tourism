"""Provenance & audit helpers for admin edits (spec §6/§8/§25).

Every admin correction through the CMS:
  * records an AdminFieldOverride (so future imports never clobber it), and
  * writes a field-level audit entry with WHO / WHAT / BEFORE / AFTER.
"""
from audit.logging_services import log_action

from .models import AdminFieldOverride


def record_admin_edit(request, obj, changes, source_view="admin_editor", reason=""):
    """changes: {field_name: (before_value, after_value)} — only actually-changed fields.

    Safe to call with an empty dict (no-op). Never raises: provenance must
    not break the edit itself.
    """
    if not changes:
        return
    label = obj._meta.label_lower  # e.g. "tourist.destination"
    for field, (before, after) in changes.items():
        try:
            AdminFieldOverride.objects.update_or_create(
                model_label=label, object_id=obj.pk, field=field,
                defaults={
                    "value": "" if after is None else str(after),
                    "overridden_by": request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
                    "reason": reason[:255],
                },
            )
        except Exception:  # pragma: no cover - provenance must never break edits
            pass
    try:
        log_action(
            request, f"{source_view}_edit", category="data_edits", severity="info",
            message=f"Edited {label} #{obj.pk}: " + ", ".join(
                f"{f} {b!r} -> {a!r}" for f, (b, a) in changes.items()
            )[:2000],
            obj=obj, object_type=obj.__class__.__name__, object_id=obj.pk,
            user=getattr(request, "user", None),
            extra={"changes": {f: {"before": str(b), "after": str(a)} for f, (b, a) in changes.items()}},
        )
    except Exception:  # pragma: no cover
        pass


def overrides_for(obj):
    """{field: AdminFieldOverride} for one record — used by importers."""
    return {
        o.field: o
        for o in AdminFieldOverride.objects.filter(
            model_label=obj._meta.label_lower, object_id=obj.pk
        )
    }
