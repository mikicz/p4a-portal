from django.contrib import admin

from src.web.tiltify.models import Campaign, Reward, Poll, Option, Donation


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "amount")


class OptionInline(admin.TabularInline):
    list_display = ("id", "name", "total_amount_raised", "created_at", "updated_at")
    model = Option


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "active", "created_at", "updated_at")
    inlines = [OptionInline]


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("id", "reward", "amount", "name", "comment", "completed_at")
