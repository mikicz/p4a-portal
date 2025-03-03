from uuid import UUID

from django.utils import timezone

from src.client import schema
from src.client.api import get_authenticated_session, get_campaign, get_rewards
from src.web.tiltify.models import Campaign, Donation, Reward, RewardClaim


def build_donation(
    campaign: Campaign,
    reward_map: dict[UUID, Reward],
    api_donation: schema.Donation,
    polls: set[UUID],
    options: set[UUID],
) -> tuple[Donation, list[RewardClaim]]:
    reward_claims = []

    for reward_claim in api_donation.reward_claims or []:
        try:
            reward = reward_map[reward_claim.reward_id]
        except KeyError:
            reward, _ = Reward.objects.get_or_create(
                uuid=reward_claim.reward_id,
                campaign=campaign,
                defaults={"missing": True},
            )
            reward_map[reward_claim.reward_id] = reward
        reward_claims.append(
            RewardClaim(
                id=reward_claim.id,
                reward=reward,
                quantity=reward_claim.quantity,
                donation_id=api_donation.id,
            )
        )

    poll_id = None if api_donation.poll_id is None or api_donation.poll_id not in polls else api_donation.poll_id
    option_id = (
        None
        if api_donation.poll_option_id is None or api_donation.poll_option_id not in options
        else api_donation.poll_option_id
    )

    donation = Donation(
        id=api_donation.id,
        campaign=campaign,
        amount=api_donation.amount.value,
        name=api_donation.donor_name,
        comment=api_donation.donor_comment,
        completed_at=api_donation.completed_at,
        poll_id=poll_id,
        poll_option_id=option_id,
    )

    return donation, reward_claims


def create_donations_and_reward_claims(
    *,
    campaign: Campaign,
    to_create: list[schema.Donation],
    reward_map: dict[UUID, Reward],
    currently_donations_created: int,
    currently_reward_claims_created: int,
    polls: set[UUID],
    options: set[UUID],
) -> tuple[int, int]:
    donations_to_create = []
    reward_claims_to_create = []

    for api_donation in to_create:
        x, y = build_donation(campaign, reward_map, api_donation, polls, options)
        donations_to_create.append(x)
        reward_claims_to_create.extend(y)

    currently_donations_created += len(Donation.objects.bulk_create(donations_to_create, ignore_conflicts=True))
    currently_reward_claims_created += len(
        RewardClaim.objects.bulk_create(reward_claims_to_create, ignore_conflicts=True)
    )

    return currently_donations_created, currently_reward_claims_created


def import_rewards(campaign: Campaign):
    print("Importing rewards details")
    with get_authenticated_session() as session:
        rewards = []
        after = None
        while True:
            rewards_response = get_rewards(session, campaign.uuid, after=after)
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
                "inserted_at": reward.inserted_at,
                "starts_at": reward.starts_at,
                "ends_at": reward.ends_at,
                "updated_at": reward.updated_at,
            },
        )


def import_campaign_details(campaign: Campaign):
    print("Importing campaign details")
    with get_authenticated_session() as session:
        c: schema.Campaign = get_campaign(session, campaign.uuid).data
    campaign.name = c.name
    campaign.slug = c.slug
    if c.team is not None and c.team.slug is not None:
        campaign.url = f"+{c.team.slug}/{c.slug}/"
    campaign.description = c.description
    campaign.supportable = c.retired_at is None or c.retired_at > timezone.now()
    campaign.published_at = c.published_at
    campaign.retired_at = c.retired_at
    campaign.save()
