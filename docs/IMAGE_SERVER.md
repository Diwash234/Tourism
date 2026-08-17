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
| `thumbnail_url`| full URL (1000px thumb served by the image server) |

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
