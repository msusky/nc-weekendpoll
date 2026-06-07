"""Tests for the date logic. These run without any network access."""

from datetime import date

import pytest

from weekendpoll.dates import parse_exclusion, to_timestamp, weekend_days


def test_saturdays_only():
    days = weekend_days(date(2026, 7, 1), date(2026, 7, 31), "saturday")
    assert days == [
        date(2026, 7, 4),
        date(2026, 7, 11),
        date(2026, 7, 18),
        date(2026, 7, 25),
    ]
    assert all(d.weekday() == 5 for d in days)


def test_both_days():
    days = weekend_days(date(2026, 7, 1), date(2026, 7, 12), "both")
    assert days == [
        date(2026, 7, 4),
        date(2026, 7, 5),
        date(2026, 7, 11),
        date(2026, 7, 12),
    ]


def test_full_half_year_count():
    # Jul-Dec 2026 has 26 Saturdays
    days = weekend_days(date(2026, 7, 1), date(2026, 12, 31), "saturday")
    assert len(days) == 26


def test_empty_range_without_weekend():
    # Mon-Fri only
    days = weekend_days(date(2026, 7, 6), date(2026, 7, 10), "saturday")
    assert days == []


def test_start_after_end_raises():
    with pytest.raises(ValueError):
        weekend_days(date(2026, 7, 10), date(2026, 7, 1), "saturday")


def test_invalid_mode_raises():
    with pytest.raises(ValueError):
        weekend_days(date(2026, 7, 1), date(2026, 7, 31), "sunday")


def test_to_timestamp_is_midnight():
    ts = to_timestamp(date(2026, 7, 4))
    assert isinstance(ts, int)
    assert ts > 0


def test_exclude_single_day():
    ex = [parse_exclusion("2026-07-11")]
    days = weekend_days(date(2026, 7, 1), date(2026, 7, 31), "saturday", ex)
    assert date(2026, 7, 11) not in days
    assert date(2026, 7, 4) in days
    assert len(days) == 3


def test_exclude_range():
    ex = [parse_exclusion("2026-07-10:2026-07-20")]
    days = weekend_days(date(2026, 7, 1), date(2026, 7, 31), "saturday", ex)
    # 11 and 18 fall in the range
    assert date(2026, 7, 11) not in days
    assert date(2026, 7, 18) not in days
    assert days == [date(2026, 7, 4), date(2026, 7, 25)]


def test_exclude_multiple():
    ex = [parse_exclusion("2026-07-04"), parse_exclusion("2026-07-25")]
    days = weekend_days(date(2026, 7, 1), date(2026, 7, 31), "saturday", ex)
    assert days == [date(2026, 7, 11), date(2026, 7, 18)]


def test_exclude_both_mode_individual_days():
    # exclude only Sunday 2026-07-05; its Saturday 07-04 should remain
    ex = [parse_exclusion("2026-07-05")]
    days = weekend_days(date(2026, 7, 1), date(2026, 7, 6), "both", ex)
    assert date(2026, 7, 4) in days
    assert date(2026, 7, 5) not in days


def test_parse_exclusion_single():
    assert parse_exclusion("2026-07-04") == (date(2026, 7, 4), date(2026, 7, 4))


def test_parse_exclusion_range():
    assert parse_exclusion("2026-07-01:2026-07-31") == (
        date(2026, 7, 1), date(2026, 7, 31))


def test_parse_exclusion_bad_format():
    with pytest.raises(ValueError):
        parse_exclusion("2026/07/04")


def test_parse_exclusion_range_reversed():
    with pytest.raises(ValueError):
        parse_exclusion("2026-07-31:2026-07-01")
