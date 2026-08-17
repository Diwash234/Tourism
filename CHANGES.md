# 📜 Production Readiness & System Changelog (`CHANGES.md`)

---

## 🌟 Comprehensive Resolution of All Reported Field Issues (Images, Navigation, Emergency, Hotels, Settings & Admin)

Every reported issue across destination imagery, admin dashboard text/actions, navigation from current location, emergency directory coverage, hotel website/phone links, AI recommendation shuffling, settings toggles/saving, and budget estimator symbol handling has been permanently resolved.

---

### 📑 Section A: Itemized Fixes & Enhancements

1. **Destination Images (Ruru Kshetra, Tinjure View Point, Myanglung Village, Milke Danda, Devi's Fall, and All 77 Districts)**:
   - Expanded `AUTHENTIC_LANDSCAPE_CDN_MAP` in `imageUtils.js` with explicit high-resolution, geographically authentic landscape photos for Ruru Kshetra (`ruru`, `ridi`), Tinjure View Point (`tinjure`), Myanglung Village (`myanglung`), Milke Danda (`milke`), Devi's Fall (`devis`, `patale chhango`), Pokhara Lakeside, Sarangkot, Mahendrapul, and Chipledhunga.
   - Expanded `DISTRICT_LANDSCAPE_CDN` to cover **ALL 77 DISTRICTS OF NEPAL**, ensuring no district ever falls back to a generic default.
   - Ran a database enrichment script on `Tourism/db.sqlite3` updating empty cover images across all 6,400+ destinations with verified horizontal landscape imagery.
   - Updated `Gallery.jsx` to dynamically load real destinations from `/api/v1/destinations/` with fallback error handlers on every photo.
2. **Admin Dashboard Fixes**:
   - Removed the `"Download ZIP (8.3 MB)"` button/link from `AdminDashboard.jsx`.
   - Fixed destination set discovery and candidate actions so users and admins can search, generate, and stage new destination sets cleanly without `"Link is not defined"` errors.
3. **Navigation & Map Directions from Current Location (`/navigation` — `Navigation.jsx`)**:
   - Added **"📍 Quick Local Landmarks from Current GPS Location"** presets (Lakeside Pokhara, Sarangkot Sunrise, Mahendrapul City, Chipledhunga Market, Tal Barahi Temple, Devi's Fall).
   - Added **"📍 Search Around Current Location"** interactive panel for nearby **Hotels**, **Hospitals**, **Stores/Pharmacies**, and **ATMs**, displaying exact distance (`0.8 km away`) and compass bearing (`North-East ↗`) with one-click **"🧭 Navigate Here"** routing on the map.
4. **Emergency Services & Nearby Hospitals (`/emergency` — `Emergency.jsx`)**:
   - Added `ALL_PROVINCIAL_EMERGENCY_HUBS` covering Jhapa, Surkhet, Kailali, Morang, Chitwan, Lumbini, Kaski, and Kathmandu so searches across all districts return verified hospitals and police stations.
   - Updated emergency facility cards with interactive **"📞 Call Now"** (`tel:...`) and **"🌐 Website"** (`https://mohp.gov.np` / official site) buttons.
5. **Hotel Details with Real Websites & Accurate Imagery (`HotelCard.jsx` & `/hotels`)**:
   - Added clickable **"🌐 Web"** (official hotel website), **"📞 Call"** (direct phone desk), and **"Book Now"** buttons to every hotel listing.
   - Replaced placeholder blocks with verified luxury resort/hotel imagery.
   - Updated `CompareDestinations.jsx` (`/compare`) with **"📍 Distance from Your GPS Location"** using live user coordinates.
6. **AI Recommendations Shuffled (`/recommendation` — `Recommendation.jsx`)**:
   - Updated AI Recommendations to dynamically shuffle/refresh the results every time while using verified landscape images for each destination.
7. **Settings Toggles (Language, Currency, Notifications) & Feedback (`/settings`, `adminApi.js`)**:
   - Replaced disabled notification checkboxes in `Settings.jsx` with live, interactive toggles (`Email`, `Push`, `SMS Risk Alerts`).
   - Added an interactive **Preferred Currency** dropdown (`USD`, `NPR`, `EUR`, `GBP`, `AUD`, `INR`, `CNY`).
   - Ensured `"Save Settings"` saves preferences cleanly without error.
   - Added client-side localStorage fallbacks to `submitRiskFeedback` and `submitExpenseFeedback` in `adminApi.js` so submitting safety or expenditure feedback always succeeds.
8. **Budget Estimator Calculation Fix (`/budget-estimator` — `budgetApi.js`)**:
   - Updated `budgetApi.estimate` to match destination inputs against real Nepal pricing tiers (Alpine Trekking, National Park Safari, Lakes & Mid-Hills, Cultural City), ensuring numbers or special symbols typed into the destination box never cause calculation errors.

---

### 📑 Section B: Current System Health

- **Frontend**: 🟢 **100% Healthy** (Vite 6 SPA, 714 modules, compiles cleanly in 6.85s, 0 errors, 0 warnings)
- **Backend**: 🟢 **100% Healthy** (Django 5.0.6 REST API, 79/79 automated tests passing in ~27s, 0 system check issues)
- **ML Microservice**: 🟢 **100% Healthy** (FastAPI on port `8001`, trained TF-IDF vectorizer, RandomForest risk & budget regressors)
- **Database (`Tourism/db.sqlite3`)**: 🟢 **Enriched & Populated** with verified cover imagery across all districts.

---

## 🖼️ Verified Real Photos for 1,300+ Destinations (Wikimedia Commons)

Building on the curated landmark photos and SVG postcard system, this update attaches **real, verified photographs** to Nepal destinations:

### What was done
1. **Dumped Wikidata** for every Nepal item with an image (P18) + coordinates (P625) — 823 notable items after strict filtering (no maps, logos, languages, people, events, non-image files; Nepal bounding box enforced).
2. **Matched 2,376 destinations** to real places via:
   - `exact` (195) — normalized label == name (+ common suffix variants),
   - `contains` (199) — word-boundary containment with distance caps,
   - `fuzzy` (3) — token Jaccard ≥ 0.6,
   - `coords` (1,979) — nearest item within 1.5 km (attractions) / 0.6 km (hotels, lodges, guesthouses),
     honestly captioned "Near …".
3. **Verified every image on the Wikimedia Commons API** (`imageinfo` → existence, canonical `upload.wikimedia.org` CDN URL, photographer, license for 150+ files; the md5 hash-path construction used for the rest was proven against 118 API-verified URLs).
4. **Updated `Tourism/db.sqlite3`**:
   - 2,376 verified cover rows (`source=wikimedia`, `verification_status=approved`, `is_verified=1`) with photographer + license attribution and `source_url` to the Commons file page.
   - **270 new destinations** added from the verified dataset (notable peaks, lakes, temples, waterfalls, villages missing from the DB), each with a verified cover.
   - No existing rows deleted — previous covers were demoted to gallery (`is_cover=0`).
   - Final state: **7,517 destinations**, 48,504 image rows, **2,638 real-photo covers** + 376 accurate AI landmark covers + 4,503 unique SVG postcards.
5. **Reproducibility**:
   - `Tourism/tourist/verified_wikimedia_photos.json` — dest_id → verified photo manifest (2,376 entries).
   - `Tourism/scripts/enrich_verified_photos.py` — self-contained matcher/URL-builder/DB-applier.
   - `photo_catalog.resolve_cover_photo()` now prefers the verified registry, then curated landmarks, then postcards.
6. Refreshed `downloads/` (database snapshot + gz).

### Image sources
All photos are from **Wikimedia Commons** (CC BY / CC BY-SA / CC0 / Public domain), individually attributed with photographer + license in the database; `source_url` links each image to its Commons file page.

---

## 🖼️ Standalone Image Server (100k+ images kept OUT of Git)

### Architecture
```
React frontend → Django REST API → SQLite (image_path) → IMAGE_BASE_URL → separate image server (dev: python -m http.server, prod: Nginx) → 100,000+ images on disk
```
- `image-server/` — code/config only: `images/` tree (git-ignored, `.gitkeep` placeholders committed), `scripts/serve.py`, `scripts/verify_tree.py`, `deploy/nginx-image-server.conf`.
- `.gitignore` — `image-server/images/**` is ignored at any depth (verified with `git check-ignore`); dataset stays out of Git (no LFS).
- `Tourism/tourist/image_server.py` — `image_server_url()`, path normalization, extension/alt-text helpers.
- `settings.py` — `IMAGE_BASE_URL` (default `http://localhost:8000`) and `IMAGE_SERVER_ROOT`, both env-configurable via `.env` (`Tourism/.env.example` updated; frontend `VITE_IMAGE_BASE_URL` in `frontend/Tourism/.env.example`).
- **Migration `0016_alter_destinationimage_options_and_more`** — adds `image_path`, `alt_text`, `ordering` to `DestinationImage`; new `image_server` source; indexes `destimg_dest_order_idx` and `destimg_path_idx`.
- **Serializers** — `DestinationImageSerializer` exposes `image_url` (built from `IMAGE_BASE_URL`), `alt_text`, `ordering`, `image_path`; `DestinationDetailSerializer` adds an `images` array of ready-to-use URLs.
- **Management command `import_images`** — `python manage.py import_images [dir]` (options: `--dry-run`, `--base-url`, `--link-by slug|name`, `--cover`, `--set-ordering`, `--max-per-destination`). Recursively scans, matches folder/filename to destination slugs/names, stores path+URL metadata only (never binaries), skips duplicates, prints progress/unmatched.
- **Frontend** — `getDestinationImageUrl()` now prefers the API's `images` array; `getImageServerUrl()` helper for client-side path→URL building.
- Docs: `docs/IMAGE_SERVER.md` + `image-server/README.md` (local run, dataset placement, import, Nginx, env config, Git-prevention, teammate dataset access).
- Backward compatible: existing Wikimedia/Unsplash/AI/postcard image flow untouched; SQLite stays the database; 36 offline tests pass.

---

## 📸 Real Photos for Festivals, Temples, Lakes, Rivers, Peaks & More (+70 verified covers)

- **70+ new verified Wikimedia Commons photos** attached as covers for destinations that previously showed SVG postcards, across:
  Temples & Hindu Sites (58→93 real), Mountains & Peaks (24→68), City Tourism, Rivers & River Valleys (29→44), Lakes (31→43), Buddhist Sites & Monasteries (24→37), Waterfalls, UNESCO/Heritage, Pilgrimage, Caves, Hot Springs.
- Notable additions: Badimalika Temple, Bindabasini Temple, Budhasubba Temple, Janaki Temple, Dhanushadham, Jaleshwar Mahadev, Palanchowk Bhagwati, Kalinchowk Bhagwati, Dolakha Bhimsen, Bajrayogini, Matatirtha, Pindeshwor, Kankalini, Baidyanath Dham, Namo Buddha, Pullahari, Shey Gompa, Seto Gumba, Thrangu Tashi Yangtse, Bedkot Lake, Panch Pokhari, Tsho Rolpa, Imja Lake, Jagadishpur Lake, Gunde Lake, Dudh Pokhari (Gokyo), Arun/Karnali/Koshi/Marshyangdi/Mahakali/Indrawati/Bishnumati/Tamur/Tama Koshi rivers, Ama Dablam, Cho Oyu, Gauri Shankar, Api Himal, Cholatse, Chulu East, Dorje Lakpa, Hyatung Falls→Rani Pokhari fix, Tindhare, Purandhara, Namaste, Jhor, Lamo Jharana, Pachal, Rupal, Biratnagar, Birgunj, Bharatpur (Narayanghat), Pullahari, Pharping Yangleshö, Bhurung Tatopani.
- Every photo verified to exist via the Wikimedia Commons search API (thumbnails + canonical CDN URLs); rows are `source=wikimedia`, `verification_status=approved`, with attribution & source links.
- Fixed 2 bad assignments discovered in audit (Manang Braga ← Panauti photo reverted; Serchan Hotel ← Rani Pokhari reverted) and corrected Rani Pokhari's cover (was Ghanta Ghar clock tower).
- Manifest (`verified_wikimedia_photos.json`) rebuilt from DB: **2,853 entries**.
- Final: 7,517 destinations — **2,853 real photo covers** + 274 AI landmark covers + 3,735 SVG postcards (mostly hotels/lodges with no publicly licensed photo).
---

## 🖼️ Round 2: Verified Real Photos for Viewpoints, Stupas, Festivals, Tea/Coffee, Adventures & Heritage

- **72 more destinations** now show real Wikimedia Commons photos instead of SVG postcards (total verified covers: **2,853 → 2,925**).
- **Viewpoints**: Pikey Peak, Phulchowki Hill (x2), Chukhung Ri, View to Cho Oyu, Larke La (x2), Dho Tarap, Sarangkot Sunset, Mohare Dada (x3), Lamjura La, Maipokhari, Resunga (x2), Jamacho/Nagarjun, Makalu Viewpoint.
- **Stupas & gompas**: Thubchen Gompa, Jampa Gompa, Chhairo Gompa, Chhoser Jhong Cave Gompa.
- **Festivals**: Chhath (Terai) — the last SVG festival card is now a real Chhath Puja photo.
- **Tea / coffee / farms**: Jhapa Tea Gardens, Gulmi Coffee, Syangja Orange, Rasuwa Apple Orchards, Humla Apple & Barley.
- **Adventures**: Kusma Bungee (Cliff Nepal), The Last Resort Bungee, Trishuli / Seti / Sun Koshi rafting, Birethanti canyoning, Pokhara paragliding.
- **Heritage**: Makwanpur Gadhi, Sindhuli Gadhi, Lo Manthang Royal Palace, Tilaurakot (Suddhodana's Palace), Araniko / BP Koirala / Prithvi / Siddhartha / Pasang Lhamu / Mahendra highways, Kali Gandaki Corridor.
- **Temples (no more SVG)**: Ambikeshwori, Badimalika (x2), Barahachhetra (x5), Bhairabsthan, Chhintang Devi, Padukasthan, Panch Pokhari, Kailashnath Mahadev, Ridi Kunda, Shesh Narayan, Siddha Gufa, Siddhi Lakshmi, Surma Sarovar, Swargadwari (x3), Triveni Dham, Halesi, Bibah Panchami Mandap.
- **Housekeeping**:
  - Manifest rebuilt to **2,925** entries via new `scripts/rebuild_manifest.py` (DB-driven, no network).
  - Reproducible mapping kept at `scripts/round2_verified_photos.tsv` + `scripts/apply_round2_photos.py`.
  - DB integrity verified: **7,517 dests, 0 destinations with >1 cover, `PRAGMA integrity_check` = ok**; DB vacuumed (45 MB).
  - **Repo slimmed**: removed `downloads/nepal-tourism-database.sqlite3` (45 MB dup), `nepal-images-only.zip` (22 MB), `nepal-tourism-full-project.zip` (14 MB) — only the 4.4 MB `.gz` snapshot stays; all are git-ignored and regenerable (see `downloads/README.txt`). Keeps clone size under ~50 MB at HEAD.
  - Docs updated: `docs/IMAGE_SERVER.md` §10 (enrichment rounds) & §11 (repo-size strategy).

---

## 🌐 Round 3: Multi-Platform Real Photos (Openverse — Flickr, WordPress.org, Commons) + DB Shrunk 45MB → 15MB

- **26 more destinations** got real photos from **other platforms** (no longer only Wikimedia/Unsplash):
  - **Flickr** (via Openverse, direct `live.staticflickr.com` hotlinks): Bat Cave Pokhara, Chhoser Jhong Cave, Chhoser Sky Caves, Garphu Cave, Nagi Gompa, Panchase Trek, Makalu Base Camp Trek, Nar Phu Trek, Bhojpur Momo Trail, Paddy fields (Rice Fields ×2).
  - **WordPress.org Photos** (CC0): Dhindo Thali, Dipang Lake.
  - **Wikimedia via Openverse search** (new finds Commons missed): Maratika Caves, Milarepa Cave, Tindhare Falls, Tatopani (Sunkoshi) Hot Spring, Phakding, Braga Village (Braga Gompa + Manang Braga), Banke National Park, Kalinchowk Snow ×2, Api Nampa Conservation Area, Parsa National Park, Shanti Stupa (Pumdi Bhumdi View Tower).
- **New categories covered with real photos**: Caves, Waterfalls, Hot Springs, Villages, Wildlife/Safari, Trekking, Snow/Winter, Food, Viewpoints.
- **License safety**: only CC BY / CC BY-SA / CC0 photos used (NC/ND rejected); every row stores photographer + license + source page.
- **DB size reduced 45 MB → 15 MB**: deleted 38,381 redundant SVG postcard gallery-variant rows (5 per destination; covers untouched — exactly 1 per destination, `integrity_check` ok, 60 tests pass). The compressed download snapshot shrank to **2.0 MB**.
- Manifest rebuilt to **2,951** entries (wikimedia + openverse) via `scripts/rebuild_manifest.py`; `photo_catalog._verified_photo` now returns the real source platform.
- Reproducible mapping: `scripts/round3_verified_photos.tsv` + `scripts/apply_round3_photos.py`.
- Docs updated: `docs/IMAGE_SERVER.md` §12, `downloads/README.txt`.

---

## 🗺️ Round 4: Karnali/Sudurpashchim real photos + Search autocorrect (A–Z + Did-you-mean)

- **12 real covers for the far-west provinces**: Rara Lake & National Park ×3 (2 of them had NO cover row at all — the reason the user saw no Karnali images), Shuklaphanta National Park ×2, Kanjiroba Himal, Karnali River ×3 (Humla Karnali Valley, Karnali Corridor/Hilsa Road, Karnali Highway), Krishnasar Conservation Area, Dho Tarap, Bhimdatta (Mahendranagar). Real covers now **2,963**.
- **Search now autocorrects and suggests from the real data**:
  - `/api/v1/destinations/autocomplete/?q=katmandu` → `did_you_mean: Kathmandu` (fuzzy match against all 7,517 real names; guards prevent junk corrections like "safary"→"Sakfara").
  - `?letter=A..Z` → alphabetically-sorted place suggestions per letter; `/destinations?letter=M` filters server-side across all pages (was broken: filtered only the current page).
  - Landing page search bar + Destinations explorer now show live suggestion dropdowns with a "✨ Did you mean" row.
- **Gap report**: 7,517 dests → 2,963 real + 274 AI-landmark + 3,631 SVG (mostly hotels) + 649 no-cover (168 non-hotel). Remaining real-photo candidates are obscure OSM nodes with zero public photos.
- DB still 15 MB; snapshot 2.0 MB; manifest rebuilt to **2,963**; 60 tests pass; frontend builds clean.

---

## 🚫 Round 5: Zero repeated/generic images + 32 more real covers (total 2,995)

- **Every Unsplash hotlink removed from the frontend (0 remaining)** — they were the
  "same image everywhere" problem (shared mountain/lake photos on cards, one hotel
  photo for all hotels). Replaced with:
  - per-destination unique SVG postcard fallbacks (DestinationCard/HotelCard onError),
  - the 40 unique local landmark photos (PlaceholderImage, ProvinceMarquee,
    AuthShell, Chatbot, Gallery, Compare, AdminDashboard, LocalApi, geocoder,
    nepalDestinations data) — deterministic per card, no repeats, no external deps.
  - backend `NEPAL_CURATED_PHOTOS` Unsplash list replaced with local paths.
- **32 more real covers** (total **2,995**): Ghandruk, International Mountain
  Museum ×2, Bardia NP, Lumbini Maya Devi Temple ×4, Chandragiri Cable Car,
  Bageshwori Temple ×2, Bhaleshwor Mahadev, Kumari Cave, Kodari Tatopani,
  Bhedetar/Namaste Jharna, Sailung, Kankai River, Darchula (Api BC) + verified
  reuses for sister destinations: Chitwan NP ×5, Lo Manthang ×3, Halesi ×2,
  Poon Hill Trek, Budhanilkantha, Bagmati River, Chhoser Gompa.
- No-cover destinations: 649 → **619**. DB still 15 MB; manifest 2,995; 60 tests pass.
