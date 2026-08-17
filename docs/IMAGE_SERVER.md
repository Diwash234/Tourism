# Standalone Image Server — Architecture & Operations

The Tourism platform keeps its **100,000+ image dataset out of Git** and serves it
from a dedicated static image server. Django stores only *metadata + relative
paths*; the browser loads images straight from the image server.

```
React frontend  ──▶  Django REST API  ──▶  SQLite database
                                                │  image_path (e.g. nepal/kathmandu/001.webp)
                                                ▼
                                           IMAGE_BASE_URL  (configurable)
                                                │
                                                ▼
                                  separate image server (dev: python -m http.server,
                                  prod: Nginx)  ──▶  100,000+ tourism images on disk
```

## Directory layout

```
image-server/
├── images/                  # ← THE DATASET (git-ignored, never committed)
│   ├── nepal/kathmandu/     # 001.webp, 002.webp, ...
│   ├── nepal/pokhara/
│   ├── nepal/mustang/
│   ├── india/
│   └── other-countries/
├── deploy/nginx-image-server.conf
├── scripts/serve.py         # dev server wrapper
├── scripts/verify_tree.py   # sanity checker
└── README.md                # full ops guide (same content as this doc)
```

## 1. Run the image server locally

```bash
cd image-server
python -m http.server 8000            # or: python scripts/serve.py 8000
```

Then:

```
http://localhost:8000/images/nepal/kathmandu/001.webp   → serves the file
```

## 2. Where the 100k+ images go

Extract/rsync the shared dataset into `image-server/images/` keeping the
`country/place/` layout. Supported extensions: `.webp .jpg .jpeg .png .gif .avif`.
Folder names should match destination slugs (`kathmandu`, `pokhara`, …) so the
import command can associate files automatically; filename prefixes
(`kathmandu_001.webp`) also work.

**Dataset access for teammates** (dataset is NOT on GitHub):

- Ask the team lead for the shared link/NAS path (e.g. `tourism-images-2026.zip`), or
- `rsync -avz user@images.internal.example.com:/srv/tourism-images/ image-server/images/`

Then run the import command (section 5).

## 3. How Django references images

`DestinationImage` stores only:

| field          | example |
|----------------|---------|
| `image_path`   | `nepal/kathmandu/001.webp` |
| `alt_text`     | `Kathmandu Durbar Square 001` |
| `ordering`     | `1` |
| `external_url` | full URL (cache of the image-server URL) |
| `thumbnail_url`| full URL (960px thumb served by the image server) |

- No `ImageField` is used for dataset images — the binary never enters SQLite.
- URL builder: `Tourism/tourist/image_server.py::image_server_url(path)`
- Config: `IMAGE_BASE_URL` and `IMAGE_SERVER_ROOT` in `Tourism/Tourism/settings.py`
  (both overridable via `.env`).

## 4. How React displays images

The Django API returns ready-to-use absolute URLs:

```json
{
  "id": 1,
  "name": "Kathmandu",
  "cover_image_url": "http://localhost:8000/images/nepal/kathmandu/001.webp",
  "images": [
    "http://localhost:8000/images/nepal/kathmandu/001.webp",
    "http://localhost:8000/images/nepal/kathmandu/002.webp"
  ],
  "gallery": [
    { "id": 10, "display_url": "http://localhost:8000/images/nepal/kathmandu/001.webp",
      "alt_text": "Kathmandu Durbar Square 001", "ordering": 1, "is_cover": true }
  ]
}
```

`getDestinationImageUrl(destination)` in `frontend/Tourism/src/utils/imageUtils.js`
prefers `destination.images[0]`, then `cover_image_url`, then `gallery[].display_url`.
Rendering is a plain `<img src={getDestinationImageUrl(d)} alt={d.name} />` — the
browser talks to the image server directly, Django is out of the transfer path.

## 5. Importing image metadata

```bash
python manage.py import_images                                  # uses IMAGE_SERVER_ROOT
python manage.py import_images ./image-server/images            # explicit path
python manage.py import_images --dry-run                        # preview only
python manage.py import_images --link-by name                   # match by name not slug
python manage.py import_images --cover --set-ordering           # set covers + ordering
python manage.py import_images --max-per-destination 10
python manage.py import_images --base-url https://images.example.com
```

It recursively scans, matches files to destinations (folder slug/name, then
filename prefix), creates `DestinationImage` rows with path/URL/alt/ordering,
skips duplicates, and prints progress + unmatched files. **It never reads image
binaries into the DB.**

## 6. Configuration — `IMAGE_BASE_URL`

