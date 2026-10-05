"""Temporary profiling harness for OpenAPI schema generation."""
import os
import time
import warnings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from django.urls import get_resolver  # noqa: E402
from drf_spectacular.generators import SchemaGenerator  # noqa: E402


def count_endpoints(resolver, prefix=""):
    n = 0
    for p in resolver.url_patterns:
        if hasattr(p, "url_patterns"):
            n += count_endpoints(p, prefix)
        else:
            n += 1
    return n


t0 = time.perf_counter()
total = count_endpoints(get_resolver())
t1 = time.perf_counter()
print(f"total url patterns: {total}  (resolve walk {t1 - t0:.2f}s)")

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    gen = SchemaGenerator()
    t2 = time.perf_counter()
    schema = gen.get_schema(request=None, public=True)
    t3 = time.perf_counter()
    print(f"schema generation: {t3 - t2:.2f}s")
    print(f"paths in schema: {len(schema.get('paths', {}))}")

    # Re-run warm to see if it is per-process cost or repeated cost.
    gen2 = SchemaGenerator()
    t4 = time.perf_counter()
    schema2 = gen2.get_schema(request=None, public=True)
    t5 = time.perf_counter()
    print(f"second generation (same process): {t5 - t4:.2f}s")

    import json

    print(f"schema json size: {len(json.dumps(schema)) / 1024:.0f} KiB")

    seen = {}
    for warn in w:
        key = str(warn.message)[:160]
        seen[key] = seen.get(key, 0) + 1
    print(f"\ndistinct warnings: {len(seen)}")
    for key, count in sorted(seen.items(), key=lambda kv: -kv[1]):
        print(f"  x{count}: {key}")
