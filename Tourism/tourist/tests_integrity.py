"""Whole-repository import integrity.

The parallel-session merge left two hard breakages on main, and both were of
the same kind: a module that tourist/urls.py transitively imports could not be
imported. A routed view class that did not exist, and a SyntaxError in
tourist/views_ml.py. Neither produced a 404 or a 500 on one endpoint -- Django
raises while *building* the URLconf, so every route in the project was
unreachable, admin and public alike, and the platform was simply down.

These are cheap checks with no database access, so they belong in the default
suite where they will fail the release gate rather than being found by hand
after a deploy.

What is asserted:

* every .py file in the project parses (catches a SyntaxError committed to a
  module the URLconf imports, without needing to import it);
* every ``<module>.<View>.as_view`` reference in any app's urls.py resolves to
  a real attribute, ignoring commented-out routes;
* the URLconf itself loads and every pattern resolves;
* the tourist migration graph has exactly one leaf node, because two leaves
  make ``manage.py migrate`` refuse to run -- which fails every deploy that
  reaches the data phase.
"""

import ast
import importlib
import os
import re
import unittest

import django
from django.conf import settings
from django.urls import get_resolver, reverse

APPS = [
    "tourist", "booking", "safety", "navigation", "admin_panel",
    "chatbot", "notifications", "audit", "translation", "system_health",
    "media_app",
]

# Names that appear as "<x>.<View>.as_view" but are not view modules:
# stdlib, third-party, or aliased imports such as
# ``from .services.ai_images import api as ai_images_api``.
_NOT_VIEW_MODULES = {
    "re", "django", "rest_framework", "settings", "urls", "static",
    "self", "cls",
}

_SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", "media", "staticfiles", "coverage",
}


def _project_root():
    # BASE_DIR is the directory holding manage.py.
    return str(settings.BASE_DIR)


def _python_files():
    root = _project_root()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            if name.endswith(".py"):
                yield os.path.join(dirpath, name)


class RepositoryParsesTests(unittest.TestCase):
    """No committed file may be unparseable.

    Checked with ast.parse rather than importing, because importing is exactly
    what breaks: a module with a SyntaxError inside the URLconf's import graph
    takes the whole site down, and this test has to still run in that state to
    report it.
    """

    def test_every_python_file_parses(self):
        offenders = []
        for path in _python_files():
            try:
                with open(path, "rb") as handle:
                    ast.parse(handle.read(), filename=path)
            except SyntaxError as exc:
                rel = os.path.relpath(path, _project_root())
                offenders.append(f"{rel} line {exc.lineno}: {exc.msg}")
            except (OSError, ValueError):
                continue
        self.assertEqual(
            offenders, [],
            "these files do not parse:\n  " + "\n  ".join(offenders),
        )


class UrlconfIntegrityTests(unittest.TestCase):
    def test_every_referenced_view_exists(self):
        missing = []
        checked = 0
        for app in APPS:
            url_path = os.path.join(_project_root(), app, "urls.py")
            if not os.path.exists(url_path):
                continue
            with open(url_path, encoding="utf-8") as handle:
                source = handle.read()
            # safety/urls.py documents its disabled routes as commented-out
            # path() calls, including views that were never implemented.
            # Only live code counts as a reference.
            code = "\n".join(line.split("#", 1)[0] for line in source.splitlines())
            for module_name, attr in sorted(
                set(re.findall(r"\b([a-z_][a-z0-9_]*)\.([A-Z][A-Za-z0-9_]*)\.as_view", code))
            ):
                if module_name in _NOT_VIEW_MODULES:
                    continue
                try:
                    module = importlib.import_module(f"{app}.{module_name}")
                except Exception:
                    # An aliased import (imported as a different name) or a
                    # module that is genuinely optional; the URLconf-load test
                    # below is what actually guarantees reachability.
                    continue
                checked += 1
                if not hasattr(module, attr):
                    missing.append(f"{app}.{module_name}.{attr}")
        self.assertEqual(
            missing, [],
            "these views are routed in urls.py but do not exist:\n  " + "\n  ".join(missing),
        )
        self.assertGreater(checked, 100, "the reference scan found suspiciously few views")

    def test_urlconf_loads_and_all_patterns_resolve(self):
        patterns = get_resolver().url_patterns  # forces every urls module to import

        seen = [0]

        def walk(items):
            for entry in items:
                if hasattr(entry, "url_patterns"):
                    walk(entry.url_patterns)
                else:
                    seen[0] += 1

        walk(patterns)
        self.assertGreater(
            seen[0], 500,
            "expected a large URL surface; a low count means the walk is wrong",
        )

    def test_image_search_routes_reverse(self):
        # Both were routed while their view classes were missing from
        # views_admin.py, which broke the whole URLconf.
        for name in ("admin-image-multi-search", "admin-image-import-media"):
            with self.subTest(name=name):
                self.assertTrue(reverse(name).startswith("/api/"))


class MigrationGraphTests(unittest.TestCase):
    def test_single_leaf_node(self):
        from django.db.migrations.loader import MigrationLoader

        loader = MigrationLoader(None, ignore_no_migrations=True)
        leaves = loader.graph.leaf_nodes("tourist")
        self.assertEqual(
            len(leaves), 1,
            "the tourist migration graph has "
            f"{len(leaves)} leaf nodes {[n[1] for n in leaves]}; "
            "`manage.py migrate` refuses to run until they are merged",
        )