"""Locate the test class for a named Django test and print it.

Usage:  python _find.py test_bulk_publish_uses_publication_gate
        python _find.py --file tourist/tests_regression.py test_weather_returns_503_without_api_key
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

target = sys.argv[1]
path = None
if sys.argv[1] == "--file":
    path = sys.argv[2]
    target = sys.argv[3]
else:
    import glob
    for guess in glob.glob("tourist/tests*.py"):
        src = io.open(guess, encoding="utf-8", errors="replace").read()
        if f"def {target}(" in src:
            path = guess
            break

if path is None:
    print("NOT FOUND")
    sys.exit(1)

src = io.open(path, encoding="utf-8", errors="replace").read().splitlines(keepends=True)
hit = next(i for i, l in enumerate(src) if re.match(rf"\s*def {target}\(", l))

# Walk back to the enclosing class.
cls = next(
    (i for i in range(hit, -1, -1) if re.match(r"^class \w+", src[i])),
    None,
)
print(f"{path}  class@{cls + 1}  test@{hit + 1}")
if cls is not None:
    print(re.match(r"^class (\w+)", src[cls]).group(1))

# Print the body up to the next same-or-less-indented def.
indent = len(src[hit]) - len(src[hit].lstrip())
end = hit + 1
while end < len(src):
    line = src[end]
    if line.strip() and (len(line) - len(line.lstrip())) <= indent \
            and re.match(r"\s*(def |class )", line):
        break
    end += 1
print("-" * 60)
sys.stdout.write("".join(src[hit:end]))