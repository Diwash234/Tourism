#!/usr/bin/env python3
"""
Local self-diagnostic for the Digital Nepal Tourism Platform.

Run it FROM THE REPO ROOT (the folder containing `Tourism/` and
`frontend/`):

    python scripts/local_check.py

It checks, in order:
  1. Database file exists and actually contains data
  2. Python dependencies import cleanly (prints the exact missing module)
  3. Django starts (runs `manage.py check` in a subprocess)
  4. Backend API is reachable (starts `runserver` on port 8000 itself if
     nothing is listening, so you only need this one script)
  5. Every core feature, including remote districts:
       - destination list / detail / map points / search
       - nearby places + nearby POIs (hospitals/banks) for
         Humla, Jumla, Darchula, Mugu, Taplejung, Kathmandu
       - navigation routes (remote town -> Kathmandu)
       - itineraries for remote start cities
  6. Frontend dev server reachable + its /api proxy works

Every failure prints ONE actionable line. Exit code 0 = all green.
Only the Python standard library is used.
"""
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ROOT, "Tourism")
API = "http://127.0.0.1:8000/api/v1/"
FRONTEND = "http://127.0.0.1:5173/"

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"
failures = []


def ok(label, detail=""):
    print(f"  [{PASS}] {label}" + (f" — {detail}" if detail else ""))


def bad(label, fix):
    print(f"  [{FAIL}] {label}")
    print(f"           FIX: {fix}")
    failures.append(label)


def warn(label, note):
    print(f"  [{WARN}] {label} — {note}")


def port_open(port, host="127.0.0.1"):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def http_json(url, timeout=90):
    t0 = time.time()
    with urllib.request.urlopen(url, timeout=timeout) as r:
        data = json.loads(r.read())
    return data, time.time() - t0


def http_post_json(url, payload, timeout=120):
    t0 = time.time()
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    return data, time.time() - t0


