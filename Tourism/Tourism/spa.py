"""Serve the built React app's index.html for client-side routes.

Only active when settings.FRONTEND_DIST_DIR contains a build (the Docker
image). API, admin, static, media and websocket paths never reach this view.
index.html is sent with no-cache so a new deploy is picked up immediately;
the hashed /assets/* files it references are long-cached by WhiteNoise.
"""
from django.conf import settings
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET


@require_GET
def spa_index(request, path=""):
    index = settings.FRONTEND_DIST_DIR / "index.html"
    if not index.is_file():
        raise Http404("Frontend build not installed.")
    response = FileResponse(index.open("rb"), content_type="text/html; charset=utf-8")
    response["Cache-Control"] = "no-cache"
    return response
