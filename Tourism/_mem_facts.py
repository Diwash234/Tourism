"""Temporary: measure the real memory cost of the fact table."""
import logging
import os
import sys
import tracemalloc

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

logging.disable(logging.CRITICAL)

from tourist import traveller_facts as tf  # noqa: E402


def rss_mb():
    try:
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    except Exception:
        pass
    # Fallback: read /proc/self/status on Linux, otherwise unknown.
    try:
        with open("/proc/self/status") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except Exception:
        pass
    return float("nan")


print(f"RSS before                : {rss_mb():8.1f} MiB")

tracemalloc.start()
base = tracemalloc.get_traced_memory()[0]

rows = tf._build_rows()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"rows built                : {len(rows)}")
print(f"tracemalloc current       : {(current - base) / 1024 / 1024:8.1f} MiB")
print(f"tracemalloc peak          : {peak / 1024 / 1024:8.1f} MiB")
print(f"RSS after                 : {rss_mb():8.1f} MiB")
print()
print(f"bytes per row (current)   : {(current - base) / max(len(rows), 1):8.0f}")

# Where does it go? Count keys and nested structures.
nested = 0
for r in rows:
    nested += sum(
        1 for v in r.values() if isinstance(v, dict)
    )
print(f"nested dicts across table : {nested}  (each is a separate allocation)")
print(f"keys per row              : {len(rows[0])}")
print()
print("sample row:")
for k, v in rows[0].items():
    print(f"   {k:18s} {str(v)[:70]}")
