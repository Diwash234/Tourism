"""Extract hardcoded UI strings from frontend pages and report dict coverage.

Usage:
    python scripts/extract_ui_strings.py                 # report only
    python scripts/extract_ui_strings.py --add-missing   # append missing EN keys to index.js
    python scripts/extract_ui_strings.py --translate     # machine-translate missing ne/hi via backend engine

Keys are namespaced by page: <pagename>.<slugified-text>.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = ROOT / "frontend" / "Tourism" / "src" / "pages"
COMPONENTS_DIR = ROOT / "frontend" / "Tourism" / "src" / "components"
I18N_PATH = ROOT / "frontend" / "Tourism" / "src" / "i18n" / "index.js"

# JSX text nodes and common string props we translate.
TEXT_RE = re.compile(r">([^<>{}]+)<")
PROP_RE = re.compile(r'(?:placeholder|title|alt|aria-label|label)\s*=\s*"([^"]+)"')
# Skip: URLs, paths, CSS, single chars, code-like tokens.
SKIP_RE = re.compile(r"^(https?://|/|#|[.\d\s\-_,;:!?()]+$)")
# Fragments of JSX/JS expressions caught by the text-node regex.
CODE_RE = re.compile(r"(&&|\|\||===|!==|=>|\(\s*\)|\)\s*[:?]|:.*\?|return|const |let |function)")
MIN_LEN = 3


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:48].strip("_")


def extract_strings(path):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()
    found = set()
    for match in TEXT_RE.finditer(text):
        s = match.group(1).strip()
        s = re.sub(r"\s+", " ", s)
        if len(s) >= MIN_LEN and not SKIP_RE.match(s) and not CODE_RE.search(s):
            # Skip strings with JSX interpolation braces.
            if "{" in s or "}" in s:
                continue
            found.add(s)
    for match in PROP_RE.finditer(text):
        s = match.group(1).strip()
        if len(s) >= MIN_LEN and not SKIP_RE.match(s):
            found.add(s)
    return found


def dict_values(lang):
    text = I18N_PATH.read_text(encoding="utf-8")
    start = text.find(f"const {lang} = {{")
    if start < 0:
        return {}
    depth = 0
    end = start
    in_str = None
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in ("'", '"'):
            in_str = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    block = text[start:end + 1]
    entries = {}
    for m in re.finditer(r'"([^"]+)"\s*:\s*"((?:[^"\\]|\\.)*)"', block):
        entries[m.group(1)] = m.group(2)
    return entries


def main():
    en = dict_values("en")
    en_values = set(en.values())
    all_missing = {}  # page -> [(key, text)]

    targets = []
    for base in (PAGES_DIR, COMPONENTS_DIR):
        if base.exists():
            targets += sorted(base.rglob("*.jsx"))

    for path in targets:
        if "test" in path.name.lower() or "spec" in path.name.lower():
            continue
        strings = extract_strings(path)
        missing = sorted(s for s in strings if s not in en_values)
        if missing:
            rel = path.relative_to(ROOT / "frontend" / "Tourism" / "src")
            page = path.stem.lower()
            all_missing[str(rel)] = [(f"{page}.{slugify(s)}", s) for s in missing]

    total = sum(len(v) for v in all_missing.values())
    print(f"Files with uncovered strings: {len(all_missing)}")
    print(f"Total uncovered strings: {total}")
    for rel, pairs in sorted(all_missing.items()):
        print(f"\n{rel} ({len(pairs)}):")
        for key, text in pairs[:15]:
            print(f"  {key} = {text[:80]}")
        if len(pairs) > 15:
            print(f"  ... and {len(pairs) - 15} more")

    if "--add-missing" in sys.argv:
        lines = []
        for rel, pairs in sorted(all_missing.items()):
            for key, text in pairs:
                safe = text.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'  "{key}": "{safe}",')
        print(f"\n--- {len(lines)} keys to append to `en` dict ---")
        Path("missing_keys.txt").write_text("\n".join(lines), encoding="utf-8")
        print("Wrote missing_keys.txt")


if __name__ == "__main__":
    main()
