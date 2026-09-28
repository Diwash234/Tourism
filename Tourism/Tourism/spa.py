from pathlib import Path
from django.http import FileResponse, Http404
from django.conf import settings


def spa_index(request):
    index_path = Path(settings.BASE_DIR) / "frontend_dist" / "index.html"
    if not index_path.is_file():
        raise Http404("Frontend bundle is not installed")
    return FileResponse(index_path.open("rb"), content_type="text/html; charset=utf-8")
