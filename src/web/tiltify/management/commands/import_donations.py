from __future__ import annotations

from datetime import timedelta

from django.core.management import BaseCommand
from django.utils import timezone

from src.client import schema
from src.client.api import get_authenticated_session, get_donations
from src.client.exceptions import CampaignNotFoundError
from src.web.tiltify.management.import_utils import (
    create_donations_and_reward_claims,
    import_campaign_details,
    import_rewards,
)
from src.web.tiltify.models import Campaign, Donation, Option, Poll, Reward


class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaign in Campaign.objects.filter(keep_refreshing=True).exclude(uuid=None):
            try:
                if not campaign.name:
                    import_campaign_details(campaign)
            except CampaignNotFoundError:
                print(f"Campaign {campaign.uuid} not found")
                continue
            self.import_campaign(campaign)

    def import_campaign(self, campaign: Campaign):
        import_rewards(campaign)
        campaign.stats_refresh_finished = timezone.now()
        self.import_donations(campaign)
        campaign.save(update_fields=["stats_refresh_finished"])

    def import_donations(self, campaign: Campaign):
        print("Importing donations details")

        to_create: list[schema.Donation] = []
        created_total: int = 0
        created_claims: int = 0

        after: str | None = None
        response: schema.DonationResponse | None
        donation_queryset = Donation.objects.filter(campaign=campaign)

        imported_ids = set(donation_queryset.values_list("id", flat=True))
        completed_after = campaign.published_at - timedelta(days=1)
        if donation_queryset.filter(loaded_from_webhook=False).exists():
            completed_after = donation_queryset.filter(loaded_from_webhook=False).latest(
                "completed_at"
            ).completed_at - timedelta(minutes=30)

        reward_map = {reward.uuid: reward for reward in Reward.objects.filter(campaign=campaign)}

        polls = set(Poll.objects.filter(campaign=campaign).values_list("id", flat=True))
        options = set(Option.objects.filter(poll__campaign=campaign).values_list("id", flat=True))

        seen_ids = set()

        with get_authenticated_session() as session:
            while True:
                response = get_donations(session, campaign.uuid, after=after, completed_after=completed_after)

                not_imported_yet = [x for x in response.data if x.id not in imported_ids]
                seen_ids.update({x.id for x in response.data})
                to_create.extend(not_imported_yet)
                imported_ids.update([x.id for x in response.data])

                if response.metadata.after is None or not response.data:
                    break

                if response.metadata.after is not None:
                    after = response.metadata.after

                if len(to_create) >= 10_000:
                    created_total, created_claims = create_donations_and_reward_claims(
                        campaign=campaign,
                        reward_map=reward_map,
                        to_create=to_create,
                        currently_donations_created=created_total,
                        currently_reward_claims_created=created_claims,
                        polls=polls,
                        options=options,
                    )
                    to_create = []

        created_total, created_claims = create_donations_and_reward_claims(
            campaign=campaign,
            reward_map=reward_map,
            to_create=to_create,
            currently_donations_created=created_total,
            currently_reward_claims_created=created_claims,
            polls=polls,
            options=options,
        )
        print(
            "New total",
            donation_queryset.count(),
            "created donations",
            created_total,
            "created reward claims",
            created_claims,
        )

        # update the ones we saw in command
        Donation.objects.filter(id__in=seen_ids, loaded_from_webhook=True).update(loaded_from_webhook=False)
