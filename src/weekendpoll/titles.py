"""Title suggestions for new weekend polls."""

from __future__ import annotations

from datetime import date


def suggest_titles(start: date, end: date) -> list[str]:
    """Return a list of human-friendly title suggestions for the range."""
    return [
        "Let's find a weekend that works for everyone",
        f"Weekend meetup {start.year}: when are you free?",
        "Find our free weekend",
        f"Weekend planning {start.strftime('%b')}-{end.strftime('%b %Y')}",
        "When do we all have time? (weekend poll)",
    ]