| environment | value |
|---|---|
| dev | `IMAGE_BASE_URL=http://localhost:8000` (default) |
| prod | `IMAGE_BASE_URL=https://images.example.com` |

Set in `Tourism/.env` (see `.env.example`). Nothing hard-codes the prod domain.
Frontend optionally supports `VITE_IMAGE_BASE_URL` (see `frontend/Tourism/.env.example`).

## 7. Production Nginx

`image-server/deploy/nginx-image-server.conf`:

```nginx
server {
    listen 443 ssl;
    server_name images.example.com;
    # ssl_certificate / ssl_certificate_key ...

    root /srv/tourism-images;        # the image-server/images tree on the server
    autoindex off;

    location /images/ {
        try_files $uri =404;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Browser requests `https://images.example.com/images/nepal/kathmandu/001.webp` →
Nginx streams the file from disk. Django is never involved.

## 8. Keeping the dataset out of Git

- `.gitignore` ignores `image-server/images/*` (only `.gitkeep` placeholders are
  committed).
- `Tourism/media/` is already ignored.
- Sanity check: `python image-server/scripts/verify_tree.py` — fails if any image
  file under `image-server/images/` is tracked by Git.
- Golden rule: never `git add image-server/images/…` with real files; distribute
  the dataset out-of-band (shared drive / rsync).

## 9. What changed in this branch

- **New**: `image-server/` (code/config/placeholders only), `docs/IMAGE_SERVER.md`,
  `Tourism/tourist/image_server.py`, migration `0016_...` (adds `image_path`,
  `alt_text`, `ordering` to `DestinationImage` + indexes `destimg_dest_order_idx`,
  `destimg_path_idx`), management command `import_images`, `IMAGE_BASE_URL`/
  `IMAGE_SERVER_ROOT` settings, serializer fields `image_url` / `images` /
  `alt_text` / `ordering`, frontend `images`-array handling in `imageUtils.js`,
  `.env.example` entries for both backend and frontend.
- **Unchanged**: SQLite stays the database; existing models/migrations intact;
  existing image pipeline (Wikimedia/Unsplash/AI/postcards) still works and is
  just extended by `image_path`-based rows.

## 10. Verified real-photo enrichment rounds (temples, festivals, viewpoints …)

On top of the image-server pipeline, the DB itself now carries **2,951
verified cover photos** (Wikimedia Commons, Flickr and WordPress.org) (hotlinked from
`upload.wikimedia.org` — no binaries stored in SQLite, so the DB grows only
a few KB per photo). Two enrichment rounds were applied:

- **Round 1** (`6a18bd0`): 72 covers for temples, peaks, lakes, rivers,
  gompas, cities, waterfalls, pilgrimage sites.
- **Round 2** (this change): 72 covers for **viewpoints, stupas/gompas,
  festivals (Chhath), tea/coffee/apple farms, adventure sports (bungee,
  rafting, paragliding, canyoning), heritage (forts, palaces, highways) and
  temples** — e.g. Kusma Bungee, Last Resort Bungee, Trishuli/Seti/Sun
  Koshi rafting, Jhapa Tea Gardens, Pikey Peak, Chukhung Ri, Larke La,
  Dho Tarap, Makwanpur Gadhi, Sindhuli Gadhi, Lo Manthang Royal Palace,
  Tilaurakot, Araniko/BP/Prithvi/Siddhartha/Pasang Lhamu/Mahendra highways,
  Ambikeshwori, Badimalika, Barahachhetra, Bhairabsthan, Padukasthan,
  Siddha Gufa, Swargadwari, Halesi, Thubchen Gompa, Jampa Gompa,
  Chhairo Gompa, Chhoser Jhong Cave Gompa and more.

Rules that keep this safe and reproducible:

1. **Every destination keeps exactly 1 cover** — the old SVG postcard cover
   is demoted to `is_cover=0` (kept as gallery) and the new verified photo
   becomes the cover. `dests>1 cover = 0` is asserted after every run.
2. Filenames are validated against the junk filters in
   `scripts/enrich_verified_photos.py` (maps, logos, `.svg/.gif/.pdf`, crash/
   war/party photos, generic "Himalayas" shots …) and matched by name tokens
   to the destination.
3. Photo metadata (photographer, license, source URL) is stored per row;
   the API serves `attribution` so credit is always shown.
4. The manifest `Tourism/tourist/verified_wikimedia_photos.json` is rebuilt
   from the DB (`scripts/rebuild_manifest.py`, no network needed) and drives
   the frontend cover resolution in `photo_catalog.py`.

