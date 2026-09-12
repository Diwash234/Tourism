from django.urls import path
from . import views

urlpatterns = [
    path("message/", views.ChatMessageView.as_view(), name="chatbot-message"),
    path("history/", views.ChatHistoryView.as_view(), name="chatbot-history"),
    path(
        "nearby-emergency/",
        views.NearbyEmergencyView.as_view(),
        name="nearby-emergency"
    ),
]

urlpatterns += [
    path("support/inbox/", views.SupportInboxView.as_view(), name="support-inbox"),
    path("support/thread/<int:conversation_id>/", views.SupportThreadView.as_view(), name="support-thread"),
    path("support/reply/", views.SupportReplyView.as_view(), name="support-reply"),
    path("support/assign/", views.SupportAssignView.as_view(), name="support-assign"),
]
