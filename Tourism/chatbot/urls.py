from django.urls import path

from . import views

urlpatterns = [
    path("message/", views.ChatMessageView.as_view(), name="chatbot-message"),
    path("history/", views.ChatHistoryView.as_view(), name="chatbot-history"),
]