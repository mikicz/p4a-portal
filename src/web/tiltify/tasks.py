from uuid import UUID

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.tasks import task

from src.client.schema import DonationWebhook, WebhookDonationData
from src.web.tiltify.management.commands.import_polls import import_polls
from src.web.tiltify.management.import_utils import build_donation, import_rewards
from src.web.tiltify.models import Campaign, Donation, Option, Poll, Reward, RewardClaim


def get_reward_map(campaign: Campaign, donation: WebhookDonationData) -> dict[UUID, Reward]:
    reward_ids = set()
    if donation.reward_id:
        reward_ids.add(donation.reward_id)
    if donation.reward_claims:
        for reward_claim in donation.reward_claims:
            if reward_claim.reward_id is None:
                continue
            reward_ids.add(reward_claim.reward_id)

    if not reward_ids:
        return {}

    reward_map = Reward.objects.filter(campaign=campaign).in_bulk(reward_ids, field_name="uuid")

    if len(reward_map) != len(reward_ids):
        import_rewards(campaign)

    return Reward.objects.filter(campaign=campaign).in_bulk(reward_ids, field_name="uuid")


def get_polls_and_options(campaign: Campaign, donation: WebhookDonationData) -> tuple[set[int], set[int]]:
    polls = set(Poll.objects.filter(campaign=campaign).values_list("id", flat=True))
    options = set(Option.objects.filter(poll__campaign=campaign).values_list("id", flat=True))

    if (donation.poll_id and donation.poll_id not in polls) or (
        donation.poll_option_id and donation.poll_option_id not in options
    ):
        import_polls(campaign)
        polls = set(Poll.objects.filter(campaign=campaign).values_list("id", flat=True))
        options = set(Option.objects.filter(poll__campaign=campaign).values_list("id", flat=True))

    return polls, options


@task
def process_webhook_task(data: str) -> None:
    webhook = DonationWebhook.parse_raw(data)
    result = {
        "campaign_id": str(webhook.data.campaign_id) if webhook.data.campaign_id else None,
        "donation_id": str(webhook.data.id),
    }

    if webhook.data.campaign_id is None:
        # We do not have a campaign ID in the webhook, so let's see if there's a singular compaign
        # that is supposed to be refreshed, and use that if there is one
        try:
            campaign = Campaign.objects.get(keep_refreshing=True)
        except ObjectDoesNotExist, MultipleObjectsReturned:
            return result | {"error": "Campaign ID empty"}
    else:
        try:
            campaign = Campaign.objects.get(uuid=webhook.data.campaign_id, keep_refreshing=True)
        except ObjectDoesNotExist:
            return result | {"error": "Campaign not found"}

    if Donation.objects.filter(campaign=campaign, id=webhook.data.id).exists():
        return result | {"error": "Donation already exists"}

    reward_map = get_reward_map(campaign, webhook.data)
    polls, options = get_polls_and_options(campaign, webhook.data)

    donation_to_create, reward_claims_to_create = build_donation(
        campaign, reward_map, webhook.data, polls, options, loaded_from_webhook=True
    )

    currently_donations_created = Donation.objects.bulk_create([donation_to_create], ignore_conflicts=True)
    currently_reward_claims_created = RewardClaim.objects.bulk_create(reward_claims_to_create, ignore_conflicts=True)

    return result | {
        "currently_donations_created": len(currently_donations_created),
        "currently_reward_claims_created": len(currently_reward_claims_created),
    }
