from django.core.management import BaseCommand

from src.client import schema
from src.client.api import get_donations
from src.web.tiltify.management.import_utils import build_donation
from src.web.tiltify.models import Campaign, Donation, Reward


class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaign in Campaign.objects.filter(keep_refreshing=True).exclude(uuid=None):
            self.check_import_campaign(campaign)

    def check_import_campaign(self, campaign: Campaign):
        self.import_donations(campaign)

    def import_donations(self, campaign: Campaign):
        missing: list[schema.Donation] = []
        after: str | None = None
        response: schema.DonationResponse | None

        donation_queryset = Donation.objects.filter(campaign=campaign)
        imported_ids = set(donation_queryset.values_list("uuid", flat=True))

        while True:
            response = get_donations(campaign.uuid, after=after)
            chunk_missing = [x for x in response.data if x.id not in imported_ids]
            missing.extend(chunk_missing)

            if response.metadata.after is None or not response.data:
                break

            if response.metadata.after is not None:
                after = response.metadata.after

        reward_map = {reward.uuid: reward for reward in Reward.objects.filter(campaign=campaign)}
        created_total = len(
            Donation.objects.bulk_create(
                [build_donation(campaign, reward_map, api_donation) for api_donation in missing]
            )
        )
        print("New total", donation_queryset.count(), "created", created_total)

        print("missing", len(missing))
