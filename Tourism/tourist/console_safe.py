"""Console-safe output for management commands.

Nepal Yatra holds place names in Devanagari as well as Latin script. On a
Windows console the default codec is cp1252, so printing a name like
"भगवानी" raises UnicodeEncodeError and kills the command -- usually at the
exact moment it is trying to report a real problem, which is the worst
possible time to lose the output.

The audit commands reconfigure the streams once at the start of ``handle()``
so a finding is always reported, whatever the host terminal.
"""
from __future__ import annotations

import sys


def make_console_utf8() -> bool:
    """Best-effort switch stdout/stderr to UTF-8 with replacement.

    Returns True when the streams were reconfigured. On CI (UTF-8) this is a
    no-op; on a legacy Windows console it prevents a crash mid-report.
    """
    changed = False
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
            changed = True
        except (ValueError, OSError, AttributeError):
            continue
    return changed


def safe_text(value, limit: int = 80) -> str:
    """Render any value as printable text that the host console can encode."""
    text = str(value)
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
    except (UnicodeEncodeError, LookupError):
        text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    return text[:limit]
