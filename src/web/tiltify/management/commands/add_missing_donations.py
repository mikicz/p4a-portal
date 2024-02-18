from datetime import timedelta

from django.core.management import BaseCommand

from src.client import schema
from src.client.api import get_donations
from src.web.tiltify.management.import_utils import create_donations_and_reward_claims
from src.web.tiltify.models import Campaign, Donation, Option, Poll, Reward


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
            response = get_donations(
                campaign.uuid, after=after, completed_after=campaign.published_at - timedelta(days=1)
            )
            all_donations.extend(response.data)
            chunk_missing = [x for x in response.data if x.id not in imported_ids]
            missing.extend(chunk_missing)

            if response.metadata.after is None or not response.data:
                break

            if response.metadata.after is not None:
                after = response.metadata.after

        reward_map = {reward.uuid: reward for reward in Reward.objects.filter(campaign=campaign)}

        polls = set(Poll.objects.filter(campaign=campaign).values_list("id", flat=True))
        options = set(Option.objects.filter(poll__campaign=campaign).values_list("id", flat=True))

        created_total, created_claims = create_donations_and_reward_claims(
            campaign=campaign,
            reward_map=reward_map,
            to_create=missing,
            currently_donations_created=0,
            currently_reward_claims_created=0,
            polls=polls,
            options=options,
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
        all_donations_map = {x.id: x for x in all_donations}

        missing_poll_ids = set(Donation.objects.filter(campaign=campaign, poll_id=None).values_list("id", flat=True))
        missing_option_ids = set(
            Donation.objects.filter(campaign=campaign, poll_option_id=None).values_list("id", flat=True)
        )

        donation_ids_list = list(
            Donation.objects.filter(
                campaign=campaign,
                completed_at__lte=max([x.completed_at for x in all_donations]),
            ).values_list("id", flat=True)
        )
        donation_ids_set = set(donation_ids_list)

        polls = set(Poll.objects.filter(campaign=campaign).values_list("id", flat=True))
        options = set(Option.objects.filter(poll__campaign=campaign).values_list("id", flat=True))

        updated_missing_poll = 0
        for donation_id in missing_poll_ids & {x.id for x in all_donations if x.poll_id is not None}:
            if all_donations_map[donation_id].poll_id in polls:
                Donation.objects.filter(id=donation_id).update(poll_id=all_donations_map[donation_id].poll_id)
                updated_missing_poll += 1

        updated_missing_poll_option = 0
        for donation_id in missing_option_ids & {x.id for x in all_donations if x.poll_option_id is not None}:
            if all_donations_map[donation_id].poll_option_id in options:
                Donation.objects.filter(id=donation_id).update(
                    poll_option_id=all_donations_map[donation_id].poll_option_id
                )
                updated_missing_poll_option += 1

        print("In all donations", len(all_donations_map.keys()))
        print("In database", len(donation_ids_set))
        print("Overlap", len(donation_ids_set & all_donations_map.keys()))
        print("Missing in DB", len(all_donations_map.keys() - donation_ids_set))
        print("Extra in DB", len(donation_ids_set - all_donations_map.keys()))
        print("Updated missing poll_id", updated_missing_poll)
        print("Updated missing poll_option_id", updated_missing_poll_option)

        for x in donation_ids_set - all_donations_map.keys():
            donation = Donation.objects.get(id=x)
            print(
                donation.id,
                donation.amount,
                donation.name,
                donation.comment,
                donation.completed_at,
            )
            donation.delete()
