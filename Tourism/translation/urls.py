from django.urls import path

from . import views

urlpatterns = [
    # Path unchanged from the pre-split tourist/urls.py entry --
    # mounted at the same api/v1/ level in the project urls.py, so the
    # full URL stays exactly /api/v1/translate/.
    path("translate/", views.TranslateTextView.as_view(), name="translate-text"),
]