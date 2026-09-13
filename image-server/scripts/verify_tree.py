# Image server — sanity checker for the dataset tree.
#
#   python verify_tree.py            # summarize layout + count files
#   python verify_tree.py --no-write # also print files that WOULD be committed
#
# Use it to confirm:
#   1. the images/ tree has the expected country/place layout;
#   2. nothing under image-server/images/ is tracked by Git (dataset stays out).
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "images"))

SUPPORTED = {".webp", ".jpg", ".jpeg", ".png", ".gif", ".avif"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true",
                    help="also print files under images/ that Git would track")
    args = ap.parse_args()

    if not os.path.isdir(ROOT):
        sys.exit(f"Image root missing: {ROOT}")

    counts = {}
    total = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT)
        n = 0
        for fn in filenames:
            if fn == ".gitkeep":
                continue
            if os.path.splitext(fn)[1].lower() in SUPPORTED:
                n += 1
        if n:
            counts[rel] = n
            total += n

    print(f"Image root : {ROOT}")
    print(f"Supported image files found : {total}")
    if not counts:
        print("(no images yet — place the dataset here)")
    for rel, n in sorted(counts.items()):
        print(f"  {n:6d}  {rel}/")

    # Git check: list what git would track under image-server/images/
    out = subprocess.run(
        ["git", "ls-files", "image-server/images/"],
        cwd=os.path.join(HERE, "..", ".."),
        capture_output=True, text=True,
    ).stdout.strip()
    tracked = [l for l in out.splitlines() if l and not l.endswith(".gitkeep")]
    if tracked:
        print(f"\nWARNING: {len(tracked)} image files are tracked by Git!")
        if args.no_write:
            for t in tracked[:20]:
                print("  ", t)
        sys.exit(1)
    print("\nOK: no image files are tracked by Git (dataset stays out of the repo).")


if __name__ == "__main__":
    main()
