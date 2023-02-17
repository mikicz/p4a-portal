from __future__ import annotations

import os
from datetime import timedelta
from pprint import pprint
from uuid import UUID

from django.core.management import BaseCommand
from django.utils import timezone

from src.client import schema
from src.client.api import get_campaign, get_donations, get_polls, get_rewards
from src.web.tiltify.models import Campaign, Donation, Option, Poll, Reward


class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaign in Campaign.objects.filter(keep_refreshing=True).exclude(uuid=None):
            self.import_campaign(campaign)

    def import_campaign(self, campaign: Campaign):
        self.import_campaign_details(campaign)
        self.import_rewards(campaign)
        campaign.stats_refresh_finished = timezone.now()
        self.import_donations(campaign)
        campaign.save(update_fields=["stats_refresh_finished"])
        self.import_polls(campaign)

    def import_campaign_details(self, campaign: Campaign):
        print("Importing campaign details")
        c: schema.Campaign = get_campaign(campaign.uuid).data
        campaign.name = c.name
        campaign.slug = c.slug
        if c.team is not None and c.team.slug is not None:
            campaign.url = f"+{c.team.slug}/{c.slug}/"
        campaign.description = c.description
        campaign.supportable = c.retired_at is None or c.retired_at > timezone.now()
        campaign.save()

    def import_polls(self, campaign: Campaign):
        print("Importing polls details")
        polls = []
        after = None
        while True:
            polls_response = get_polls(campaign.uuid, after=after)
            polls.extend(polls_response.data)
            if polls_response.metadata.after is None:
                break
            after = polls_response.metadata.after

        campaign.polls_refresh_finished = timezone.now()
        existing_polls = {x.id: x for x in Poll.objects.all()}
        api_poll: schema.Poll
        for api_poll in polls:
            if api_poll.id in existing_polls:
                poll = existing_polls[api_poll.id]
            else:
                poll = Poll(campaign=campaign)

            poll.id = api_poll.id
            poll.name = api_poll.name
            poll.active = api_poll.active
            poll.created_at = api_poll.inserted_at
            poll.updated_at = api_poll.updated_at
            poll.save()

            for api_option in api_poll.options:
                Option.objects.update_or_create(
                    id=api_option.id,
                    poll=poll,
                    defaults={
                        "name": api_option.name,
                        "total_amount_raised": api_option.amount_raised.value,
                        "created_at": api_option.inserted_at,
                        "updated_at": api_option.updated_at,
                    },
                )
        campaign.save(update_fields=["polls_refresh_finished"])

    def import_rewards(self, campaign: Campaign):
        print("Importing rewards details")
        rewards = []
        after = None
        while True:
            rewards_response = get_rewards(campaign.uuid, after=after)
            rewards.extend(rewards_response.data)
            if rewards_response.metadata.after is None:
                break
            after = rewards_response.metadata.after

        Reward.objects.update(active=False)

        reward: schema.Reward
        for reward in rewards:
            Reward.objects.update_or_create(
                id=reward.legacy_id,
                defaults={
                    "uuid": reward.id,
                    "campaign": campaign,
                    "name": reward.name,
                    "amount": reward.amount.value,
                    "description": reward.description,
                    "quantity": reward.quantity,
                    "remaining": reward.quantity_remaining,
                    "currency": reward.amount.currency,
                    "active": reward.active and (reward.quantity is None or (reward.quantity_remaining or 0) > 0),
                    "image_src": reward.image.src,
                    "image_alt": reward.image.alt,
                    "image_width": reward.image.width,
                    "image_height": reward.image.height,
                },
            )

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
            completed_after = donation_queryset.latest("completed_at").completed_at - timedelta(minutes=5)

        reward_map = {reward.uuid: reward for reward in Reward.objects.filter(campaign=campaign)}
        reward_ids = set(reward_map.keys())
        while True:
            response = get_donations(campaign.uuid, after=after, completed_after=completed_after)

            not_imported_yet = [x for x in response.data if x.id not in imported_ids]
            # somehow some donations have non-existent rewards?
            to_create.extend([x for x in not_imported_yet if x.reward_id in reward_ids or x.reward_id is None])
            if os.environ.get("DEBUG", "false") == "true":
                if invalid := [
                    x for x in not_imported_yet if x.reward_id not in reward_ids and x.reward_id is not None
                ]:
                    pprint(invalid)
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


def build_donation(campaign: Campaign, reward_map: dict[UUID, Reward], api_donation: schema.Donation):
    return Donation(
        uuid=api_donation.id,
        campaign=campaign,
        amount=api_donation.amount.value,
        name=api_donation.donor_name,
        comment=api_donation.donor_comment,
        completed_at=api_donation.completed_at,
        reward=None if api_donation.reward_id is None else reward_map[api_donation.reward_id],
    )
