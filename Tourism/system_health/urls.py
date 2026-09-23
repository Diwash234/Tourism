from django.urls import path
from . import views

urlpatterns = [
    path("", views.quick_health, name="health-quick"),
    path("full/", views.full_health, name="health-full"),
    path("sample/", views.sample_now, name="health-sample"),
]
