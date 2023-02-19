from __future__ import annotations

from datetime import timedelta

from django.core.management import BaseCommand
from django.utils import timezone

from src.client import schema
from src.client.api import get_donations
from src.web.tiltify.management.import_utils import build_donation, import_campaign_details, import_rewards
from src.web.tiltify.models import Campaign, Donation, Reward


class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaign in Campaign.objects.filter(keep_refreshing=True).exclude(uuid=None):
            self.import_campaign(campaign)

    def import_campaign(self, campaign: Campaign):
        import_campaign_details(campaign)
        import_rewards(campaign)
        campaign.stats_refresh_finished = timezone.now()
        self.import_donations(campaign)
        campaign.save(update_fields=["stats_refresh_finished"])

    def import_donations(self, campaign: Campaign):
        print("Importing donations details")

        to_create: list[schema.Donation] = []
        created_total: int = 0

        after: str | None = None
        response: schema.DonationResponse | None
        donation_queryset = Donation.objects.filter(campaign=campaign)

        imported_ids = set(donation_queryset.values_list("uuid", flat=True))
        completed_after = None
        if donation_queryset.exists():
            completed_after = donation_queryset.latest("completed_at").completed_at - timedelta(minutes=30)

        reward_map = {reward.uuid: reward for reward in Reward.objects.filter(campaign=campaign)}
        while True:
            response = get_donations(campaign.uuid, after=after, completed_after=completed_after)

            not_imported_yet = [x for x in response.data if x.id not in imported_ids]
            to_create.extend(not_imported_yet)
            imported_ids.update([x.id for x in response.data])

            if response.metadata.after is None or not response.data:
                break

            if response.metadata.after is not None:
                after = response.metadata.after

            if len(to_create) >= 10_000:
                created_total += len(
                    Donation.objects.bulk_create(
                        [build_donation(campaign, reward_map, api_donation) for api_donation in to_create]
                    )
                )
                to_create = []

        created_total += len(
            Donation.objects.bulk_create(
                [build_donation(campaign, reward_map, api_donation) for api_donation in to_create]
            )
        )
        print("New total", donation_queryset.count(), "created", created_total)
