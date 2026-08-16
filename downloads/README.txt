================================================================
 Nepal Tourism — Downloads
================================================================

QUICK START AFTER GIT PULL
--------------------------
The source code, the 20 real AI photos, the management commands,
and the seed SQLite database are ALL committed to git. After a
fresh `git pull origin arena/019ff5f0-tourism` you already have
everything you need. Just run:

    ./run.sh

The downloads/ folder is git-ignored (it contains convenience zips
and uncompressed copies only). This README explains what's in it.


Contents of this folder
-----------------------

1. nepal-tourism-full-project.zip (32 MB)
   Full source snapshot excluding .venv/, node_modules/, dist/,
   __pycache__, .git, and the sqlite DB (the DB is delivered as a
   separate gz so you can drop it in fresh). Contains everything
   needed to run the project on your machine. After unzipping:
     python3 -m venv .venv
     pip install -r Tourism/requirements.txt  (or see run.sh)
     cd frontend/Tourism && npm install
     cd ../.. && ./run.sh

2. nepal-tourism-database.sqlite3 (28 MB) / .gz (3.6 MB)
   Seed database with:
     - 6,414 real destinations across Nepal
     - 46,079 image rows (Unsplash + Wikimedia + AI generated)
     - 1,552 hotels
     - 19 of 20 headline destinations have a local AI-generated
       cover photo attached as a real file in media/ (the 20th,
       Gosaikunda, didn't match an attraction record so it falls
       back to Unsplash -- the hotel at Gosaikunda still gets the
       AI photo)
     - Full audit + system_health tables
     - QA Tester role ready
   To use: copy nepal-tourism-database.sqlite3 to
     Tourism/Tourism/db.sqlite3
   Then run migrations once (they're already applied but it's safe):
     python manage.py migrate

3. nepal-images-only.zip (5.5 MB)
   Just the 20 real AI-generated Nepal destination photos (one per
   destination), useful if you want to swap in your own photos or
   use them elsewhere without pulling the whole repo.


What you actually get in git (you don't need the zips)
------------------------------------------------------
After `git pull` you have:
  frontend/Tourism/public/images/destinations/<place>/*.jpg
     -> 20 real AI photos, 180-350KB each (no color blocks)
  Tourism/tourist/management/commands/attach_local_photos.py
     -> management command that attached the AI photos to destinations
  Tourism/tourist/management/commands/download_ai_images.py
     -> management command to download more AI images (needs internet)
  Tourism/tourist/management/commands/assign_destination_photos.py
     -> assigns diverse curated Unsplash photos to every destination
  frontend/Tourism/src/components/ui/
     -> LightRays, CrazyButton, FlowingMenu, CircularGallery,
        PasswordStrengthField (all animated ReactBits-style)
  Tourism/Tourism/db.sqlite3 (28 MB)
     -> the seeded database (46k images / 6.4k destinations / 1.5k hotels)


Why "1 lakh+" photos isn't here anymore
---------------------------------------
The previous 123,164-image / 379 MB DB from earlier sessions was a
sandbox-local file that was git-ignored. It was wiped when the
sandbox reset between sessions and was never pushed to GitHub
(GitHub rejects files over 100 MB anyway). The new DB has 46k
image rows (mostly curated Unsplash URLs), which is still very rich
and each destination has ~6-13 diverse photos in its gallery.

To get MORE photos (the AI image downloader generates real binaries):
    cd Tourism
    python manage.py download_ai_images --all --num 8   # needs internet
That will generate and save real JPEGs into Tourism/media/ for every
destination.

If you want to re-run the offline safe diversification on a fresh DB:
    python manage.py import_osm_destinations
    python manage.py assign_destination_photos --stale-only
    python manage.py attach_local_photos

Those three commands populate everything without needing internet
(they use the CSV seed data and bundled Unsplash photo URLs).


Fixes in this push
------------------
- Fixed missing FiLock import in Register.jsx ("fillot is not defined")
- Fixed isUsable() bug that was rejecting the new AI photos
- Deleted the old 8KB red/blue/purple img1..img5.jpg color blocks
- Added 10 NEW AI photos (Ilam, Janakpur, Bandipur, Bardiya, Dolpo,
  Gosaikunda, Koshi-Tappu, Manaslu, Rara, Tilicho) for a total of 20
- Expanded LOCAL_NEPAL_PHOTOS map with proper aliases
- Attached all 20 AI photos as real ImageField files to their
  matching destination records (not just frontend fallbacks)
- Cleared stale cover_image URL fields so the AI photos show up as
  covers for the headline destinations
- Added audit + system_health backend apps and admin diagnostics
- QA Tester role + QA demo button on login
- Password strength meter with crack-time watermark + checklist
- Warm Nepal earth-tone palette (no purple/blue)
- CircularGallery on destination details page
- Global ErrorBoundary + frontend error beacon
