r"""Serve the OpenAPI document from a cache instead of rebuilding it per request.

Why this exists
---------------
``tourist.urls`` is mounted under both ``/api/v1/`` and ``/api/v2/``, so the
project registers ~1580 URL patterns and drf-spectacular emits 852 paths and
1416 operations. Walking every one of those views to rebuild the document costs
**10-40 seconds of pure CPU** on this machine (measured; the document itself is
~2.4 MB of JSON).

That cost used to be paid on *every* request to ``/api/v1/models/``,
``/api/v2/models/``, ``/v1/models/`` and ``/api/schema/``. The previous
mitigation was ``cache_page(60 * 60)``, which does not work here:

* the response is served with ``Vary: Accept``, so each distinct ``Accept``
  header (``application/json`` from curl, ``text/html`` from a browser, the
  SPA's default) is a separate cache entry, and
* ``LocMemCache`` is per-process, so every ``runserver`` autoreload and every
  new gunicorn/daphne worker started from scratch.

Because the work is CPU-bound Python it holds the GIL, so ``runserver``'s
threaded server cannot serve anything else while it runs. That is why an
unrelated ``GET /health`` was reported as ``Slow request ... took 4.90s`` even
though ``/health`` itself answers in under a millisecond, and why clients gave
up mid-response and produced ``Broken pipe`` noise. The slow schema endpoint
was starving the entire site.

What this does instead
----------------------
``CachedSchemaAPIView`` subclasses ``SpectacularAPIView`` and replaces only
``_get_schema_response``:

1. A **fingerprint** is computed from the mtime/size of the Django project and
   installed first-party app ``.py`` files plus the drf-spectacular version and
   schema-affecting settings.
2. The finished document is looked up **in-process** (a module-level dict), then
   **on disk** under ``BASE_DIR/.openapi_cache``, keyed by that fingerprint.
3. Only on a genuine miss is ``SchemaGenerator.get_schema()`` called. Its return
   value is already normalised, sanitised and post-processed by the library, so
   caching the dict is equivalent to caching the rendered response — content
   negotiation (JSON/YAML) still happens per request in DRF's renderer.

Editing any Python file changes the fingerprint, so the document is rebuilt
automatically; nothing goes stale. The expensive rebuild is therefore paid once
per deploy instead of once per request.

Staleness safety
----------------
A fingerprint mismatch always rebuilds, so a stale document can never be served
after a code change. Within a single unchanged tree the document is by
definition correct. Writes are atomic (``write`` to a temp file, then
``replace``) so a crashed or concurrent writer cannot leave a truncated file.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from pathlib import Path

from django.apps import apps
from django.conf import settings
from rest_framework.response import Response

from drf_spectacular.views import SpectacularAPIView

logger = logging.getLogger(__name__)

# Directory names that never affect the shape of the API surface.
_IGNORED_DIR_PARTS = frozenset(
    {
        ".git",
        ".github",
        ".pytest_cache",
        "__pycache__",
        "build",
        "dist",
        "frontend_dist",
        "media",
        "migrations",
        "node_modules",
        "staticfiles",
        "venv",
    }
)

# Only settings that can actually change the generated document.
_FINGERPRINT_SETTINGS = ("ROOT_URLCONF", "SPECTACULAR_SETTINGS", "REST_FRAMEWORK")

_memory_cache: dict[tuple[str, str, bool], dict] = {}

# Serialises generation. Without this the start-up warm-up thread and a request
# arriving at the same moment each run their own SchemaGenerator: the build was
# observed taking 61s instead of ~30s (two concurrent walks of ~1,600 views),
# and peak memory doubled -- which is exactly what a memory-limited instance
# cannot afford. Callers now wait for the single in-flight build instead.
_build_lock = threading.Lock()


def _iter_source_files(base: Path):
    """Yield project and installed-app Python files that can affect the API."""
    roots = {base / settings.SETTINGS_MODULE.split(".", 1)[0]}
    for app_config in apps.get_app_configs():
        app_path = Path(app_config.path)
        try:
            app_path.relative_to(base)
        except ValueError:
            continue
        roots.add(app_path)

    seen = set()
    for root in sorted(roots):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            try:
                relative_parts = path.relative_to(base).parts
            except ValueError:  # pragma: no cover - defensive
                continue
            if _IGNORED_DIR_PARTS.intersection(relative_parts) or path in seen:
                continue
            seen.add(path)
            yield path

    # Include standalone project modules, such as manage.py, without walking
    # unrelated repository directories.
    for path in sorted(base.glob("*.py")):
        if path not in seen:
            yield path


def _source_fingerprint() -> str:
    """Hash schema-relevant project sources plus schema-affecting settings.

    Uses ``mtime_ns`` + size rather than file contents: it is accurate enough to
    invalidate on any edit while costing only a ``stat()`` per file, instead of
    reading and hashing several megabytes on every single request.
    """
    digest = hashlib.sha256()
    base = Path(settings.BASE_DIR)

    for path in sorted(_iter_source_files(base)):
        try:
            stat = path.stat()
        except OSError:
            continue
        digest.update(str(path.relative_to(base)).encode("utf-8"))
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
        digest.update(str(stat.st_size).encode("ascii"))

    for setting_name in _FINGERPRINT_SETTINGS:
        digest.update(setting_name.encode("ascii"))
        digest.update(
            json.dumps(
                getattr(settings, setting_name, {}), sort_keys=True, default=str
            ).encode("utf-8")
        )

    try:
        import drf_spectacular

        digest.update(str(drf_spectacular.__version__).encode("ascii"))
    except Exception:  # pragma: no cover - defensive
        pass

    return digest.hexdigest()


def _cache_dir() -> Path:
    return Path(settings.BASE_DIR) / ".openapi_cache"


def _cache_path(fingerprint: str, version: str) -> Path:
    suffix = version or "default"
    # ``version`` comes from the query string, so keep it filesystem-safe.
    safe_suffix = "".join(c if c.isalnum() or c in "-_." else "_" for c in suffix)[:64]
    return _cache_dir() / f"schema-{fingerprint}-{safe_suffix}.json"


def _prune_stale_entries(keep: Path) -> None:
    """Keep only the newest few cached documents so the directory cannot grow."""
    try:
        entries = sorted(
            _cache_dir().glob("schema-*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )
    except OSError:
        return
    for stale in entries[4:]:
        try:
            stale.unlink()
        except OSError:
            pass
    # Remove documents written for fingerprints we have moved past.
    for stale in _cache_dir().glob("*.tmp"):
        try:
            if stale != keep.with_suffix(".tmp"):
                stale.unlink()
        except OSError:
            pass


def _read_disk_cache(path: Path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def _write_disk_cache(path: Path, document: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(document, handle)
        # Atomic swap: a reader never observes a half-written document.
        os.replace(tmp, path)
    except OSError as exc:
        logger.warning("OpenAPI schema cache not written (%s); serving uncached.", exc)


def _build_schema(view: "CachedSchemaAPIView", request, version: str) -> dict | None:
    generator = view.generator_class(
        urlconf=view.urlconf, api_version=version, patterns=view.patterns
    )
    return generator.get_schema(request=request, public=view.serve_public)


def get_cached_schema(view: "CachedSchemaAPIView", request, version: str):
    """Return the cached document, building it only on a genuine miss.

    Shared by the request path and the start-up warm-up so both take exactly the
    same code path -- a warmed cache is indistinguishable from one built during
    a request.
    """
    cache_key = (view.serve_public, version or "")

    document = _memory_cache.get(cache_key)
    if document is not None:
        return document

    # Only one generation at a time. The lock is re-checked inside, so a caller
    # that queued behind an in-flight build returns its result rather than
    # starting a second one.
    with _build_lock:
        document = _memory_cache.get(cache_key)
        if document is not None:
            return document

        fingerprint = _source_fingerprint()
        path = _cache_path(fingerprint, version or "")

        document = _read_disk_cache(path)
        if document is not None:
            logger.info("OpenAPI schema loaded from disk cache (%s).", path.name)
        else:
            logger.info(
                "Rebuilding OpenAPI schema; this happens once per code change, not "
                "once per request."
            )
            document = _build_schema(view, request, version)
            if document is None:
                return None
            _write_disk_cache(path, document)
            _prune_stale_entries(path)

        _memory_cache[cache_key] = document
        return document


def warm_schema_cache() -> bool:
    """Build or load the document ahead of the first request.

    Walking every registered view costs 10-30s of CPU. Without this, the first
    request to /api/v1/models/ after any code change pays that cost, which in
    development looks like "the site is slow" every single time a file is
    saved -- and the client usually gives up first ("Broken pipe").

    Called from ``Tourism.apps``' ready() in a daemon thread, so it overlaps
    start-up instead of blocking it, and any request that does arrive first
    still blocks correctly on the same build.
    """
    view = CachedSchemaAPIView()
    document = get_cached_schema(view, None, "")
    return document is not None


class CachedSchemaAPIView(SpectacularAPIView):
    """``SpectacularAPIView`` that generates the document at most once per tree."""

    # Deliberately replaces the parent's implementation rather than wrapping it,
    # so the expensive ``SchemaGenerator`` call is the only thing that changes.
    def _get_schema_response(self, request):
        version = self.api_version or request.version or self._get_version_parameter(request)

        document = get_cached_schema(self, request, version)
        if document is None:
            return Response(data={"detail": "Schema generation failed."}, status=503)

        return Response(
            data=document,
            headers={
                "Content-Disposition": f'inline; filename="{self._get_filename(request, version)}"',
                # The document only changes when the code changes, so let the
                # browser and any CDN hold on to it instead of re-fetching it.
                "Cache-Control": "public, max-age=300",
            },
        )
