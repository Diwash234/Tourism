
## Image server

The app uses a standalone image server for the large tourism dataset. See
[docs/IMAGE_SERVER.md](../docs/IMAGE_SERVER.md) — run `python -m http.server 8000`
in `image-server/`, set `IMAGE_BASE_URL`, then
`python manage.py import_images ./image-server/images`.
