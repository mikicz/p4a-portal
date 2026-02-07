from django.contrib import admin
from django.urls import path

from src.web.tiltify.views import CampaignsView, CampaignView, WebhookView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", CampaignsView.as_view(), name="index"),
    path("<int:pk>/", CampaignView.as_view(), name="campaign"),
    path("webhook/", WebhookView.as_view(), name="webhook"),
]