Remaining SVG postcards are mostly hotels/guest-houses, tiny OSM viewpoint
nodes and obscure villages with genuinely no public photo — the deterministic
postcard system covers those so no card is ever blank.

## 11. Keeping the GitHub repo small (clone size)

The repo intentionally stays under ~50 MB of tracked data at HEAD:

- `Tourism/db.sqlite3` (~15 MB) is the single committed database — it is
  under GitHub's 100 MB/file limit, and photo rows are metadata only.
- `downloads/` keeps **only** the compressed snapshot
  `nepal-tourism-database.sqlite3.gz` (~2.0 MB). The uncompressed duplicate,
  the images zip and the full-project zip are git-ignored and regenerable
  (`downloads/README.txt` shows the exact commands).
- The 100k+ photo dataset lives in `image-server/images/`, which is
  git-ignored by design (section 8) — never commit binaries there.
- Old copies remain in git history (that's why `.git` is larger than the
  working tree); if you want a fully slim clone, rewrite history with
  `git filter-repo` and force-push — do this only when you're ready to
  invalidate existing clones.

## 12. Round 3 — multi-platform real photos (Openverse: Flickr / WordPress.org)

The user asked to stop relying on Wikimedia/Unsplash only and pull from other
social media + platforms too. Round 3 added **26 more real covers** (total
**2,951**) sourced through the **Openverse API** (`api.openverse.org`, an open
aggregator of CC-licensed images):

- **Flickr** (via Openverse): Bat Cave Pokhara, Jhong Cave, Chhoser valley,
  Nagi Gompa, Panchase Trek, Makalu Base Camp, Nar Phu Valley, momo, paddy
  fields — direct `live.staticflickr.com` URLs with photographer + CC license.
- **WordPress.org Photos** (via Openverse): Dhindo Thali, Dipang Lake — CC0.
- **Wikimedia Commons** (via Openverse search): Maratika Caves, Milarepa
  Cave, Tindhare Falls, Tatopani Sindhupalchok, Phakding, Braga Village,
  Banke NP, Kalinchowk Snow, Api Nampa, Parsa NP, Shanti Stupa (Pumdi Bhumdi).

New categories covered: caves, waterfalls, hot springs, villages, wildlife,
trekking, snow/winter, food, forests/eco. Legal rule applied: **only
CC BY / CC BY-SA / CC0** photos are used (no NC/ND), attribution stored per
row. `source_platform`/`license_type`/`photographer` are exposed by the API.

**DB size cut 45 MB → 15 MB:** the 38,381 redundant SVG postcard *gallery*
variant rows (5 per destination) were deleted — every destination keeps its
cover (real photo or the single deterministic postcard), and gallery
fallbacks are generated on the fly (`resolve_gallery_photos`). `VACUUM` after.

## 13. Round 4 — Karnali & Sudurpashchim real photos + search autocorrect

- **12 more real covers** for the far-west provinces the user reported as
  missing: **Rara Lake & National Park** (3 destinations — including two that
  previously had *no cover row at all*), **Shuklaphanta National Park** ×2,
  **Kanjiroba Himal**, **Karnali River** (Humla Karnali Valley, Karnali
  Corridor/Hilsa Road, Karnali Highway), **Krishnasar Conservation Area**
  (blackbucks), **Dho Tarap** village and **Bhimdatta (Mahendranagar)**.
  Real covers now **2,963** (2,925 Commons + 38 Openverse/Flickr/WordPress).
- **Remaining gap report** (7,517 destinations): 2,963 real covers, 274
  curated AI landmark covers, 3,631 SVG postcards (≈2,900 are hotels/guest
  houses with no public photo anywhere), 649 destinations with no cover row
  (168 are non-hotel — mostly tiny OSM nodes).
- **Search suggestions + autocorrect**: `GET /api/v1/destinations/autocomplete/`
  now returns `{query, did_you_mean, results}` — fuzzy `did_you_mean` is
  computed from the real destination names (difflib, prefix+ratio guards so
  "katmandu"→"Kathmandu" works but garbage never corrects to unrelated
  villages). `?letter=A..Z` returns names starting with that letter.
  `DestinationFilter` gained `letter`/`starts_with` so `/destinations?letter=M`
  filters server-side across all pages. Frontend: Landing search bar and the
  Destinations explorer show suggestion dropdowns + "Did you mean" rows.

## 14. Round 5 — no repeated images + 32 more real covers (2,995)

- All `images.unsplash.com` hotlinks removed from the frontend (was the source of
  "same image on every card": shared mountain/lake fallbacks, one hotel photo for
  all hotels). Fallbacks are now per-destination unique postcards or the 40
  curated local landmark photos — deterministic per card, zero repeats.
