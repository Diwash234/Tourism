from django.urls import path

from . import views

urlpatterns = [
    path("images/resolve/", views.ImageResolveView.as_view(), name="image-resolve"),
]