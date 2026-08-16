==========================================================================
  Nepal Tourism Platform — Offline Snapshot
==========================================================================

After `git pull` (or extracting this zip), run `./run.sh` from the repo
root. It creates a Python virtualenv in `.venv/`, installs pip packages,
runs migrations, installs npm packages, and starts:
  - Django API   : http://0.0.0.0:8000
  - Vite/React   : http://0.0.0.0:5173
Both are bound to 0.0.0.0 so any device on your LAN can reach them.

--------------------------------------------------------------------------
DEFAULT ADMIN LOGIN
--------------------------------------------------------------------------
  Email     : admin123@gmail.com
  Password  : admin123
If you ever reset the DB you can re-create it with:
  cd Tourism && python manage.py shell -c "
  from django.contrib.auth import get_user_model; User=get_user_model()
  User.objects.create_superuser(email='admin123@gmail.com',
    password='admin123', first_name='Site', last_name='Admin',
    role='SUPER_ADMIN')"

--------------------------------------------------------------------------
CONTENTS
--------------------------------------------------------------------------
1. nepal-tourism-full-project.zip   — snapshot of the full source
2. nepal-images-only.zip            — /images/ public assets (30 AI JPEGs
                                      for headline places + 14 category SVGs)
3. nepal-tourism-database.sqlite3   — pre-seeded SQLite DB (shipped as
                                      Tourism/db.sqlite3 by the repo too)
4. nepal-tourism-database.sqlite3.gz— compressed DB for slower links

--------------------------------------------------------------------------
WHAT IS IN THE DB (as of this snapshot)
--------------------------------------------------------------------------
  • 7,052 destinations across Nepal
  • 42,312 total image rows (cover + 6 gallery per destination)
  • 36-category taxonomy (mountains / hills / valleys / trekking /
    temples / buddhist-sites / heritage / lakes / rivers / waterfalls /
    forests / wildlife / bird-watching / caves / viewpoints / villages /
    culture / festivals / spiritual-wellness / adventure / air-sports /
    water-sports / agriculture / tea-coffee / camping / cycling /
    winter / hot-springs / cities / shopping / food-culinary /
    scenic-routes / eco-tourism / museums / natural-wonders / pilgrimage)
  • 250+ hand-curated LANDMARK photos mapped by name (no more generic
    mountain-on-temple / beach-on-rafting mismatches):
    - All major Durbar Squares (Kathmandu / Bhaktapur / Patan)
    - Pashupatinath / Boudhanath / Swayambhunath / Janaki Mandir /
      Muktinath / Manakamana / Dakshinkali / Guhyeshwari /
      Bindhyabasini / Pathibhara / Changunarayan / Doleshwor /
      Kalinchowk / Halesi Mahadev / Bhaleshwor
    - Phewa / Begnas / Rara / Tilicho / Phoksundo / Gosaikunda /
      Gokyo / Panch Pokhari / Rani Pokhari / Indra Sarovar
    - Davis / Rupse / Pachaljharana / Hyatung / Sundarijal /
      Jhor / Tindhare waterfalls
    - Mahendra / Gupteshwor / Chamere (Bat) / Siddha / Halesi caves
    - Everest / Annapurna / Manaslu / Dhaulagiri / Makalu /
      Kanchenjunga / Machhapuchhre peaks
    - EBC / ABC / Annapurna Circuit / Langtang / Manaslu /
      Upper Mustang / Rara / Mardi Himal / Khopra treks
    - Chitwan / Bardiya / Khaptad / Sagarmatha / Shey Phoksundo /
      Langtang / Shivapuri / Makalu Barun / Koshi Tappu parks
    - Sarangkot / Nagarkot / Chandragiri / Phulchowki / Shree Antu /
      Daman / Kakani / Kala Patthar / Gokyo Ri / Poon Hill viewpoints
    - Manakamana / Chandragiri cable cars
    - Trishuli / Bhote Koshi / Sun Koshi / Karnali rafting;
      Sarangkot paragliding / ultralight; Kushma bungee
    - Kanyam / Ilam tea gardens
    - Ghandruk / Ghale Gaun / Bandipur / Marpha / Kagbeni / Jomsom /
      Dhampus / Chitlang / Panauti / Bungamati / Khokana / Kirtipur /
      Dhulikhel / Tansen / Barpak villages
    - Indra Jatra / Bisket / Rato Machhindranath / Mani Rimdu /
      Tiji / Dashain / Tihar / Holi / Gai Jatra / Ghode Jatra festivals
    - Lumbini / Maya Devi / Kopan / Tengboche / Thrangu Tashi Yangtse /
      Thame / Braga / Rinchenling / Shey monasteries & stupas
  • Hotels/lodges separated behind a type filter (default list shows
    REAL attractions, not thousands of hotels).
  • Category chips on the Destinations page for every taxonomy group.
  • Mood-based AI recommendations: /api/v1/destinations/mood-recommendations
    ?mood=happy|relaxed|chill|adventure|romantic|family|spiritual|cultural
    |wildlife|trekking|hiking|scenic|photography|excited|solitude|sad|
    energetic|winter|snow|pilgrimage|lakeside&days=N
  • Autocomplete search: /api/v1/destinations/autocomplete/?q=...

--------------------------------------------------------------------------
IMAGE SOURCING & ACCURACY
--------------------------------------------------------------------------
  - 30 bundled AI JPEGs for the top 30 headline destinations (Everest,
    Phewa, Chitwan, Lumbini, Bhaktapur, Patan, Kathmandu Durbar,
    Annapurna, Upper Mustang, Ilam, Janakpur, Bandipur, Bardiya, Dolpo,
    Gosaikunda, Koshi Tappu, Manaslu, Rara, Tilicho, Pashupatinath,
    Boudhanath, Swayambhunath, Dharahara, Mahendra Cave, Davis Falls,
    Langtang, Muktinath, Manakamana).
  - All other covers come from large, category-pure Unsplash photo
    pools (30-40 photos per category) with STRICT whole-word keyword
    matching so we no longer get beach photos on rafting or wetlands
    on rivers.
  - The /admin interface (Django) lets you:
      * Browse every destination with its cover thumbnail & image count
      * Approve / reject / mark-verified any image in bulk
      * Reassign covers for selected destinations (action menu)
      * Upload/replace individual destination images
      * Create new staff/admin/super-admin users via the Users page
  - The React Admin Dashboard (`/admin-dashboard`) exposes the same
    image-moderation queue and a staff-user creation form.
  - Default cover/gallery photos are committed in APPROVED state. New
    user-uploaded images can be required to go through the pending
    queue by toggling the setting in the admin.

--------------------------------------------------------------------------
COLORS / THEME
--------------------------------------------------------------------------
  Deep mountain green : #1f6b4d
  Warm terracotta     : #c2603a
  Himalayan gold      : #b8862f
  Warm off-white      : #faf8f4
  (No purple / blue theme anywhere — only the Nepal palette.)

--------------------------------------------------------------------------
LAN ACCESS
--------------------------------------------------------------------------
Both servers bind 0.0.0.0. ALLOWED_HOSTS = ['*'],
CORS_ALLOW_ALL_ORIGINS = True. Point any phone/laptop on the same WiFi
at http://<your-lan-ip>:5173 and it will work.
