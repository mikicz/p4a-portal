from uuid import UUID

from src.client import schema
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
