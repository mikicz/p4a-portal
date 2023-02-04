from __future__ import annotations

import urllib.parse

from django.core.management import BaseCommand
from django.utils import timezone

from src.client import schema
from src.client.api import get_campaign, get_donations, get_polls, get_rewards
from src.web.tiltify.models import Campaign, Donation, Option, Poll, Reward


class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaign in Campaign.objects.filter(keep_refreshing=True):
            self.import_campaign(campaign)

    def import_campaign(self, campaign: Campaign):
        self.import_campaign_details(campaign)
        self.import_polls(campaign)
        campaign.stats_refresh_finished = timezone.now()
        campaign.save(update_fields=["stats_refresh_finished"])
        self.import_rewards(campaign)
        self.import_donations(campaign)

    def import_campaign_details(self, campaign: Campaign):
        print("Importing campaign details")
        c: schema.Campaign = get_campaign(campaign.id).data
        campaign.name = c.name
        campaign.slug = c.slug
        if c.team is not None and c.team.slug is not None:
            campaign.url = f"+{c.team.slug}/{c.slug}/"
        else:
            campaign.url = f"@{c.user.slug}/{c.slug}/"
        campaign.description = c.description
        campaign.supportable = c.ends_at is None or c.ends_at > timezone.now()
        campaign.save()

    def import_polls(self, campaign: Campaign):
        print("Importing polls details")
        polls = get_polls(campaign.id).data
        campaign.polls_refresh_finished = timezone.now()
        campaign.save(update_fields=["polls_refresh_finished"])
        existing_polls = {x.id: x for x in Poll.objects.all()}
        api_poll: schema.Poll
        for api_poll in polls:
            if api_poll.id in existing_polls:
                poll = existing_polls[api_poll.id]
            else:
                poll = Poll(campaign_id=campaign.id)

            poll.id = api_poll.id
            poll.name = api_poll.name
            poll.active = api_poll.active
            poll.created_at = api_poll.created_at
            poll.updated_at = api_poll.updated_at
            poll.save()

            for api_option in api_poll.options:
                Option.objects.update_or_create(
                    id=api_option.id,
                    poll=poll,
                    defaults={
                        "name": api_option.name,
                        "total_amount_raised": api_option.total_amount_raised,
                        "created_at": api_option.created_at,
                        "updated_at": api_option.updated_at,
                    },
                )

    def import_rewards(self, campaign: Campaign):
        print("Importing rewards details")
        rewards = get_rewards(campaign.id).data
        reward: schema.Reward
        for reward in rewards:
            Reward.objects.update_or_create(
                id=reward.id,
                defaults={
                    "campaign": campaign,
                    "name": reward.name,
                    "amount": reward.amount,
                    "description": reward.description,
                    "kind": reward.kind,
                    "quantity": reward.quantity,
                    "remaining": reward.remaining,
                    "currency": reward.currency,
                    "active": reward.active,
                    "image_src": reward.image.src,
                    "image_alt": reward.image.alt,
                    "image_width": reward.image.width,
                    "image_height": reward.image.height,
                },
            )

    def import_donations(self, campaign: Campaign):
        print("Importing donations details")

        to_create: list[schema.Donation] = []
        all_imported_count = 0

        before: int | None = None
        response: schema.DonationResponse | None
        imported_ids = set(Donation.objects.filter(campaign=campaign).values_list("id", flat=True))
        while True:
            response = get_donations(campaign.id, before=before)

            not_imported_yet = [x for x in response.data if x.id not in imported_ids]
            if not not_imported_yet:
                all_imported_count += 1

            to_create.extend(not_imported_yet)
            imported_ids.update([x.id for x in response.data])

            if response.links.prev is None or not response.data or all_imported_count >= 5:
                break

            parsed_url = urllib.parse.urlparse(response.links.prev)
            query = dict(urllib.parse.parse_qsl(parsed_url.query))
            before = query.get("before")
            if before is not None:
                before = int(before)

            if len(to_create) >= 10_000:
                Donation.objects.bulk_create(
                    [Donation(campaign=campaign, **api_donation.dict()) for api_donation in to_create]
                )
                to_create = []

        Donation.objects.bulk_create([Donation(campaign=campaign, **api_donation.dict()) for api_donation in to_create])
