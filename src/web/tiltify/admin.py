from django.contrib import admin

from src.web.tiltify.models import Campaign, Donation, Option, Poll, Reward, RewardClaim


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


class RewardClaimInline(admin.TabularInline):
    list_display = ("quantity", "reward")
    model = RewardClaim


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("id", "amount", "name", "comment", "completed_at", "has_rewards")
    inlines = [RewardClaimInline]

    def has_rewards(self, obj):
        return obj.rewardclaim_set.exists()


@admin.register(RewardClaim)
class RewardClaimAdmin(admin.ModelAdmin):
    list_display = ("id", "quantity", "reward", "donation")
