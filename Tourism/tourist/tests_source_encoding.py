"""Guard against the encoding corruption that silently broke province lookup.

What happened
-------------
Three files were re-encoded as Windows-1252 and written back as UTF-8, gaining a
BOM and turning every non-ASCII character into mojibake. Most of the damage was
cosmetic, but not all of it: ``views_navigation.py`` held the Devanagari
province names in a lookup table, and the corrupted keys silently stopped
matching. ``canon_province`` then returned the raw Devanagari string instead of
"Bagmati Province", and the API published it to travellers. No test failed at
the moment of corruption -- the test that noticed had been passing all along
and only went red because the data it relied on was destroyed underneath it.

Why a test for this
-------------------
A corrupted dictionary key fails open: the code keeps running and simply stops
doing its job. Nothing raises. The only reliable detector is reading the bytes
back and noticing they are not what was written, so this checks the repository
itself.

The check is on the *bytes*, not the rendered glyph, because the corruption is
only visible as a byte pattern. It runs without touching the database.
"""
from __future__ import annotations

import unittest
from pathlib import Path

from django.conf import settings

BOM = b"\xef\xbb\xbf"

# Sequences that only appear when UTF-8 bytes were decoded as cp1252/latin-1
# and written back out. "â€”" is a mis-decoded em dash, "Ã©" a mis-decoded "é",
# and so on. Their presence in source means the file was double-encoded.
MOJIBAKE_MARKERS = (
    b"\xc3\xa2\xe2\x82\xac",   # â€  (mis-decoded em/en dash, quotes, bullet)
    b"\xc3\xa2\xe2\x80\xa0",   # â€  (mis-decoded arrow, dagger)
    b"\xc3\x83",               # Ã   (mis-decoded accented Latin)
    b"\xc3\x82\xc2",           # Â   (mis-decoded non-breaking space)
    b"\xc3\xaf\xc2\xbb\xc2\xbf",  # ï»¿ (a BOM that got double-encoded)
)


def source_roots() -> list[Path]:
    base = Path(settings.BASE_DIR)
    roots = [base / "tourist"]
    frontend = base.parent / "frontend"
    if frontend.exists():
        roots.append(frontend)
    return [r for r in roots if r.exists()]


def candidate_files() -> list[Path]:
    found: list[Path] = []
    for root in source_roots():
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css"}:
                continue
            if "node_modules" in path.parts or "migrations" in path.parts or "dist" in path.parts or "build" in path.parts or ".vite" in path.parts:
                continue
            if "__pycache__" in path.parts:
                continue
            # This file necessarily contains the very byte patterns it hunts
            # for, so it would otherwise always report itself.
            if path.name == Path(__file__).name:
                continue
            found.append(path)
    return found


class SourceEncodingTests(unittest.TestCase):
    """The repository must be plain UTF-8 without a BOM."""

    def test_no_source_file_has_a_utf8_bom(self):
        offenders = []
        for path in candidate_files():
            try:
                with open(path, "rb") as fh:
                    if fh.read(3) == BOM:
                        offenders.append(str(path))
            except OSError:
                continue
        self.assertEqual(
            offenders, [],
            "these files start with a UTF-8 BOM; re-save them as UTF-8 without BOM:\n  "
            + "\n  ".join(offenders),
        )

    def test_no_source_file_contains_mojibake(self):
        offenders = []
        for path in candidate_files():
            try:
                data = path.read_bytes()
            except OSError:
                continue
            for marker in MOJIBAKE_MARKERS:
                if marker in data:
                    offenders.append(f"{path} contains {marker!r}")
                    break
        self.assertEqual(
            offenders, [],
            "these files look double-encoded (UTF-8 bytes read as cp1251/cp1252 and "
            "written back as UTF-8). Devanagari dictionary keys and user-facing "
            "strings are affected:\n  " + "\n  ".join(offenders),
        )

    def test_province_lookup_keys_are_real_devanagari(self):
        """The specific corruption that reached production.

        ``canon_province`` is supposed to map "बागमती प्रदेश" to
        "Bagmati Province". When the table was double-encoded the keys stopped
        matching and the function fell through, returning the Devanagari string
        unchanged -- so the API served the untranslated value. Assert on the
        real characters, not on a rendered glyph.
        """
        import tourist.views_navigation as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        self.assertIn(
            "बागमती प्रदेश",
            source,
            "views_navigation.py no longer contains the correctly encoded Devanagari "
            "province name; province normalisation will silently stop working.",
        )
        self.assertNotIn(
            "à¤¬à¤¾à¤—à¤®à¤¤à¥€",
            source,
            "views_navigation.py contains mis-decoded Devanagari province keys.",
        )
