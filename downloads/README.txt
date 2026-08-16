NEPAL TOURISM PLATFORM — DOWNLOADS
====================================

Files in this folder:
---------------------
1. nepal-tourism-database.sqlite3     (~42 MB)  — Full SQLite database with 7,247 destinations, 43,482 images
2. nepal-tourism-database.sqlite3.gz  (~4.7 MB) — Compressed version of the DB
3. nepal-tourism-full-project.zip     (~14 MB)  — Backend + Frontend source code snapshot
4. nepal-images-only.zip              (~22 MB)  — Just the curated Nepal destination images
5. README.txt                         — This file


DEFAULT ADMIN CREDENTIALS
-------------------------
  Email:    admin123@gmail.com
  Password: admin123
  Role:     SUPER_ADMIN

After starting the site (./run.sh), log in at:
  - Django Admin:   http://localhost:8000/admin
  - Admin Dashboard: http://localhost:5173/admin-dashboard


IMAGE SYSTEM — WHAT CHANGED
---------------------------
The photo system has been completely redesigned to fix the "same generic
Unsplash photo everywhere" problem:

1. CURATED AI LANDMARK PHOTOS (40+ Nepal landmarks):
   Pashupatinath, Boudhanath, Swayambhunath, Swayambhu, Dharahara,
   Kathmandu Durbar Square, Bhaktapur, Patan/Lalitpur, Phewa Lake/Pokhara,
   Davis Falls, Mahendra Cave, World Peace Pagoda,
   Everest Base Camp/Sagarmatha, Annapurna Base Camp, Langtang Valley,
   Upper Mustang/Lo Manthang, Muktinath, Manakamana, Gosaikunda,
   Chitwan NP, Bardiya NP, Koshi Tappu, Rara Lake, Tilicho Lake, Phoksundo,
   Manaslu, Dolpo, Ilam Tea Gardens, Janakpur/Janaki Mandir, Bandipur,
   Nagarkot sunrise, Lumbini, plus new additions for Pathibhara, Rani Mahal,
   Gorkha Durbar, Kanchenjunga, Dhaulagiri, Chandragiri, Ghandruk,
   Sarangkot, Dhulikhel, Bhote Koshi, Kanyam Tea Garden, Khaptad NP.

2. DETERMINISTIC UNIQUE SVG POSTCARDS for every other destination (7,200+):
   Every non-landmark destination gets a unique Nepal-themed SVG postcard
   generated live by the Django server, keyed by name + category + district.
   These are vector graphics (instant load, no external dependencies), colored
   with the Nepal palette (deep green, terracotta, Himalayan gold) and
   featuring category-appropriate silhouettes (mountains, pagoda roofs, stupa
   eyes, waterfalls, stupas, wildlife, city skylines, prayer flags, etc.).
   NO TWO destinations get the same postcard — the repetition problem is
   mathematically eliminated.

3. ZERO UNSplash GENERIC HOTLINKS in default data:
   All previous ~200 generic Unsplash URLs that repeated across 7,000+
   destinations have been removed. The only external hotlinks are those added
   manually by admins through the image pipeline.

4. GALLERY IMAGE MODERATION QUEUE:
   Gallery (non-cover) images are created with STATUS = PENDING. Admin must
   approve them in the Django admin (/admin/tourist/destinationimage/) or via
   the Admin Dashboard before they appear as approved. This lets staff
   gradually replace the placeholder postcards with real photos of each place.

5. COVERS ARE ALWAYS APPROVED so the site works out of the box.

ADMIN WORKFLOW FOR ADDING REAL IMAGES
--------------------------------------
1. Log in to /admin or /admin-dashboard as admin123@gmail.com.
2. Navigate to Destinations -> pick a place -> Images tab.
3. Use "Discover images" (image acquisition pipeline) or paste real URLs
   (Pexels, Openverse, Wikimedia Commons, official tourism sites, Dojolo, etc.).
4. Mark the correct one as "cover", set others as gallery.
5. Set verification_status = APPROVED for accurate photos, REJECTED for wrong ones.
6. Over time, all 7,247 destinations will accumulate real, accurate photos
   through this moderation pipeline.

CATEGORIES (36 active)
----------------------
mountains, hills, valleys, lakes, rivers, waterfalls, caves, hot-springs,
forests, wildlife, bird-watching, parks-gardens, temples, buddhist-sites,
pilgrimage, spiritual-wellness, heritage, museums, culture, festivals,
cities, shopping, food-culinary, villages, tea-coffee, agriculture,
viewpoints, trekking, adventure, air-sports, water-sports, camping,
cycling, winter, scenic-routes, eco-tourism, cablecar

Each has unique SVG silhouettes for the postcards.


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