def main():
    print("=" * 72)
    print(" Digital Nepal Tourism Platform — local self-check")
    print(f" repo root: {ROOT}")
    print("=" * 72)

    # ------------------------------------------------------------------ 1
    print("\n[1/6] Database")
    db = os.path.join(BACKEND, "db.sqlite3")
    if not os.path.exists(db) or os.path.getsize(db) < 1_000_000:
        bad(
            "db.sqlite3 missing or empty",
            "restore it with:  git checkout -- Tourism/db.sqlite3   "
            "(it is committed in this repo). Never delete it.",
        )
        sys.exit(1)
    try:
        c = sqlite3.connect(db)
        n_dest = c.execute("SELECT COUNT(*) FROM tourist_destination").fetchone()[0]
        n_hot = c.execute("SELECT COUNT(*) FROM tourist_hotel").fetchone()[0]
        c.close()
        if n_dest < 100:
            bad(
                f"db.sqlite3 has only {n_dest} destinations",
                "the data file is a blank migration. Restore the committed "
                "one:  git checkout -- Tourism/db.sqlite3",
            )
            sys.exit(1)
        ok(f"db.sqlite3", f"{n_dest} destinations, {n_hot} hotels")
    except sqlite3.DatabaseError as e:
        bad("db.sqlite3 unreadable", f"{e} — restore with git checkout -- Tourism/db.sqlite3")
        sys.exit(1)

    # ------------------------------------------------------------------ 2
    print("\n[2/6] Python dependencies")
    venv_python = os.path.join(ROOT, ".venv", "bin", "python")
    if os.name == "nt":
        venv_python = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
    py = venv_python if os.path.exists(venv_python) else sys.executable
    try:
        probe = subprocess.run(
            [py, "-c",
             "import django, rest_framework, django_filters, decouple, "
             "corsheaders, whitenoise, requests, pandas, PIL, networkx; "
             "print(django.get_version())"],
            capture_output=True, text=True, timeout=60, cwd=BACKEND,
        )
        if probe.returncode == 0:
            ok("core imports", f"django {probe.stdout.strip()} via {os.path.relpath(py, ROOT)}")
        else:
            missing = [l for l in probe.stderr.splitlines() if "No module named" in l]
            mod = missing[0].split("'")[1] if missing else "unknown module"
            bad(
                f"python dependency missing: {mod}",
                "cd to the repo root, then:  python3 -m venv .venv && "
                "source .venv/bin/activate && pip install -r Tourism/requirements.txt "
                "(Windows: use .venv\\Scripts\\activate)",
            )
            sys.exit(1)
    except (OSError, subprocess.TimeoutExpired) as e:
        bad("could not probe python", str(e))
        sys.exit(1)
    manage = os.path.join(BACKEND, "manage.py")
    manage_cmd = [py, manage]

    # ------------------------------------------------------------------ 3
    print("\n[3/6] Django system check")
    chk = subprocess.run(manage_cmd + ["check"], capture_output=True, text=True,
                         timeout=120, cwd=BACKEND)
    if chk.returncode == 0:
        ok("manage.py check", "no issues")
    else:
        tail = "\n           ".join((chk.stderr or chk.stdout).strip().splitlines()[-3:])
        bad("manage.py check failed", "see the traceback above and fix the import it names "
            "(99% of cases: pip install -r Tourism/requirements.txt in the venv)")
        print(f"           {tail}")
        sys.exit(1)

    # ------------------------------------------------------------------ 4
    print("\n[4/6] Backend server (port 8000)")
    server_proc = None
    if port_open(8000):
        ok("port 8000 already listening", "using the server you started")
    else:
        print("  …nothing on port 8000 — starting one for this check…")
        log = open(os.path.join(ROOT, "scripts", "local_check_server.log"), "wb")
        server_proc = subprocess.Popen(
            manage_cmd + ["runserver", "127.0.0.1:8000", "--noreload"],
            cwd=BACKEND, stdout=log, stderr=subprocess.STDOUT,
        )
        for _ in range(40):
            if port_open(8000):
                break
            time.sleep(0.5)
        if not port_open(8000):
            bad(
                "runserver did not come up in 20 s",
                "run it manually to see the error:  cd Tourism && python manage.py runserver 0.0.0.0:8000",
            )
            sys.exit(1)
        ok("runserver started", "(this script will stop it when done)")

    try:
        # ------------------------------------------------------------ 5
        print("\n[5/6] Features — core data + remote coordinates")
        try:
            d, dt = http_json(API + "destinations/?page_size=1")
            ok("destination list API", f"{d['count']} public destinations [{dt:.1f}s]")
            if d["count"] < 100:
                bad("destination list nearly empty",
                    "restore the committed DB (git checkout -- Tourism/db.sqlite3) — "
                    "a fresh `migrate` alone creates EMPTY tables")
        except Exception as e:
            bad("destination list API", f"{e} — is Django running? cd Tourism && python manage.py runserver 0.0.0.0:8000")

        for u, label in [
            ("destinations/map-points/", "map points (all 6,600+ places)"),
            ("districts/", "all-77-districts API"),
            ("hotels/?page_size=1", "hotels API"),
            ("places/search/?q=pokhara&page_size=3", "search API"),
        ]:
            try:
                d, dt = http_json(API + u)
                n = d.get("count") if isinstance(d, dict) else len(d)
                ok(label, f"{n} [{dt:.1f}s]")
            except Exception as e:
                bad(label, str(e))

        # remote coordinate matrix
        spots = [
            ("Khaudta (Humla)", 29.25, 80.20),
            ("Jumla", 29.28, 82.18),
            ("Darchula", 29.33, 80.98),
            ("Garcha (Mugu)", 28.78, 81.96),
            ("Taplejung", 27.57, 87.86),
            ("Kathmandu", 27.717, 85.324),
        ]
        print("\n  remote coordinate matrix (nearby destinations + hospitals/banks):")
        for label, lat, lon in spots:
            try:
                d, _ = http_json(API + f"places/nearby/?lat={lat}&lon={lon}&radius_km=25")
                n = len(d.get("results") or d.get("destinations") or [])
                # POIs via any real destination near the spot:
                s, _ = http_json(API + f"places/search/?q={label.split()[0]}&page_size=1")
                res = s.get("results") or []
                poi_line = "poi=n/a"
                if res and res[0].get("slug"):
                    p, _ = http_json(API + f"destinations/{res[0]['slug']}/nearby-pois/?categories=hospitals,banks&radius_km=5")
                    cats = p.get("categories") or {}
                    poi_line = " | ".join(
                        f"{k}={len((cats.get(k) or {}).get('results') or [])}"
                        for k in ("hospitals", "banks")
                    )
                ok(f"{label} ({lat},{lon})", f"nearby={n} {poi_line}")
            except Exception as e:
                bad(f"{label} ({lat},{lon})", str(e))

        print("\n  navigation routes -> Kathmandu (27.717, 85.324):")
        for label, lat, lon in [
            ("Jumla -> KTM", 29.28, 82.18),
            ("Darchula -> KTM", 29.33, 80.98),
            ("Humla -> KTM", 29.25, 80.20),
            ("Ilam -> KTM", 26.91, 87.94),
        ]:
            try:
                d, dt = http_post_json(
                    API + "navigation/route",
                    {"start_latitude": lat, "start_longitude": lon,
                     "end_latitude": 27.717, "end_longitude": 85.324},
                )
                ok(f"{label}", f"{d.get('distance_km')} km via {str(d.get('source'))[:24]} [{dt:.1f}s]")
            except Exception as e:
                bad(f"{label}", str(e))

        print("\n  itineraries for remote start cities:")
        for city in ["Humla", "Jumla", "Darchula", "Taplejung"]:
            try:
                d, dt = http_post_json(API + "ml/itinerary/", {"days": 3, "start_city": city})
                stops = sum(len(day.get("destinations") or []) for day in (d.get("itinerary") or []))
                ok(f"itinerary start={city}", f"{stops} recorded stops [{dt:.1f}s]")
                if stops == 0:
                    bad(f"itinerary {city} empty",
                        "DB data missing? git checkout -- Tourism/db.sqlite3")
            except Exception as e:
                bad(f"itinerary start={city}", str(e))

        # ------------------------------------------------------------ 6
        print("\n[6/6] Frontend (port 5173, npm run dev)")
        if port_open(5173):
            try:
                with urllib.request.urlopen(FRONTEND, timeout=15) as r:
                    ok("frontend page", f"HTTP {r.status}")
                d, dt = http_json(FRONTEND + "api/v1/destinations/?page_size=1", timeout=30)
                ok("frontend -> /api proxy", f"{d['count']} destinations [{dt:.2f}s]")
            except Exception as e:
                bad("frontend reachable but /api proxy failed",
                    f"{e} — your Vite proxy targets 127.0.0.1:8000; make sure Django is up there")
        else:
            warn("frontend not running",
                 "start it:  cd frontend/Tourism && npm install && npm run dev   "
                 "(the backend on port 8000 is enough for the API tests above)")
    finally:
        if server_proc:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()
            print("\n  (stopped the temporary runserver this check started)")

    print("\n" + "=" * 72)
    if failures:
        print(f" RESULT: {len(failures)} problem(s) — see FIX lines above.")
        sys.exit(1)
    print(" RESULT: all green. If the browser still shows empty pages,")
    print("         hard-refresh (Ctrl/Cmd+Shift+R) and check the browser")
    print("         console — any remaining 'connection refused' means the")
    print("         Django process on port 8000 was stopped again.")
    print("=" * 72)


if __name__ == "__main__":
    main()
