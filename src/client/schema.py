import datetime
from uuid import UUID

import pydantic
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


class Option(BaseTiltifyModel):
    id: int = pydantic.Field(alias="legacy_id")
    name: str
    amount_raised: Amount
    inserted_at: datetime.datetime
    updated_at: datetime.datetime


class Poll(BaseTiltifyModel):
    id: int = pydantic.Field(alias="legacy_id")
    name: str
    active: bool
    inserted_at: datetime.datetime
    updated_at: datetime.datetime
    options: list[Option]


class Donation(BaseTiltifyModel):
    id: UUID
    legacy_id: int
    amount: Amount
    donor_name: str
    donor_comment: str | None
    completed_at: datetime.datetime
    reward_id: UUID | None


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


if __name__ == "__main__":
    response = CampaignResponse.parse_obj(
        {
            "meta": {"status": 200},
            "data": {
                "id": 1,
                "name": "My Awesome Campaign",
                "slug": "my-awesome-campaign",
                "url": "/@username/my-awesome-campaign",
                "startsAt": 1493355600000,
                "endsAt": 1496206800000,
                "description": "My awesome weekend campaign.",
                "avatar": {"src": "https://asdf.cloudfront.net/asdf.jpg", "alt": "", "width": 200, "height": 200},
                "causeId": 17,
                "fundraisingEventId": 39,
                "fundraiserGoalAmount": 10000,
                "originalGoalAmount": 5000,
                "amountRaised": 3402.00,
                "supportingAmountRaised": 8923.00,
                "totalAmountRaised": 12325.00,
                "supportable": True,
                "status": "published",
                "user": {
                    "id": 1,
                    "username": "UserName",
                    "slug": "username",
                    "url": "/@username",
                    "avatar": {"src": "https://asdf.cloudfront.net/asdf.jpg", "alt": "", "width": 200, "height": 200},
                },
                "team": {
                    "id": 1,
                    "username": "Team Name",
                    "slug": "teamslug",
                    "url": "/+teamslug",
                    "avatar": {"src": "https://asdf.cloudfront.net/asdf.jpg", "alt": "", "width": 200, "height": 200},
                },
                "livestream": {"type": "twitch", "channel": "tiltify"},
            },
        }
    )
    print(response)
    response = RewardResponse.parse_obj(
        {
            "meta": {"status": 200},
            "data": [
                {
                    "id": 1,
                    "name": "Fingerstache vhs paleo tattooed echo cold-pressed.",
                    "description": "Chuck Norris can access the DB from the UI.",
                    "amount": 43,
                    "kind": "virtual",
                    "quantity": None,
                    "remaining": None,
                    "fairMarketValue": 88,
                    "currency": "USD",
                    "shippingAddressRequired": False,
                    "shippingNote": None,
                    "image": {
                        "src": "",
                        "alt": "Chuck Norris can access the DB from the UI.",
                        "width": 270,
                        "height": 176,
                    },
                    "active": True,
                    "startsAt": 0,
                    "createdAt": 1498169329000,
                    "updatedAt": 1498249889000,
                }
            ],
        }
    )
    print(response)
    response = PollResponse.parse_obj(
        {
            "data": [
                {
                    "active": True,
                    "amount_raised": {"currency": "USD", "value": "182.32"},
                    "id": "b1fd4188-354b-43c5-8386-3faa753d5877",
                    "inserted_at": "2023-02-06T18:01:06.049521Z",
                    "legacy_id": 124257425,
                    "name": "Learn a TikTok dance live!",
                    "options": [
                        {
                            "amount_raised": {"currency": "USD", "value": "182.32"},
                            "id": "3d895da9-b96f-4cb5-9ab0-504a0c1bf0df",
                            "inserted_at": "2023-02-06T18:01:06.181453Z",
                            "legacy_id": 571780308,
                            "name": "Learn a TikTok dance live!",
                            "updated_at": "2023-02-06T18:01:06.181484Z",
                        },
                        {
                            "amount_raised": {"currency": "USD", "value": "182.32"},
                            "id": "3d895da9-b96f-4cb5-9ab0-504a0c1bf0df",
                            "inserted_at": "2023-02-06T18:01:06.181453Z",
                            "legacy_id": 571780308,
                            "name": "Learn a TikTok dance live!",
                            "updated_at": "2023-02-06T18:01:06.181484Z",
                        },
                        {
                            "amount_raised": {"currency": "USD", "value": "182.32"},
                            "id": "3d895da9-b96f-4cb5-9ab0-504a0c1bf0df",
                            "inserted_at": "2023-02-06T18:01:06.181453Z",
                            "legacy_id": 571780308,
                            "name": "Learn a TikTok dance live!",
                            "updated_at": "2023-02-06T18:01:06.181484Z",
                        },
                    ],
                    "updated_at": "2023-02-06T18:01:06.296875Z",
                }
            ],
            "metadata": {"after": "bGlnaHQgwd==", "before": None, "limit": 10},
        }
    )
    print(response)
    response = DonationResponse.parse_obj(
        {
            "meta": {"status": 200},
            "data": [
                {
                    "id": 21347,
                    "amount": 4.20,
                    "name": "Yoda",
                    "comment": "Judge me by my size, do you?",
                    "completedAt": 1490328000000,
                    "rewardId": 12,
                },
                {
                    "id": 21342,
                    "amount": 1.00,
                    "name": "Me",
                    "comment": "This is an easy Game",
                    "completedAt": 1490327800000,
                },
            ],
            "links": {"prev": "", "next": "", "self": ""},
        }
    )
    print(response)
