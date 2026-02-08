import datetime
from uuid import UUID

import ujson as ujson
from pydantic import BaseModel


class BaseTiltifyModel(BaseModel):
    class Config:
        json_loads = ujson.loads
        json_dumps = ujson.dumps


class Metadata(BaseTiltifyModel):
    limit: int
    before: str | None
    after: str | None


class Team(BaseTiltifyModel):
    slug: str


class Campaign(BaseTiltifyModel):
    id: UUID
    name: str
    slug: str
    url: str | None
    description: str
    team: Team | None
    published_at: datetime.datetime | None
    retired_at: datetime.datetime | None


class RewardImage(BaseTiltifyModel):
    src: str
    alt: str
    width: int
    height: int


class Amount(BaseTiltifyModel):
    currency: str
    value: float


class Reward(BaseTiltifyModel):
    id: UUID
    legacy_id: int
    name: str
    amount: Amount
    description: str
    # kind: str
    quantity: int | None
    quantity_remaining: int | None
    active: bool
    image: RewardImage
    inserted_at: datetime.datetime | None
    starts_at: datetime.datetime | None
    ends_at: datetime.datetime | None
    updated_at: datetime.datetime | None


class Option(BaseTiltifyModel):
    id: UUID
    name: str
    amount_raised: Amount
    inserted_at: datetime.datetime
    updated_at: datetime.datetime


class Poll(BaseTiltifyModel):
    id: UUID
    name: str
    active: bool
    inserted_at: datetime.datetime
    updated_at: datetime.datetime
    options: list[Option]


class RewardClaim(BaseTiltifyModel):
    id: UUID
    quantity: int
    reward_id: UUID | None
    custom_question: str | None


class Donation(BaseTiltifyModel):
    id: UUID
    legacy_id: int
    amount: Amount
    donor_name: str
    donor_comment: str | None
    completed_at: datetime.datetime
    reward_claims: list[RewardClaim] | None
    poll_id: UUID | None
    poll_option_id: UUID | None


class WebhookMeta(BaseTiltifyModel):
    id: UUID
    event_type: str
    generated_at: datetime.datetime
    attempted_at: datetime.datetime
    subscription_source_id: UUID
    subscription_source_type: str


class WebhookDonationData(Donation):
    campaign_id: UUID
    cause_id: UUID | None
    created_at: datetime.datetime
    email: str | None
    fundraising_event_id: UUID | None
    reward_custom_question: str | None
    reward_id: UUID | None
    sustained: bool
    target_id: UUID | None
    team_event_id: UUID | None


class DonationWebhook(BaseTiltifyModel):
    data: WebhookDonationData
    meta: WebhookMeta


class DonationList(BaseTiltifyModel):
    donations: list[Donation]


class Links(BaseTiltifyModel):
    prev: str | None
    next: str | None
    self: str | None


class CampaignResponse(BaseTiltifyModel):
    data: Campaign


class RewardResponse(BaseTiltifyModel):
    metadata: Metadata
    data: list[Reward]


class PollResponse(BaseTiltifyModel):
    metadata: Metadata
    data: list[Poll]


class DonationResponse(BaseTiltifyModel):
    metadata: Metadata
    data: list[Donation]
