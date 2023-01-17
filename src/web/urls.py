from django.contrib import admin
from django.urls import path

from src.web.tiltify.views import CampaignsView, CampaignView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", CampaignsView.as_view(), name="index"),
    path("<int:pk>/", CampaignView.as_view(), name="campaign"),
]
