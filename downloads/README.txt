==========================================================================
  Nepal Tourism Platform — Offline Snapshot
==========================================================================

This folder contains a ready-to-run snapshot of the Nepal Tourism
Django+React project. After `git pull`, run `./run.sh` from the repo
root — it creates a venv, installs pip packages, runs migrations,
installs npm packages, and starts Django on 0.0.0.0:8000 and Vite on
0.0.0.0:5173 (LAN-accessible out of the box).

--------------------------------------------------------------------------
CONTENTS
--------------------------------------------------------------------------

1. nepal-tourism-full-project.zip
   A snapshot of the repository (excluding venv, node_modules, build
   artifacts) for offline transfer.

2. nepal-images-only.zip
   Curated Nepal destination imagery (30 AI JPEGs for headline places
   + 14 SVG category icons). Extract into
   frontend/Tourism/public/images/ if your clone is missing images.

3. nepal-tourism-database.sqlite3 / .gz
   Pre-seeded SQLite database:
     • ~6,810 destinations across Nepal covering a 36-category
       taxonomy (mountains, hills, valleys, trekking, temples,
       buddhist-sites, heritage, lakes, rivers, waterfalls, forests,
       wildlife, bird-watching, caves, viewpoints, villages, culture,
       festivals, spiritual-wellness, adventure, air-sports,
       water-sports, agriculture, tea-coffee, camping, cycling,
       winter, hot-springs, cities, shopping, food-culinary,
       scenic-routes, eco-tourism, museums, natural-wonders,
       pilgrimage).
     • 40,000+ curated image rows (deterministic Unsplash-licensed
       gallery pools per category + 30 bundled AI photos).
     • Default listing shows REAL attractions; hotels/lodges live
       behind the "Hotels & Stays" type chip.
     • Admin image-moderation enabled (approve / reject / mark
       verified per image; reassign covers in bulk).
   To restore: copy the .sqlite3 to Tourism/db.sqlite3 and run
   `python manage.py migrate`.

--------------------------------------------------------------------------
WHAT WAS FIXED / ADDED
--------------------------------------------------------------------------
 • Register page "FiLock is not defined" crash → fixed import.
 • QA Tester checkbox removed from Register & Login pages.
 • photo_catalog.py rewritten: pool ordering fixed (category keywords
   evaluated before generic mountain/lake/heritage so "Annapurna
   Butterfly Museum" gets museum photos, not trekking photos);
   every destination now receives category-accurate covers + 6 gallery
   images (40,860 total rows).
 • Old solid-colour placeholders removed.
 • 30 headline destinations have accurate bundled AI photos in
   frontend/Tourism/public/images/destinations/<place>/.
 • Added: Mahendra Cave, Davis Falls / Patale Chhango, Dharahara,
   Langtang Valley, Rani Mahal, Gorkha Durbar, Pathibhara, Khaptad,
   plus 310 more seeded across all 36 categories.
 • Category filter chips on Destinations page (Lakes, Mountains,
   Temples, Stupas, Caves, Waterfalls, Wildlife, Viewpoints,
   Museums, Tea Gardens, …).
 • A–Z alphabet browsing bar and real-time autocomplete search.
 • Mood-based AI recommendations (happy / relaxed / chill /
   adventure / romantic / family / spiritual / cultural / wildlife
   / trekking / photography / solitude / winter / pilgrimage) with
   number-of-days filter — wired to /api/v1/destinations/mood-recommendations/.
 • Admin Dashboard can create staff/admin/sub-admin users directly
   (role + district assignment) and moderate images.
 • Diagnostics Center page for system-health + error reporting.
 • PageHeader uses Nepal palette (deep mountain green #1f6b4d,
   terracotta #c2603a, Himalayan gold #b8862f, off-white #faf8f4);
   no purple/blue.
 • ReactBits components working: LightRays, CrazyButton, FlowingMenu,
   CircularGallery, PasswordStrengthField.
 • LAN access: Django 0.0.0.0:8000, Vite 0.0.0.0:5173,
   ALLOWED_HOSTS=['*'], CORS_ALLOW_ALL_ORIGINS=True.
 • downloads/ folder is committed to git.

--------------------------------------------------------------------------
ADMIN QUICK START
--------------------------------------------------------------------------
Default superuser (if seeded): admin / admin123
If none exists, create one with:
    python manage.py createsuperuser
Then visit /admin for Django admin or /admin-dashboard for the React
admin panel (image moderation, staff creation, pending queue).

--------------------------------------------------------------------------
ADDING MORE AI IMAGES (requires internet)
--------------------------------------------------------------------------
    python manage.py download_ai_images --all --num 8
Generates photos via Pollinations.ai and saves them under
frontend/Tourism/public/images/destinations/<slug>/.
