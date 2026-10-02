import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

names = sys.argv[1:]
for path in ("tourist/tests.py", "tourist/tests_regression.py", "tourist/tests_admin_control_center.py"):
    try:
        src = io.open(path, encoding="utf-8", errors="replace").read().splitlines(keepends=True)
    except FileNotFoundError:
        continue
    for target in names:
        hits = [i for i, l in enumerate(src) if f"def {target}(" in l]
        for hit in hits:
            cls = next((i for i in range(hit, -1, -1) if re.match(r"^class \w+", src[i])), None)
            indent = len(src[hit]) - len(src[hit].lstrip())
            end = hit + 1
            while end < len(src):
                line = src[end]
                if line.strip() and (len(line) - len(line.lstrip())) <= indent \
                        and re.match(r"\s*(def |class )", line):
                    break
                end += 1
            print(f"##### {path}:{hit + 1}  "
                  f"{(re.match(chr(94) + 'class (\\w+)', src[cls]).group(1) if cls else '?')}")
            sys.stdout.write("".join(src[hit:end]))
            print()