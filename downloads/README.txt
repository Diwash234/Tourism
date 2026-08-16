==========================================================================
  Nepal Tourism Platform — Offline Snapshot
==========================================================================

This folder contains a ready-to-run snapshot of the Nepal Tourism
Django+React project. After `git pull`, run `./run.sh` from the repo
root — it will create a venv, install pip packages, run migrations,
install npm packages, and start Django on :8000 and Vite on :5173.

--------------------------------------------------------------------------
CONTENTS
--------------------------------------------------------------------------

1. nepal-tourism-full-project.zip
   A snapshot of the entire repository (excluding venv, node_modules,
   and build artifacts) for easy offline transfer.

2. nepal-images-only.zip
   Just the curated AI-generated Nepal destination JPEGs, plus the
   image folder structure. Extract this into
   frontend/Tourism/public/images/destinations/ if your clone is
   missing images.

3. nepal-tourism-database.sqlite3 / .gz
   A pre-seeded SQLite database with:
     • 6,437 destinations across Nepal (temples, caves, lakes,
       trekking routes, stupas, national parks, museums, viewpoints,
       Durbar Squares, plus 5,000+ hotels/lodges in a separate filter).
     • 38,000+ curated gallery images (Unsplash-licensed + 20 bundled
       AI-generated Nepal photos for the top 20 destinations).
     • 990 real tourist attractions shown on the default
       "Destinations" page; hotels/lodges are separated under the
       "Hotels & Stays" filter chip.

   To restore: copy the .sqlite3 file to Tourism/db.sqlite3 (overwriting
   the existing one), then `python manage.py migrate`.

--------------------------------------------------------------------------
WHAT WAS FIXED
--------------------------------------------------------------------------
 • Register page "FiLock is not defined" crash → fixed missing import.
 • "All images look the same" → root cause was photo_catalog.py had
   CATEGORY_POOLS defined before the photo-pool lists existed, so the
   attach_local_photos management command crashed on every run with
   NameError and never diversified images. Pools are now defined in the
   correct order and re-assigned.
 • Old solid-colour placeholders (img1.jpg…img5.jpg ~8KB purple/red/
   blue blocks) were deleted. Every destination now gets a category-
   appropriate cover + gallery.
 • 20 headline destinations (Nagarkot, Pokhara/Phewa, Everest Base
   Camp, Kathmandu Durbar Square, Chitwan, Lumbini, Bhaktapur, Patan,
   Annapurna, Upper Mustang, Ilam tea gardens, Janakpur, Bandipur,
   Bardiya, Dolpo, Gosaikunda, Koshi Tappu, Manaslu, Rara, Tilicho)
   have accurate bundled AI photos shipped in
   frontend/Tourism/public/images/destinations/<place>/.
 • 17+ curated real Nepal destinations added (Mahendra Cave Pokhara,
   Davis Falls / Patale Chhango, Gupteshwor Mahadev Cave,
   Bindhyabasini Temple, World Peace Pagoda, Begnas Lake, Rupa Lake,
   Pashupatinath, Boudhanath, Swayambhunath, Dharahara, Garden of
   Dreams, Thamel, Narayanhiti Palace, Chandragiri Cable Car,
   Phulchowki Hill, Langtang Valley, Kyanjin Gompa, Helambu, Panch
   Pokhari, Tengboche Monastery, Namche Bazaar, Kala Patthar, Gokyo
   Lakes, Poon Hill, Machhapuchhre, Thorong La, Muktinath, Kagbeni,
   Sauraha, Khaptad NP, Pathibhara, Kanyam, Shree Antu, Halesi
   Mahadev, Janaki Mandir, Manakamana, Gorkha Durbar, Bandipur
   Bazaar, Tansen Palpa, Rani Mahal, Bhaktapur Durbar Square, Patan
   Durbar Square).
 • Default destination listing now shows REAL attractions (temples,
   caves, lakes, mountains, museums, parks) — NOT thousands of
   hotels. A filter chip bar lets users switch between
   "Attractions / Hotels & Stays / All Places".
 • PageHeader.jsx and LocalApi.js were never empty; they are working
   components with Nepal-themed palette (deep mountain green
   #1f6b4d, terracotta #c2603a, Himalayan gold #b8862f, warm off-white
   #faf8f4).
 • downloads/ folder is committed to git so `git pull` gets it.

--------------------------------------------------------------------------
ADDING MORE AI IMAGES (requires internet)
--------------------------------------------------------------------------
On your own internet-connected machine you can generate additional
AI photos for more destinations:

    python manage.py download_ai_images --all --num 8

This calls Pollinations.ai to generate photos and saves them under
frontend/Tourism/public/images/destinations/<slug>/ — they are served
statically by Vite, so no /media/ configuration needed.
