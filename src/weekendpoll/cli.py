"""weekendpoll command-line interface.

Create and fill Nextcloud Polls date polls for finding a free weekend
among several people, then print a public share link.

Credentials are read from (in order of precedence):
  1. command-line flags  --url / --user / --password
  2. environment vars    WEEKENDPOLL_URL / WEEKENDPOLL_USER / WEEKENDPOLL_PASSWORD

Use a Nextcloud *app password*, never your account password
(Settings -> Security -> Create new app password).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import date, datetime

from . import __version__
from .client import PollsClient, PollsError
from .dates import ALL_DAY_SECONDS, parse_exclusion, to_timestamp, weekend_days
from .titles import suggest_titles


# ----------------------------------------------------------------------
# argument parsing
# ----------------------------------------------------------------------

def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"invalid date '{value}', expected YYYY-MM-DD"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weekendpoll",
        description="Create and fill a Nextcloud Polls date poll with weekends.",
    )
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")

    # shared connection flags
    conn = argparse.ArgumentParser(add_help=False)
    conn.add_argument("-U", "--url", help="Nextcloud base URL "
                      "(or env WEEKENDPOLL_URL)")
    conn.add_argument("-u", "--user", help="Nextcloud login name "
                      "(or env WEEKENDPOLL_USER)")
    conn.add_argument("-p", "--password", help="Nextcloud app password "
                      "(or env WEEKENDPOLL_PASSWORD)")
    conn.add_argument("-I", "--index-php", action="store_true",
                      help="use /index.php in web-UI links (only needed on "
                           "instances without pretty URLs)")

    sub = parser.add_subparsers(dest="command", required=True)

    # create: make a new poll and fill it
    c = sub.add_parser("create", parents=[conn],
                       help="create a new weekend poll and fill it")
    _add_range_args(c)
    c.add_argument("-t", "--title", help="poll title (omit to choose from suggestions)")
    c.add_argument("-d", "--description", default=(
        "Please mark the weekends you are available. "
        "Feel free to propose your own dates."),
        help="poll description")
    _add_permission_args(c)
    c.add_argument("-S", "--no-share", action="store_true",
                   help="do not create a public share link")
    c.add_argument("-y", "--yes", action="store_true",
                   help="skip the confirmation prompt")
    c.set_defaults(func=cmd_create)

    # fill: add weekends to an existing poll
    f = sub.add_parser("fill", parents=[conn],
                       help="add weekends to an existing poll")
    f.add_argument("poll_id", type=int, help="ID of the existing poll")
    _add_range_args(f)
    _add_permission_args(f)
    f.add_argument("-N", "--no-config", action="store_true",
                   help="do not touch the poll's configuration")
    f.add_argument("-y", "--yes", action="store_true",
                   help="skip the confirmation prompt")
    f.set_defaults(func=cmd_fill)

    # share: create a public link for an existing poll
    s = sub.add_parser("share", parents=[conn],
                       help="create a public share link for a poll")
    s.add_argument("poll_id", type=int, help="ID of the existing poll")
    s.set_defaults(func=cmd_share)

    # list: show polls
    li = sub.add_parser("list", parents=[conn],
                        help="list polls visible to you")
    li.add_argument("-i", "--mine", action="store_true",
                    help="show only polls you own")
    li.set_defaults(func=cmd_list)

    # prune: delete polls older than N days
    pr = sub.add_parser("prune", parents=[conn],
                        help="delete polls older than a given age")
    pr.add_argument("-o", "--older-than", type=int, required=True, metavar="DAYS",
                    help="delete polls created more than DAYS days ago")
    pr.add_argument("-i", "--mine", action="store_true",
                    help="only consider polls you own (recommended)")
    pr.add_argument("-y", "--yes", action="store_true",
                    help="skip the confirmation prompt")
    pr.set_defaults(func=cmd_prune)

    return parser


def _add_range_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("-s", "--start", type=_parse_date, required=True,
                   help="range start, YYYY-MM-DD (inclusive)")
    p.add_argument("-e", "--end", type=_parse_date, required=True,
                   help="range end, YYYY-MM-DD (inclusive)")
    p.add_argument("-m", "--mode", choices=("saturday", "both"), default="saturday",
                   help="'saturday' = one option per weekend; "
                        "'both' = Saturday and Sunday separately")
    p.add_argument("-T", "--timed", action="store_true",
                   help="create timed options instead of all-day")
    p.add_argument("-x", "--exclude", action="append", default=[],
                   metavar="DATE[:DATE]",
                   help="exclude a date or an inclusive range "
                        "(YYYY-MM-DD or YYYY-MM-DD:YYYY-MM-DD); "
                        "repeatable for multiple exclusions")


def _add_permission_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("-P", "--no-proposals", action="store_true",
                   help="do not let participants propose their own dates")
    p.add_argument("-C", "--no-comments", action="store_true",
                   help="disable comments")
    p.add_argument("-M", "--no-maybe", action="store_true",
                   help="disable the 'maybe' option")
    p.add_argument("-A", "--anonymous", action="store_true",
                   help="pseudonymise participant names")


# ----------------------------------------------------------------------
# credential resolution
# ----------------------------------------------------------------------

def _resolve_client(args) -> PollsClient:
    url = args.url or os.environ.get("WEEKENDPOLL_URL")
    user = args.user or os.environ.get("WEEKENDPOLL_USER")
    password = args.password or os.environ.get("WEEKENDPOLL_PASSWORD")
    missing = [n for n, v in
               (("url", url), ("user", user), ("password", password)) if not v]
    if missing:
        raise PollsError(
            "Missing credentials: " + ", ".join(missing) +
            ". Pass --url/--user/--password or set "
            "WEEKENDPOLL_URL/WEEKENDPOLL_USER/WEEKENDPOLL_PASSWORD."
        )
    return PollsClient(url, user, password,
                       use_index_php=bool(getattr(args, "index_php", False)))


def _build_config(args) -> dict:
    return {
        "description": getattr(args, "description", None) or "",
        "access": "open",
        "allowProposals": "disallow" if args.no_proposals else "allow",
        "allowComment": not args.no_comments,
        "allowMaybe": not args.no_maybe,
        "anonymous": bool(args.anonymous),
    }


def _choose_title(args) -> str:
    if getattr(args, "title", None):
        return args.title
    suggestions = suggest_titles(args.start, args.end)
    print("\nTitle suggestions:")
    for i, t in enumerate(suggestions, 1):
        print(f"  {i}) {t}")
    print("  0) enter your own")
    choice = input("Choice [1]: ").strip() or "1"
    if choice == "0":
        return input("Title: ").strip() or suggestions[0]
    try:
        return suggestions[int(choice) - 1]
    except (ValueError, IndexError):
        return suggestions[0]


def _preview_and_confirm(args, days, *, header: str) -> bool:
    print(f"\n{header}")
    print(f"Range : {args.start.isoformat()} to {args.end.isoformat()}")
    print(f"Mode  : {args.mode} ({'timed' if args.timed else 'all-day'})")
    print(f"Count : {len(days)} weekend option(s):\n")
    for d in days:
        print(f"   {d.strftime('%a %d %b %Y')}")
    if args.yes:
        return True
    return input("\nProceed? [y/N] ").strip().lower() in ("y", "yes")


def _fill_dates(client: PollsClient, poll_id: int, days, timed: bool) -> tuple[int, int]:
    duration = 0 if timed else ALL_DAY_SECONDS
    added = skipped = 0
    for d in days:
        result = client.add_date_option(poll_id, to_timestamp(d), duration)
        if result == "added":
            added += 1
            print(f"  + {d.isoformat()}")
        else:
            skipped += 1
    return added, skipped


# ----------------------------------------------------------------------
# subcommand handlers
# ----------------------------------------------------------------------

def _resolve_exclusions(args) -> list:
    """Parse --exclude tokens into (start, end) ranges, raising PollsError
    with a friendly message on bad input."""
    ranges = []
    for token in getattr(args, "exclude", []) or []:
        try:
            ranges.append(parse_exclusion(token))
        except ValueError as exc:
            raise PollsError(str(exc)) from None
    return ranges


def cmd_create(args) -> int:
    client = _resolve_client(args)
    exclusions = _resolve_exclusions(args)
    days = weekend_days(args.start, args.end, args.mode, exclusions)
    if not days:
        print("No weekend days in that range (after exclusions).",
              file=sys.stderr)
        return 1
    title = _choose_title(args)
    if not _preview_and_confirm(args, days, header=f"New poll: {title!r}"):
        print("Aborted.")
        return 1

    poll_id = client.create_poll(title)
    print(f"Created poll - ID {poll_id}")
    client.configure_poll(poll_id, _build_config(args))
    added, skipped = _fill_dates(client, poll_id, days, args.timed)

    print(f"\nDone. {added} added, {skipped} skipped.")
    print(f"Internal : {client.internal_url(poll_id)}")
    if not args.no_share:
        link = client.create_public_share(poll_id)
        if link:
            print(f"Share    : {link}")
    return 0


def cmd_fill(args) -> int:
    client = _resolve_client(args)
    exclusions = _resolve_exclusions(args)
    days = weekend_days(args.start, args.end, args.mode, exclusions)
    if not days:
        print("No weekend days in that range (after exclusions).",
              file=sys.stderr)
        return 1
    client.get_poll(args.poll_id)  # validates existence / access
    if not _preview_and_confirm(args, days,
                                header=f"Fill existing poll {args.poll_id}"):
        print("Aborted.")
        return 1
    if not args.no_config:
        client.configure_poll(args.poll_id, _build_config(args))
    added, skipped = _fill_dates(client, args.poll_id, days, args.timed)
    print(f"\nDone. {added} added, {skipped} skipped.")
    print(f"Internal : {client.internal_url(args.poll_id)}")
    return 0


def cmd_share(args) -> int:
    client = _resolve_client(args)
    client.get_poll(args.poll_id)
    link = client.create_public_share(args.poll_id)
    if link:
        print(link)
        return 0
    print("Could not create a public share link.", file=sys.stderr)
    return 1


def _poll_age_days(poll: dict, now: float) -> float | None:
    created = poll.get("created")
    if not created:
        return None
    return (now - float(created)) / 86400.0


def _is_owned(poll: dict) -> bool:
    status = poll.get("currentUserStatus") or {}
    return bool(status.get("isOwner"))


def _format_poll_row(poll: dict, age_days: float | None) -> str:
    pid = poll.get("id", "?")
    title = poll.get("title", "(untitled)")
    age = f"{age_days:.0f}d" if age_days is not None else "?"
    owned = "you" if _is_owned(poll) else "-"
    return f"  [{pid:>4}] {age:>5} ago  owner={owned:<3}  {title}"


def cmd_list(args) -> int:
    client = _resolve_client(args)
    now = time.time()
    polls = client.list_polls()
    if args.mine:
        polls = [p for p in polls if _is_owned(p)]
    if not polls:
        print("No polls found.")
        return 0
    polls.sort(key=lambda p: p.get("created", 0))
    print(f"{len(polls)} poll(s):\n")
    for p in polls:
        print(_format_poll_row(p, _poll_age_days(p, now)))
    return 0


def cmd_prune(args) -> int:
    client = _resolve_client(args)
    now = time.time()
    threshold = args.older_than
    polls = client.list_polls()
    if args.mine:
        polls = [p for p in polls if _is_owned(p)]

    candidates = []
    for p in polls:
        age = _poll_age_days(p, now)
        if age is not None and age > threshold:
            candidates.append((p, age))

    if not candidates:
        print(f"No polls older than {threshold} days.")
        return 0

    candidates.sort(key=lambda t: t[1], reverse=True)
    print(f"{len(candidates)} poll(s) older than {threshold} days "
          f"would be deleted:\n")
    for p, age in candidates:
        print(_format_poll_row(p, age))

    if not args.yes:
        print("\nThis permanently deletes the polls listed above.")
        if input("Delete them? [y/N] ").strip().lower() not in ("y", "yes"):
            print("Aborted. Nothing deleted.")
            return 1

    deleted = failed = 0
    for p, _age in candidates:
        pid = p.get("id")
        try:
            client.delete_poll(int(pid))
            deleted += 1
            print(f"  deleted [{pid}] {p.get('title', '')}")
        except PollsError as exc:
            failed += 1
            print(f"  failed  [{pid}]: {exc}", file=sys.stderr)
    print(f"\nDone. {deleted} deleted, {failed} failed.")
    return 0 if failed == 0 else 2


# ----------------------------------------------------------------------
# entry point
# ----------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PollsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
