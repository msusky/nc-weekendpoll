"""Tests for URL construction (no network access needed)."""

from weekendpoll.client import PollsClient

BASE = "https://example.nextcloud.hosting.zone"


def _client(**kw):
    return PollsClient(BASE, "user", "pw", **kw)


def test_api_base_uses_ocs():
    c = _client()
    assert c.api == f"{BASE}/ocs/v2.php/apps/polls/api/v1.0"


def test_pretty_urls_by_default():
    c = _client()
    # pretty URLs (default): no /index.php
    assert c.internal_url(3) == f"{BASE}/apps/polls/vote/3"


def test_share_base_pretty():
    c = _client()
    assert c.app_base == f"{BASE}/apps/polls"


def test_index_php_opt_in():
    c = _client(use_index_php=True)
    assert c.internal_url(3) == f"{BASE}/index.php/apps/polls/vote/3"


def test_trailing_slash_stripped():
    c = PollsClient(BASE + "/", "user", "pw")
    assert c.internal_url(3) == f"{BASE}/apps/polls/vote/3"
