import os
from typing import Any
from uuid import UUID

import requests
from pydantic import BaseModel

from src.client.schema import CampaignResponse, DonationResponse, PollResponse, RewardResponse

api_token = os.environ.get("TILTIFY_TOKEN")


def _make_request(
    campaign_uuid: UUID,
    response_cls: type[BaseModel],
    *,
    sub_url: str | None = None,
    data: dict[str, Any] | None = None,
    print_url: bool = False,
):
    full_url = f"https://v5api.tiltify.com/api/public/team_campaigns/{str(campaign_uuid)}/" + (sub_url or "")
    if print_url:
        print(full_url, data)

    response = requests.get(
        full_url,
        params=data,
        headers={"Authorization": f"Bearer {api_token}"},
    )
    response.raise_for_status()
    return response_cls.parse_raw(response.content)


def get_campaign(campaign_uuid: UUID) -> CampaignResponse:
    return _make_request(campaign_uuid, CampaignResponse)


def get_rewards(campaign_uuid: UUID, after: str | None = None) -> RewardResponse:
    data = {"limit": 100}
    if after is not None:
        data["after"] = after
    return _make_request(campaign_uuid, RewardResponse, sub_url="rewards", print_url=True, data=data)


def get_polls(campaign_uuid: UUID, after: str | None = None) -> PollResponse:
    data = {"limit": 100}
    if after is not None:
        data["after"] = after
    return _make_request(campaign_uuid, PollResponse, sub_url="polls", print_url=True, data=data)


def get_donations(campaign_uuid: UUID, after: str | None = None) -> DonationResponse:
    data = {"limit": 100}
    if after is not None:
        data["after"] = after

    return _make_request(campaign_uuid, DonationResponse, sub_url="donations", data=data, print_url=True)


if __name__ == "__main__":
    id_ = 155357
    print(get_campaign(id_))
    print(get_rewards(id_))
    print(get_polls(id_))
    print(get_donations(id_))
    print(get_donations(id_, before=5706171))
