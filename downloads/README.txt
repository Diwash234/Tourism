NEPAL TOURISM PLATFORM — DOWNLOADS
====================================

Files in this folder (kept intentionally small so the repo stays easy to clone):
------------------------------------------------------------------------------
1. nepal-tourism-database.sqlite3.gz  (~4.4 MB) — Compressed full SQLite DB snapshot
2. README.txt                         — This file

Why only the compressed snapshot?
---------------------------------
The full database is already committed at `Tourism/Tourism/db.sqlite3` (~45 MB).
Keeping an *uncompressed copy* here as well made the GitHub repo >100 MB and
slow to clone, so the duplicate copy and the stale zip bundles were removed.

Regenerate anything you need from the committed DB:

  # uncompressed copy (same file as Tourism/db.sqlite3)
  cp ../Tourism/db.sqlite3 nepal-tourism-database.sqlite3

  # compressed snapshot
  gzip -9 -k -f ../Tourism/db.sqlite3 -c > nepal-tourism-database.sqlite3.gz

  # full-project zip (backend + frontend source)
  cd .. && zip -r downloads/nepal-tourism-full-project.zip Tourism \
      -x "Tourism/db.sqlite3" "Tourism/.env" "*/node_modules/*" "*/__pycache__/*"

  # images-only zip (curated landmark photo pack, if you need a copy)
  cd frontend/Tourism && zip -r ../../downloads/nepal-images-only.zip public/images

GitHub's hard limit is 100 MB per file; the committed DB (~45 MB) stays well
under it, and future photo rows are just URL metadata (no binaries in SQLite),
so the DB grows only a few KB per thousand photos.


CURRENT SNAPSHOT
----------------
- 7,517 destinations
- 2,925 verified real Wikimedia Commons cover photos (temples, stupas,
  mountains, lakes, rivers, waterfalls, festivals, heritage, tea/coffee,
  adventure, viewpoints …) + 274 curated AI landmark photos
- SVG postcards only for places that have no public photo yet
- Every destination has exactly 1 cover image


DEFAULT ADMIN CREDENTIALS
-------------------------
  Email:    admin123@gmail.com
  Password: admin123
  Role:     SUPER_ADMIN

After starting the site (./run.sh), log in at:
  - Django Admin:   http://localhost:8000/admin
  - Admin Dashboard: http://localhost:5173/admin-dashboard


IMAGE SYSTEM
------------
1. VERIFIED REAL PHOTOS (2,925): every approved cover carries a real
   Wikimedia Commons photo URL (hotlinked from upload.wikimedia.org) with
   photographer + license attribution stored in the DB and served by the API.

2. CURATED AI LANDMARK PHOTOS (274): 40+ famous Nepal landmarks
   (Pashupatinath, Boudhanath, Swayambhunath, Dharahara, Kathmandu Durbar
   Square, Bhaktapur, Patan, Phewa Lake, Davis Falls, World Peace Pagoda,
   Everest Base Camp, Annapurna Base Camp, Langtang Valley, Lo Manthang,
   Muktinath, Manakamana, Gosaikunda, Chitwan NP, Bardiya NP, Rara Lake,
   Tilicho Lake, Phoksundo, Janakpur, Nagarkot, Lumbini, Pathibhara,
   Rani Mahal, Gorkha Durbar, Kanchenjunga, Dhaulagiri, Chandragiri,
   Ghandruk, Sarangkot, Dhulikhel, Khaptad NP …).

3. DETERMINISTIC UNIQUE SVG POSTCARDS: every destination without a public
   photo gets a unique Nepal-themed SVG postcard generated live by Django,
   keyed by name + category + district (vector, instant load, Nepal palette).
   NO TWO destinations get the same postcard.

4. GALLERY IMAGE MODERATION QUEUE: gallery images start PENDING; admins
   approve them at /admin or the Admin Dashboard.

5. COVERS ARE ALWAYS APPROVED so the site works out of the box.

6. STANDALONE IMAGE SERVER: 100k+ photo binaries live outside Git in
   `image-server/images/` (served by a separate static server / CDN) — see
   docs/IMAGE_SERVER.md.


ADMIN WORKFLOW FOR ADDING REAL IMAGES
--------------------------------------
1. Log in to /admin or /admin-dashboard as admin123@gmail.com.
2. Navigate to Destinations -> pick a place -> Images tab.
3. Use "Discover images" or paste real URLs (Wikimedia Commons, Pexels, etc.).
4. Mark the correct one as "cover", set others as gallery.
5. Set verification_status = APPROVED for accurate photos, REJECTED for wrong ones.


STARTING THE SITE
-----------------
cd /path/to/Tourism
chmod +x run.sh
./run.sh

Then visit:
  Frontend (Vite/React):  http://localhost:5173
  Backend API (Django):   http://localhost:8000/api/v1/
  Django Admin:           http://localhost:8000/admin   (admin123 / admin123)

LAN access: both servers bind to 0.0.0.0 so other devices on your network can
reach the site via your LAN IP (e.g. http://192.168.1.XX:5173).
