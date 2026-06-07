"""Thin client for the Nextcloud Polls OCS API.

Verified against Polls v9.1.1 (OCS API v1.0). The endpoint paths and payload
shapes below were checked against the app's controllers for that release:

  - POST /poll                      add(type, title)
  - PUT  /poll/{id}                 update(pollId, pollConfiguration={...})
  - POST /poll/{id}/option          add(pollId, option={...})   <- option is nested
  - POST /poll/{id}/share/{type}    add(pollId, type)           <- type is in the URL
  - GET  /poll/{id}                 get(pollId)

All endpoints live under /ocs/v2.php/apps/polls/api/v1.0 and require the
`OCS-APIRequest: true` header. Responses are wrapped in {"ocs": {"data": ...}}.
"""

from __future__ import annotations

import requests


class PollsError(RuntimeError):
    """Raised when the Polls API returns an unexpected status."""


class PollsClient:
    """Minimal authenticated client for the Nextcloud Polls API."""

    def __init__(self, base_url: str, username: str, app_password: str,
                 timeout: int = 30, use_index_php: bool = False) -> None:
        self.base_url = base_url.rstrip("/")
        # OCS API endpoints always live under /ocs/v2.php, regardless of
        # whether the instance uses pretty URLs for the web UI.
        self.api = f"{self.base_url}/ocs/v2.php/apps/polls/api/v1.0"
        # Web-UI links: most instances use pretty URLs (no /index.php).
        # Set use_index_php=True for instances that require the index.php prefix.
        prefix = "/index.php" if use_index_php else ""
        self.app_base = f"{self.base_url}{prefix}/apps/polls"
        self.timeout = timeout
        self._session = requests.Session()
        self._session.auth = (username, app_password)
        self._session.headers.update({
            "Content-Type": "application/json;charset=utf-8",
            "Accept": "application/json",
            "OCS-APIRequest": "true",
        })

    # -- helpers --------------------------------------------------------

    @staticmethod
    def _unwrap(resp: requests.Response):
        """Return the payload inside the OCS envelope, or the raw JSON."""
        try:
            data = resp.json()
        except ValueError:
            return None
        if isinstance(data, dict) and "ocs" in data:
            return data["ocs"].get("data")
        return data

    def _check(self, resp: requests.Response, ok=(200, 201), action: str = "") -> None:
        if resp.status_code == 401:
            raise PollsError("Authentication failed - check username / app password.")
        if resp.status_code not in ok:
            raise PollsError(
                f"{action or 'Request'} failed: HTTP {resp.status_code} "
                f"{resp.text[:200]}"
            )

    # -- API calls ------------------------------------------------------

    def get_poll(self, poll_id: int) -> dict:
        resp = self._session.get(f"{self.api}/poll/{poll_id}", timeout=self.timeout)
        if resp.status_code == 404:
            raise PollsError(f"Poll {poll_id} not found.")
        self._check(resp, action="Get poll")
        data = self._unwrap(resp) or {}
        return data.get("poll", data)

    def list_polls(self) -> list[dict]:
        """Return all polls visible to the authenticated user."""
        resp = self._session.get(f"{self.api}/polls", timeout=self.timeout)
        self._check(resp, action="List polls")
        data = self._unwrap(resp) or {}
        return data.get("polls", [])

    def delete_poll(self, poll_id: int) -> None:
        resp = self._session.delete(f"{self.api}/poll/{poll_id}", timeout=self.timeout)
        if resp.status_code == 404:
            raise PollsError(f"Poll {poll_id} not found.")
        self._check(resp, action="Delete poll")

    def create_poll(self, title: str, poll_type: str = "datePoll") -> int:
        resp = self._session.post(
            f"{self.api}/poll",
            json={"type": poll_type, "title": title},
            timeout=self.timeout,
        )
        self._check(resp, action="Create poll")
        data = self._unwrap(resp) or {}
        poll = data.get("poll", data)
        poll_id = poll.get("id")
        if not poll_id:
            raise PollsError(f"Create poll returned no id: {resp.text[:200]}")
        return int(poll_id)

    def configure_poll(self, poll_id: int, config: dict) -> None:
        # v9: body key is "pollConfiguration"
        resp = self._session.put(
            f"{self.api}/poll/{poll_id}",
            json={"pollConfiguration": config},
            timeout=self.timeout,
        )
        self._check(resp, action="Configure poll")

    def add_date_option(self, poll_id: int, timestamp: int, duration: int = 0) -> str:
        """Add one date option. Returns 'added' or 'exists'."""
        resp = self._session.post(
            f"{self.api}/poll/{poll_id}/option",
            json={"option": {"timestamp": timestamp, "duration": duration}},
            timeout=self.timeout,
        )
        if resp.status_code == 409:
            return "exists"
        self._check(resp, action="Add option")
        return "added"

    def create_public_share(self, poll_id: int) -> str | None:
        """Create a public share and return the full share URL, or None."""
        # v9: share type is part of the URL, not the body
        resp = self._session.post(
            f"{self.api}/poll/{poll_id}/share/public",
            json={},
            timeout=self.timeout,
        )
        self._check(resp, action="Create public share")
        data = self._unwrap(resp) or {}
        share = data.get("share", data)
        token = share.get("token")
        if not token:
            return None
        return f"{self.app_base}/s/{token}"

    def internal_url(self, poll_id: int) -> str:
        return f"{self.app_base}/vote/{poll_id}"
