"""Integration tests against a live Nextcloud instance with the Polls app.

These are SKIPPED unless the following environment variables are set, so the
normal `pytest` run stays fully offline:

    WEEKENDPOLL_IT_URL       base URL of a running Nextcloud
    WEEKENDPOLL_IT_USER      admin/login name
    WEEKENDPOLL_IT_PASSWORD  password or app password

The CI workflow (.github/workflows/integration.yml) starts a Nextcloud
container, installs the Polls app, and sets these variables. The tests verify
the full round-trip: create a poll, configure it, add date options, create a
public share, then delete the poll.
"""

from __future__ import annotations

import os
from datetime import date

import pytest

from weekendpoll.client import PollsClient
from weekendpoll.dates import ALL_DAY_SECONDS, to_timestamp, weekend_days

IT_URL = os.environ.get("WEEKENDPOLL_IT_URL")
IT_USER = os.environ.get("WEEKENDPOLL_IT_USER")
IT_PASSWORD = os.environ.get("WEEKENDPOLL_IT_PASSWORD")

pytestmark = pytest.mark.skipif(
    not (IT_URL and IT_USER and IT_PASSWORD),
    reason="integration env vars not set (WEEKENDPOLL_IT_URL/USER/PASSWORD)",
)


@pytest.fixture
def client() -> PollsClient:
    return PollsClient(IT_URL, IT_USER, IT_PASSWORD)


@pytest.fixture
def temp_poll(client: PollsClient):
    """Create a poll for a test and always delete it afterwards."""
    poll_id = client.create_poll("weekendpoll integration test")
    try:
        yield poll_id
    finally:
        try:
            client.delete_poll(poll_id)
        except Exception:
            pass


def test_create_configure_and_list(client: PollsClient, temp_poll: int):
    client.configure_poll(temp_poll, {
        "description": "integration",
        "access": "open",
        "allowProposals": "allow",
        "allowComment": True,
        "allowMaybe": True,
        "anonymous": False,
    })
    poll = client.get_poll(temp_poll)
    assert int(poll.get("id")) == temp_poll

    ids = [int(p.get("id")) for p in client.list_polls()]
    assert temp_poll in ids


def test_add_date_options(client: PollsClient, temp_poll: int):
    days = weekend_days(date(2026, 7, 1), date(2026, 7, 31), "saturday")
    for d in days:
        result = client.add_date_option(temp_poll, to_timestamp(d), ALL_DAY_SECONDS)
        assert result in ("added", "exists")
    # adding the same option again must be reported as existing, not error
    again = client.add_date_option(temp_poll, to_timestamp(days[0]), ALL_DAY_SECONDS)
    assert again == "exists"


def test_public_share(client: PollsClient, temp_poll: int):
    link = client.create_public_share(temp_poll)
    assert link is not None
    assert "/apps/polls/s/" in link


def test_delete_poll(client: PollsClient):
    poll_id = client.create_poll("weekendpoll delete test")
    client.delete_poll(poll_id)
    with pytest.raises(Exception):
        client.get_poll(poll_id)
