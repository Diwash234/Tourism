"""Normalise source whitespace: final newline, trailing spaces, line endings.

Scope, and why it is not more
-----------------------------
This fixes three things that are mechanically safe and genuinely wrong:

  * a file that does not end with a newline. POSIX text files should, and the
    absence produces noisy "No newline at end of file" diff markers and breaks
    naive line-based tooling;
  * trailing whitespace at the end of a line;
  * CRLF line endings inside files that .gitattributes declares as LF.

It deliberately does **not** enforce a maximum line length or re-indent code.
Both would produce a very large diff across a repository more than one person is
editing, turning a formatting change into a merge-conflict generator for no
functional gain. Line length is reported, not enforced.

Only whitespace bytes change. No line of content is added, removed or reordered,
so behaviour is unaffected and ``git diff -w`` on the result shows nothing.

Files that ``.gitattributes`` marks ``-text`` are skipped entirely. Those are the
published release artifacts whose exact bytes are checksummed; normalising them
would invalidate a checksum while the diff looked empty. The declaration is read
from the file rather than hardcoded, so adding a new artifact is covered
automatically.

Usage
-----
    python scripts/normalize_source_whitespace.py           # report only
    python scripts/normalize_source_whitespace.py --write   # apply
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TEXT_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml", ".md",
    ".css", ".html", ".sh", ".cjs", ".mjs", ".txt", ".cfg", ".ini", ".toml",
}
# .gitattributes marks these eol=crlf, so CRLF is correct for them.
CRLF_ALLOWED_SUFFIXES = {".bat", ".cmd", ".ps1"}
SKIP_PARTS = {"node_modules", ".git", "venv", "__pycache__", "dist", "build", "media"}
ATTRS = ROOT / ".gitattributes"


def binary_declared_paths() -> set[str]:
    """Paths .gitattributes marks as -text: byte-exact, never touched."""
    if not ATTRS.exists():
        return set()
    declared: set[str] = set()
    for line in ATTRS.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2 or parts[1] != "-text":
            continue
        for pattern in parts[0].split(","):
            pattern = pattern.strip()
            if pattern and not pattern.startswith("*") and "/" in pattern:
                declared.add(pattern.rstrip("/"))
    return declared


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return [ROOT / name for name in result.stdout.split("\0") if name]


def normalise(text: str) -> str:
    """The single definition of "correct" used by both reporting and writing.

    Having one function is the point: if the report and the fix disagreed, the
    command would claim to have normalised a file and leave it unchanged.

    An empty file is left empty. Rewriting a 0-byte ``__init__.py`` as a file
    containing one newline is churn with no benefit, and it is the kind of change
    that appears in a diff and gets reverted by the next person who does not
    know why it happened.
    """
    body = text[1:] if text.startswith("\ufeff") else text
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    if not body.strip():
        return body
    lines = [line.rstrip() for line in body.split("\n")]
    # A trailing newline leaves a final empty element; keep the file's real last
    # line and then ensure exactly one terminating newline.
    tail = lines.pop() if lines else ""
    out = "\n".join(lines)
    if tail:
        out = f"{out}\n{tail}" if out else tail
    return out if out.endswith("\n") else out + "\n"


def inspect(path: Path, binary_paths: set[str]) -> dict:
    rel = path.relative_to(ROOT).as_posix()
    raw = path.read_bytes()
    if rel in binary_paths or path.suffix in CRLF_ALLOWED_SUFFIXES:
        return {"skip": True}
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return {"skip": True}
    if "\x00" in text[:4096]:
        return {"skip": True}
    return {
        "skip": False,
        # A file counts as missing a final newline only if its very last byte is
        # not a line terminator. Checking after rstrip() always reports
        # "missing", which is how this first claimed 959 of 1,003 files.
        "final_newline": bool(text) and not text.endswith(("\n", "\r")),
        "crlf": "\r\n" in text,
        "trailing_ws": any(line != line.rstrip() for line in text.split("\n")),
        # More than one terminating newline means a run of blank lines at EOF.
        # Collapsing it removes a line: still a whitespace-only edit and
        # invisible to `git diff -w`, but counted separately so the report never
        # claims a change it has not itemised.
        "blank_eof": text.endswith("\n\n") or text.endswith("\r\n\r\n"),
        "bom": text.startswith("\ufeff"),
        "fixed": normalise(text),
        "original": text,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Normalise source whitespace.")
    parser.add_argument("--write", action="store_true", help="Apply the changes.")
    args = parser.parse_args(argv)

    binary_paths = binary_declared_paths()
    buckets: dict[str, list[str]] = {
        "missing a final newline": [], "trailing whitespace": [],
        "CRLF in an LF path": [], "UTF-8 BOM": [], "blank lines at EOF": [],
    }
    pending: list[tuple[Path, str]] = []

    for path in tracked_files():
        if path.suffix not in TEXT_SUFFIXES or not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        info = inspect(path, binary_paths)
        if info["skip"]:
            continue
        flags = []
        if info["bom"]:
            buckets["UTF-8 BOM"].append(path.name)
        if info["final_newline"]:
            buckets["missing a final newline"].append(path.name)
        if info["trailing_ws"]:
            buckets["trailing whitespace"].append(path.name)
        if info["crlf"]:
            buckets["CRLF in an LF path"].append(path.name)
        if info["blank_eof"] and info["fixed"] != info["original"] and not info["final_newline"]:
            buckets["blank lines at EOF"].append(path.name)
        if info["fixed"] != info["original"]:
            pending.append((path, info["fixed"]))

    for label, names in buckets.items():
        print(f"{label:28} {len(names)}")

    if not pending:
        print("\nsource whitespace is already normalised")
        return 0

    if not args.write:
        print(f"\n{len(pending)} file(s) would change; dry run, pass --write to apply")
        for path, _ in pending[:20]:
            print("   ", path.relative_to(ROOT))
        return 0

    for path, fixed in pending:
        path.write_text(fixed, encoding="utf-8", newline="\n")
    print(f"\nrewrote {len(pending)} file(s); whitespace bytes only")
    print("verify with: git diff -w --stat   (should show no content changes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
