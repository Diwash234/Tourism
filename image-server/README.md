# Image Server — static image hosting for the Tourism platform

This directory is a **standalone, static image server**. It stores and serves the
large tourism image dataset (100,000+ images) over plain HTTP in development and
over HTTPS via Nginx in production.

**The image files themselves are never committed to Git.** Only this code/config
is committed; `image-server/images/` is in `.gitignore`.

```
image-server/
├── images/                  # ← the actual image dataset lives here (NOT in Git)
│   ├── nepal/
│   │   ├── kathmandu/       # 001.webp, 002.webp, ...
│   │   ├── pokhara/
│   │   └── mustang/
│   ├── india/
│   └── other-countries/
├── deploy/
│   └── nginx-image-server.conf   # production Nginx vhost
├── scripts/
│   └── verify_tree.py            # sanity checker for the dataset layout
└── README.md
```

---

## 1. Run locally (development)

The simplest way is Python's built-in HTTP server, run **from this directory**:

```bash
cd image-server
python -m http.server 8000
```

That makes every file under `images/` available as:

```
http://localhost:8000/images/nepal/kathmandu/001.webp
http://localhost:8000/images/nepal/pokhara/002.jpg
```

Any port works — just keep the port in sync with `IMAGE_BASE_URL` (see below).

You can also use the convenience script:

```bash
python image-server/scripts/serve.py 8000
```

### Verify it works

```bash
curl -I http://localhost:8000/images/nepal/kathmandu/001.webp
# HTTP/1.0 200 OK
```

---

## 2. Where the 100k+ dataset goes

Drop (or symlink) the real images into `image-server/images/`, grouped by
country → place folder:

```
images/
├── nepal/
│   ├── kathmandu/
│   │   ├── 001.webp
│   │   ├── 002.webp
│   │   └── ...
│   ├── pokhara/
│   ├── mustang/
│   └── ... (any Nepali place folder you have)
├── india/
└── other-countries/
```

- Supported extensions: `.webp`, `.jpg`, `.jpeg`, `.png`, `.gif`, `.avif`.
- Folder names should match the destination **slug** (or name) in the database so
  `python manage.py import_images` can associate them automatically
  (e.g. folder `kathmandu` ↔ destination slug `kathmandu`).
- If you only have a loose dump (files named like `kathmandu_001.webp`), the
  import command also matches on filename prefixes.

### Getting the dataset (for teammates)

The dataset lives **outside GitHub** (it is too large). Ask the project owner /
team lead for access to the shared dataset, e.g.:

- a shared drive / cloud storage link (`tourism-images-2026.zip`, ~XX GB), or
- an internal NAS path, or
- `rsync` from the team's image host:

```bash
rsync -avz user@images.internal.example.com:/srv/tourism-images/ image-server/images/
```

After obtaining it, unzip/rsync into `image-server/images/` (keep the
`country/place/` layout) and run the import command (section 5).

---

## 3. How Django references the images

Django **never receives or stores the image binaries**. The database stores only
the relative path and metadata on `DestinationImage`:

| Field          | Example value                          |
|----------------|----------------------------------------|
| `image_path`   | `nepal/kathmandu/001.webp`             |
| `alt_text`     | `Kathmandu Durbar Square – view 1`     |
| `ordering`     | `1`                                    |
| `external_url` | `https://images.example.com/images/nepal/kathmandu/001.webp` (optional cache) |
| `thumbnail_url`| optional thumb URL                     |

The full URL is generated from the **configurable base URL**:

```python
# Tourism/Tourism/settings.py
IMAGE_BASE_URL = config("IMAGE_BASE_URL", default="http://localhost:8000")
IMAGE_SERVER_ROOT = config("IMAGE_SERVER_ROOT", default=str(BASE_DIR.parent / "image-server" / "images"))
```

URL construction helper: `Tourism/tourist/image_server.py::image_server_url(path)`

