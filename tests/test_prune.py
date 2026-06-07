"""Tests for list/prune helper logic (no network access needed)."""

import time

from weekendpoll.cli import _format_poll_row, _is_owned, _poll_age_days


def test_age_days_from_created():
    now = time.time()
    poll = {"created": now - 10 * 86400}
    age = _poll_age_days(poll, now)
    assert age is not None
    assert round(age) == 10


def test_age_none_when_missing():
    assert _poll_age_days({}, time.time()) is None


def test_is_owned_true():
    assert _is_owned({"currentUserStatus": {"isOwner": True}}) is True


def test_is_owned_false_or_missing():
    assert _is_owned({"currentUserStatus": {"isOwner": False}}) is False
    assert _is_owned({}) is False


def test_format_row_contains_id_and_title():
    row = _format_poll_row(
        {"id": 3, "title": "Test poll",
         "currentUserStatus": {"isOwner": True}},
        12.0,
    )
    assert "3" in row
    assert "Test poll" in row
    assert "you" in row


def test_format_row_missing_fields():
    # When fields are missing from the list response, show defaults
    row = _format_poll_row({"id": 5}, None)
    assert "[   5]" in row
    assert "?" in row  # age is missing
    assert "(untitled)" in row  # title is missing
