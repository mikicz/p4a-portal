import datetime

import ujson as ujson
from pydantic import BaseModel


def to_camel(string: str) -> str:
    def capitalize(word: str, i: int) -> str:
        return word.lower() if i == 0 else word.capitalize()

    return "".join(capitalize(word, i) for i, word in enumerate(string.split("_")))


class BaseTiltifyModel(BaseModel):
    class Config:
        alias_generator = to_camel
        json_loads = ujson.loads
        json_dumps = ujson.dumps


class Meta(BaseTiltifyModel):
    status: int


class Campaign(BaseTiltifyModel):
    id: int
    name: str
    slug: str
    url: str | None
    description: str


class RewardImage(BaseTiltifyModel):
    src: str
    alt: str
    width: int
    height: int


class Reward(BaseTiltifyModel):
    id: int
    name: str
    amount: float
    description: str
    kind: str
    quantity: str | None
    remaining: str | None
    currency: str
    active: bool
    image: RewardImage


class Option(BaseTiltifyModel):
    id: int
    poll_id: int
    name: str
    total_amount_raised: float
    created_at: datetime.datetime
    updated_at: datetime.datetime


class Poll(BaseTiltifyModel):
    id: int
    name: str
    active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    options: list[Option]


class Donation(BaseTiltifyModel):
    id: int
    amount: float
    name: str
    comment: str | None
    completed_at: datetime.datetime
    reward_id: int | None


class Links(BaseTiltifyModel):
    prev: str | None
    next: str | None
    self: str | None


class CampaignResponse(BaseTiltifyModel):
    meta: Meta
    data: Campaign


class RewardResponse(BaseTiltifyModel):
    meta: Meta
    data: list[Reward]


class PollResponse(BaseTiltifyModel):
    meta: Meta
    data: list[Poll]


class DonationResponse(BaseTiltifyModel):
    meta: Meta
    data: list[Donation]
    links: Links


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
            "meta": {"status": 200},
            "data": [
                {
                    "id": 47,
                    "name": "Should pineapple go on pizza?",
                    "active": True,
                    "campaignId": 1337,
                    "createdAt": 1498169329000,
                    "updatedAt": 1498169329000,
                    "options": [
                        {
                            "id": 42,
                            "pollId": 47,
                            "name": "No",
                            "totalAmountRaised": 50,
                            "createdAt": 1498169329000,
                            "updatedAt": 1498169329000,
                        },
                        {
                            "id": 44,
                            "pollId": 47,
                            "name": "Yes",
                            "totalAmountRaised": 50,
                            "createdAt": 1498169329000,
                            "updatedAt": 1498169329000,
                        },
                    ],
                },
            ],
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