```python
image_server_url("nepal/kathmandu/001.webp")
# -> "http://localhost:8000/images/nepal/kathmandu/001.webp"   (dev)
# -> "https://images.example.com/images/nepal/kathmandu/001.webp" (prod)
```

The REST API returns these URLs (see section 4); the browser then loads them
straight from the image server — Django is never in the image transfer path.

---

## 4. How React displays them

The frontend uses whatever URL the API returns, in a normal `<img>`:

- `DestinationCard` / `DestinationDetails` → `getDestinationImageUrl(destination)`
  (in `frontend/Tourism/src/utils/imageUtils.js`), which prefers
  `destination.images[0]` / `cover_image_url` / `gallery[].display_url`.
- The destination detail API returns an `images` array of ready-to-use URLs:

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
      "alt_text": "Kathmandu Durbar Square", "ordering": 1, "is_cover": true }
  ]
}
```

No changes are needed to how the browser loads images — they are plain
`<img src="...">` (or the existing `SmartImage` component).

---

## 5. Importing image metadata into the database

```bash
# from the Tourism/ directory (where manage.py lives)
python manage.py import_images                       # uses IMAGE_SERVER_ROOT
python manage.py import_images ./image-server/images # explicit path
python manage.py import_images --dry-run             # preview only
python manage.py import_images --link-by slug        # match by slug (default)
python manage.py import_images --link-by name        # match by name
python manage.py import_images --base-url https://images.example.com
```

What it does:

1. Recursively scans the directory for supported image files.
2. Associates each file with a destination:
   - path folder matches a destination slug (e.g. `nepal/kathmandu/…` → `kathmandu`), or
   - filename prefix matches a destination slug/name (e.g. `kathmandu_001.webp`).
3. Creates/updates `DestinationImage` rows storing only `image_path`, `alt_text`,
   `ordering`, and the computed `external_url`/`thumbnail_url` — **never the binary**.
4. Skips duplicates (same destination + same `image_path`).
5. Prints progress and a summary with any errors (unmatched files, etc.).

---

## 6. Configuration — `IMAGE_BASE_URL`

| Environment | `.env` value |
|---|---|
| Local dev | `IMAGE_BASE_URL=http://localhost:8000` (default) |
| Production | `IMAGE_BASE_URL=https://images.example.com` |

The full URL is always `IMAGE_BASE_URL + /images/ + image_path`. Nothing in the
code hard-codes the production domain.

Frontend (optional): if you ever need to *construct* image URLs client-side,
`frontend/Tourism/.env` can set `VITE_IMAGE_BASE_URL`; `imageUtils.js` reads it.
Normal usage doesn't need it — the API already returns absolute URLs.

---

## 7. Production — Nginx

See `deploy/nginx-image-server.conf` for a complete vhost. Key parts:

```nginx
server {
    listen 443 ssl;
    server_name images.example.com;
    # ... ssl_certificate / ssl_certificate_key ...

    root /srv/tourism-images;            # the extracted image-server/images tree
    autoindex off;

    location /images/ {
        # Serve image files directly from disk. Django is never involved.
        try_files $uri =404;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

The browser requests `https://images.example.com/images/nepal/kathmandu/001.webp`
and Nginx streams the file from disk — zero Django involvement.

---

## 8. Preventing the dataset from entering Git

- `image-server/images/` (and `image-server/images/**`) is ignored in `.gitignore`;
  only `.gitkeep` placeholders are kept.
- `Tourism/media/` is already ignored.
- To be extra safe, run the sanity checker after cloning:

```bash
python image-server/scripts/verify_tree.py --no-write
```

It lists files that would be committed under `image-server/images/` if the
ignore rules were missing (i.e. it double-checks `.gitignore` is doing its job).

**Golden rule:** never `git add image-server/images/...` with real files. Add the
dataset outside Git (shared drive / rsync), and only commit code + metadata.
