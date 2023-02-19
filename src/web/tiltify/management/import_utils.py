from uuid import UUID

from django.utils import timezone

from src.client import schema
from src.client.api import get_campaign, get_rewards
from src.web.tiltify.models import Campaign, Donation, Reward


def build_donation(campaign: Campaign, reward_map: dict[UUID, Reward], api_donation: schema.Donation):
    reward = None
    if api_donation.reward_id is not None:
        try:
            reward = reward_map[api_donation.reward_id]
        except KeyError:
            reward, _ = Reward.objects.get_or_create(
                uuid=api_donation.reward_id, campaign=campaign, defaults={"missing": True}
            )
            reward_map[api_donation.reward_id] = reward

    return Donation(
        uuid=api_donation.id,
        campaign=campaign,
        amount=api_donation.amount.value,
        name=api_donation.donor_name,
        comment=api_donation.donor_comment,
        completed_at=api_donation.completed_at,
        reward=reward,
    )


def import_rewards(campaign: Campaign):
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


def import_campaign_details(campaign: Campaign):
    print("Importing campaign details")
    c: schema.Campaign = get_campaign(campaign.uuid).data
    campaign.name = c.name
    campaign.slug = c.slug
    if c.team is not None and c.team.slug is not None:
        campaign.url = f"+{c.team.slug}/{c.slug}/"
    campaign.description = c.description
    campaign.supportable = c.retired_at is None or c.retired_at > timezone.now()
    campaign.published_at = c.published_at
    campaign.retired_at = c.retired_at
    campaign.save()
