from django.urls import path

from . import views

urlpatterns = [
    # Path unchanged from the pre-split tourist/urls.py entry -- mounted
    # at the same api/v1/ level, so the full URL stays exactly
    # /api/v1/images/resolve/.
    path("images/resolve/", views.ImageResolveView.as_view(), name="image-resolve"),
]