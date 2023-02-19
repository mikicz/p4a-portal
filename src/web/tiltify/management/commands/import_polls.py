from __future__ import annotations

from django.core.management import BaseCommand
from django.utils import timezone

from src.client import schema
from src.client.api import get_polls
from src.web.tiltify.models import Campaign, Option, Poll


class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaign in Campaign.objects.filter(keep_refreshing=True).exclude(uuid=None):
            self.import_polls(campaign)

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