- 32 more real covers: Ghandruk, Intl. Mountain Museum ×2, Bardia NP, Lumbini
  Maya Devi ×4, Chandragiri Cable Car, Bageshwori ×2, Bhaleshwor Mahadev,
  Kumari Cave, Kodari Tatopani, Namaste Jharna (Bhedetar), Sailung, Kankai
  River, Darchula/Api + verified reuses (Chitwan ×5, Lo Manthang ×3, Halesi ×2,
  Poon Hill, Budhanilkantha, Bagmati, Chhoser).
- Totals: **2,995 real covers** / 7,517 dests; no-cover 619; DB 15 MB.

## 15. Round 6 — broken-thumbnail root cause fixed + multi-source fallback chain

- **All Wikimedia cover URLs fixed**: the app built `1000px-` thumb URLs, but
  Wikimedia only serves standard sizes (…500/960/1280/1920…) and rejects
  hotlinks to non-standard sizes (phab T414805). All 4,699 rows now use
  `960px-` — verified byte-for-byte against the imageinfo API thumburl.
- **Multi-source fallback chain** (user request: keep Unsplash/Wikimedia as
  filters — use the next source when one is missing):
  real verified cover → API images/gallery → local landmark photos →
  deterministic pool (local + Unsplash landscapes) → unique postcard.
- DB URL audit: 0 junk/utm/1000px URLs. DB 15 MB, manifest 2,995, 60 tests.

## 16. Round 7 — local-landmark photos replace SVG on destination pages

- Frontend now treats SVG postcard URLs as "not a real photo": the resolution
  chain goes real cover → gallery → **local landmark photo** → multi-source
  pool → unique postcard (last resort). ~150 extra place-name → local-photo
  mappings added (Kathmandu sites, Pokhara sites, trek routes, Mustang,
  Terai parks, tea gardens, temples, falls, caves…).
- Destination detail gallery generates 4 deterministic unique photos per
  place (no repeated generic fallbacks).
- 23 more real covers (total **3,018**) + 8 real gallery rows for famous
  places (Gupteshwor, Bhadrakali, Koshi Tappu, Godavari, Makalu, Dhunche,
  Jomsom, Maya Devi).
- Audit totals: 3,018 real + 274 AI + 3,629 SVG (mostly hotels) + 596
  no-cover (frontend chain guarantees a visible photo for every destination).

## 17. Round 8 — all-province data, real images & nationwide emergency/navigation

- Province values normalized to 7 canonical names (filter by `?province=...`).
- 12 new destinations + 12 real covers (total 3,022) for Koshi/Madhesh/Karnali/
  Sudurpashchim incl. Akala Devi, Pathibhara, Jumla, Simikot, Dharan, Gadhimai,
  Lahan, Charikot, Dolakha Bhimsen, Parshuram Dham, Bhimeshwor.
- Navigation "nearby" now uses a 77-facility nationwide directory with real
  Haversine distance + compass bearing (all 7 provinces).
- Emergency page covers all 77 districts.
- MapillaryImages rendered on destination details; setup hint when no token.

## 18. Round 9 — ML mood-form recommendations + category-correct images

- Recommendation page: multi-checkbox mood form → weighted content-based ML
  recommender scoring all destinations; results carry ml_score + real cover +
  budget + best season.
- imageUtils: name-only, category-aware matching with typed photo pools
  (temple/lake/mountain/wildlife/hotel/…) — fixes the "everything in Pokhara
  shows lakeside / Lalitpur shows Patan / temples show tigers" bugs.
- 9 wrong covers replaced with correct real photos (World Peace Pagoda,
  Shanti Stupa, Tal Barahi, 360 Paragliding, Gangkhar Puensum, Mid-Hill
  Highway, Brindaban Forest, Godawari, Devkota House).
- Admin dashboard theme purple -> orange.

## 19. Round 11 — two real photos for every destination (new manifest)

- `verified_wikimedia_photos.json`: 7,548 entries, one per destination,
  each with `url` + `url2` (and `thumb`/`thumb2`, photographer, license,
  source for both). Rebuilt from the DB by `scripts/rebuild_manifest.py`.
- DB: every destination now has 2 verified real image rows (15,115 rows);
  name-seeded category-typed picks from the 794-URL verified pool for the
  5,013 destinations that previously had none.
- API `images[]` = cover + 2 real gallery photos; frontend ignores SVG
  postcard URLs so real images show on cards and detail pages.
