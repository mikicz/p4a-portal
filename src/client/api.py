import contextlib
import os
from collections.abc import Generator
from datetime import datetime
from typing import Any
from uuid import UUID

import requests
from pydantic import BaseModel
from requests.adapters import HTTPAdapter, Retry

from src.client.schema import CampaignResponse, DonationResponse, PollResponse, RewardResponse

api_token = os.environ.get("TILTIFY_TOKEN")


@contextlib.contextmanager
def get_authenticated_session() -> Generator[requests.Session, None, None]:
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504, 429])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    session.headers.update({"Authorization": f"Bearer {api_token}"})

    yield session


def _make_request(
    session: requests.Session,
    campaign_uuid: UUID,
    response_cls: type[BaseModel],
    *,
    sub_url: str | None = None,
    data: dict[str, Any] | None = None,
    print_url: bool = False,
):
    full_url = f"https://v5api.tiltify.com/api/public/team_campaigns/{campaign_uuid!s}/" + (sub_url or "")
    if print_url:
        print(full_url, data)

    response = session.get(full_url, params=data)
    response.raise_for_status()
    return response_cls.parse_raw(response.content)


def get_campaign(session: requests.Session, campaign_uuid: UUID) -> CampaignResponse:
    return _make_request(session, campaign_uuid, CampaignResponse)


def get_rewards(session: requests.Session, campaign_uuid: UUID, after: str | None = None) -> RewardResponse:
    data = {"limit": 100}
    if after is not None:
        data["after"] = after
    return _make_request(session, campaign_uuid, RewardResponse, sub_url="rewards", print_url=True, data=data)


def get_polls(session: requests.Session, campaign_uuid: UUID, after: str | None = None) -> PollResponse:
    data = {"limit": 100}
    if after is not None:
        data["after"] = after
    return _make_request(session, campaign_uuid, PollResponse, sub_url="polls", print_url=True, data=data)


def get_donations(
    session: requests.Session, campaign_uuid: UUID, after: str | None = None, completed_after: datetime | None = None
) -> DonationResponse:
    data = {"limit": 100}
    if after is not None:
        data["after"] = after
    if completed_after is not None:
        data["completed_after"] = completed_after.isoformat()

    return _make_request(session, campaign_uuid, DonationResponse, sub_url="donations", data=data, print_url=True)


if __name__ == "__main__":
    id_ = "dd353610-992e-4050-bb34-0d1f7ee6e0f3"
    # print(get_campaign(id_))
    # print(get_rewards(id_))
    # print(get_polls(id_))
    with get_authenticated_session() as sesh:
        print(get_donations(sesh, id_))
    # print(get_donations(id_, before=5706171))
