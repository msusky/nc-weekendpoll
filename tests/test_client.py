"""Tests for the PollsClient list_polls enrichment."""

from unittest.mock import Mock, patch

from weekendpoll.client import PollsClient


def test_list_polls_extracts_nested_fields():
    """list_polls extracts title and created from nested locations in the API response."""
    client = PollsClient("https://example.com", "user", "pw")

    list_response = Mock()
    list_response.status_code = 200
    list_response.json.return_value = {
        "ocs": {"data": {"polls": [
            {
                "id": 1,
                "configuration": {"title": "Poll 1"},
                "status": {"created": 1000},
            },
            {
                "id": 2,
                "title": "Already at root",
                "created": 2000,
            },
        ]}}
    }

    with patch.object(client._session, "get") as mock_get:
        mock_get.return_value = list_response
        polls = client.list_polls()

    assert len(polls) == 2
    # Poll 1: extracted from nested locations
    assert polls[0]["title"] == "Poll 1"
    assert polls[0]["created"] == 1000
    # Poll 2: already at root level
    assert polls[1]["title"] == "Already at root"
    assert polls[1]["created"] == 2000
