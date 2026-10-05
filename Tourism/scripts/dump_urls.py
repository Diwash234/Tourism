"""Dump every resolved URL pattern from the Django project.

Run with:  python scripts/dump_urls.py > urls.txt
The frontend dead-end audit compares its axios calls against this list, so the
output has to come from the resolver itself rather than from grepping urls.py.
"""
import os
import re
import sys
import json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402
django.setup()

from django.urls import get_resolver  # noqa: E402
from django.urls.resolvers import URLPattern, URLResolver  # noqa: E402


def walk(resolver, prefix=""):
    out = []
    for p in resolver.url_patterns:
        if isinstance(p, URLResolver):
            sub = walk(p, prefix + str(p.pattern))
            if sub:
                out.extend(sub)
            else:
                out.append(prefix + str(p.pattern))
        elif isinstance(p, URLPattern):
            out.append(prefix + str(p.pattern))
    return out


def main():
    resolver = get_resolver()
    routes = []
    for r in walk(resolver):
        # Django path() converters and re_path() groups both become wildcards,
        # but the regex group syntax has to stay valid Python/JS regex.
        norm = re.sub(r"\(\?P<[^>]*>", "(?:", r)
        while "<" in norm:
            i = norm.index("<")
            j = norm.index(">", i)
            norm = norm[:i] + "[^/]+" + norm[j + 1:]
        norm = norm.lstrip("/").rstrip("/")
        routes.append(norm)

    # regex-based routes cannot be matched statically; keep them flagged
    wild = re.compile(r"\[\^/[^]]*\]\+")
    static = sorted({r for r in routes if not wild.search(r)})
    dynamic = sorted({r for r in routes if wild.search(r)})
    print(json.dumps({"static": static, "dynamic": dynamic}, indent=1))


if __name__ == "__main__":
    main()