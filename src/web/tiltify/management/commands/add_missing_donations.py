from django.core.management import BaseCommand

from src.client import schema
from src.client.api import get_donations
from src.web.tiltify.management.import_utils import create_donations_and_reward_claims
from src.web.tiltify.models import Campaign, Donation, Reward


class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaign in Campaign.objects.filter(keep_refreshing=True).exclude(uuid=None):
            self.check_import_campaign(campaign)

    def check_import_campaign(self, campaign: Campaign):
        all_donations: list[schema.Donation] = self.import_donations(campaign)
        self.fix_donations(campaign, all_donations)

    def import_donations(self, campaign: Campaign) -> list[schema.Donation]:
        missing: list[schema.Donation] = []
        all_donations: list[schema.Donation] = []
        after: str | None = None
        response: schema.DonationResponse | None

        donation_queryset = Donation.objects.filter(campaign=campaign)
        imported_ids = set(donation_queryset.values_list("id", flat=True))

        while True:
            response = get_donations(campaign.uuid, after=after)
            all_donations.extend(response.data)
            chunk_missing = [x for x in response.data if x.id not in imported_ids]
            missing.extend(chunk_missing)

            if response.metadata.after is None or not response.data:
                break

            if response.metadata.after is not None:
                after = response.metadata.after

        reward_map = {reward.uuid: reward for reward in Reward.objects.filter(campaign=campaign)}

        created_total, created_claims = create_donations_and_reward_claims(
            campaign=campaign,
            reward_map=reward_map,
            to_create=missing,
            currently_donations_created=0,
            currently_reward_claims_created=0,
        )

        print(
            "New total",
            donation_queryset.count(),
            "created donations",
            created_total,
            "created claims",
            created_claims,
        )

        return all_donations

    def fix_donations(self, campaign: Campaign, all_donations: list[schema.Donation]):
        all_donations_ids = {x.id for x in all_donations}

        donation_ids_list = list(
            Donation.objects.filter(
                campaign=campaign,
                completed_at__lte=max([x.completed_at for x in all_donations]),
            ).values_list("id", flat=True)
        )
        donation_ids_set = set(donation_ids_list)

        print("In all donations", len(all_donations_ids))
        print("In database", len(donation_ids_set))
        print("Overlap", len(donation_ids_set & all_donations_ids))
        print("Missing in DB", len(all_donations_ids - donation_ids_set))
        print("Extra in DB", len(donation_ids_set - all_donations_ids))

        for x in donation_ids_set - all_donations_ids:
            donation = Donation.objects.get(id=x)
            print(
                donation.id,
                donation.amount,
                donation.name,
                donation.comment,
                donation.completed_at,
            )
            donation.delete()
