from django.urls import path

from . import views

urlpatterns = [
    path("translate/", views.TranslateTextView.as_view(), name="translate-text"),
    path("translate/batch/", views.TranslateBatchView.as_view(), name="translate-batch"),
]