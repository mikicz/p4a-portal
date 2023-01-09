import os
from typing import Optional, Any

import requests
from pydantic import BaseModel

from src.client.schema import CampaignResponse, RewardResponse, PollResponse, DonationResponse

api_token = os.environ.get("TILTIFY_TOKEN")


def _make_request(
    campaign_id: int,
    response_cls: type[BaseModel],
    *,
    sub_url: Optional[str] = None,
    data: Optional[dict[str, Any]] = None,
    print_url: bool = False,
):
    full_url = f"https://tiltify.com/api/v3/campaigns/{campaign_id}/" + (sub_url or "")
    if print_url:
        print(full_url, data)

    response = requests.get(
        full_url,
        params=data,
        headers={"Authorization": "Bearer {}".format(api_token)},
    )
    response.raise_for_status()
    return response_cls.parse_raw(response.content)


def get_campaign(campaign_id: int) -> CampaignResponse:
    return _make_request(campaign_id, CampaignResponse)


def get_rewards(campaign_id: int) -> RewardResponse:
    return _make_request(campaign_id, RewardResponse, sub_url="rewards")


def get_polls(campaign_id: int) -> PollResponse:
    return _make_request(campaign_id, PollResponse, sub_url="polls")


def get_donations(campaign_id: int, before: Optional[int] = None, after: Optional[int] = None) -> DonationResponse:
    data = {"count": 100}
    if before is not None:
        data["before"] = before
    if after is not None:
        data["after"] = after

    return _make_request(campaign_id, DonationResponse, sub_url="donations", data=data, print_url=True)


if __name__ == "__main__":
    id_ = 155357
    print(get_campaign(id_))
    print(get_rewards(id_))
    print(get_polls(id_))
    print(get_donations(id_))
    print(get_donations(id_, before=5706171))
