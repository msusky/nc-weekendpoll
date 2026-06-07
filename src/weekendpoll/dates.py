"""Date helpers for computing weekends in a range."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

SATURDAY = 5
SUNDAY = 6

ALL_DAY_SECONDS = 86400


def parse_exclusion(value: str) -> tuple[date, date]:
    """Parse one exclusion token into an inclusive (start, end) date range.

    Accepts a single day 'YYYY-MM-DD' or a range 'YYYY-MM-DD:YYYY-MM-DD'.
    A single day is treated as a one-day range.
    """
    parts = value.split(":")
    if len(parts) == 1:
        d = _parse_iso(parts[0])
        return (d, d)
    if len(parts) == 2:
        start = _parse_iso(parts[0])
        end = _parse_iso(parts[1])
        if start > end:
            raise ValueError(
                f"exclusion range start after end: '{value}'"
            )
        return (start, end)
    raise ValueError(
        f"invalid exclusion '{value}', expected DATE or DATE:DATE (YYYY-MM-DD)"
    )


def _parse_iso(value: str) -> date:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"invalid date '{value}', expected YYYY-MM-DD") from None


def _is_excluded(day: date, exclusions: list[tuple[date, date]]) -> bool:
    return any(start <= day <= end for start, end in exclusions)


def weekend_days(
    start: date,
    end: date,
    mode: str = "saturday",
    exclusions: list[tuple[date, date]] | None = None,
) -> list[date]:
    """Return the weekend days between start and end (inclusive).

    mode="saturday": one option per weekend (Saturday only).
    mode="both":     Saturday and Sunday as separate days.

    exclusions: optional list of inclusive (start, end) ranges. Any weekend day
    falling inside one of these ranges is omitted. In "saturday" mode a weekend
    is dropped if its Saturday is excluded; in "both" mode each day is checked
    individually.
    """
    if start > end:
        raise ValueError("start date must not be after end date")
    if mode not in ("saturday", "both"):
        raise ValueError("mode must be 'saturday' or 'both'")
    exclusions = exclusions or []

    days: list[date] = []
    day = start
    while day <= end:
        is_weekend = (
            (mode == "saturday" and day.weekday() == SATURDAY)
            or (mode == "both" and day.weekday() in (SATURDAY, SUNDAY))
        )
        if is_weekend and not _is_excluded(day, exclusions):
            days.append(day)
        day += timedelta(days=1)
    return days


def to_timestamp(d: date) -> int:
    """Midnight of the given day as a Unix timestamp (seconds)."""
    return int(datetime.combine(d, time(0, 0)).timestamp())
