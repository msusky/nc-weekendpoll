# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html):
given a version MAJOR.MINOR.PATCH, MAJOR changes are incompatible, MINOR changes
add functionality in a backward-compatible way, and PATCH changes are
backward-compatible fixes. Until 1.0.0 the API and CLI may still change between
MINOR versions.

## [Unreleased]

_Nothing yet._

## [0.1.0] - 2026-06-07

Initial release.

### Added
- `create` command: create a date poll and fill it with every weekend in a
  range, set permissions, and print a public share link.
- `fill` command: add weekends to an existing poll (skips duplicates).
- `share` command: create a public share link for an existing poll.
- `list` command: list polls visible to you, with `--mine` to show only owned
  polls.
- `prune` command: delete polls older than a given number of days, after an
  explicit confirmation prompt; `--mine` and `--yes` supported.
- `--mode saturday|both` to choose one option per weekend or Saturday and
  Sunday separately.
- `--exclude DATE[:DATE]` (repeatable) to omit specific dates or inclusive
  ranges, e.g. holidays or already-booked weekends.
- `--index-php` to support instances without pretty URLs.
- Short forms for every long option (e.g. `-s`/`--start`).
- Credentials via `--url/--user/--password` flags or
  `WEEKENDPOLL_URL/USER/PASSWORD` environment variables.
- Integration tests running the full create → configure → add options → share →
  delete round-trip against live Nextcloud containers (server 32 and 33) with
  the Polls app, via `.github/workflows/integration.yml`. Skipped locally unless
  `WEEKENDPOLL_IT_URL/USER/PASSWORD` are set.
- Packaging for PyPI (`nc-weekendpoll`) with a Trusted-Publishing release
  workflow, `py.typed` marker, and CI on Python 3.10–3.13.

### Notes
- Distributed on PyPI as `nc-weekendpoll`; the import package and CLI command
  are `weekendpoll`. The `nc-` prefix signals the Nextcloud relationship
  (matching community practice such as nc-py-api) without using the registered
  trademark as part of the package name.
- Unofficial project, not affiliated with Nextcloud GmbH. "Nextcloud" is used
  descriptively only; see the README trademark notice.
- API calls verified against the Polls app source for v9.1.1 (OCS API v1.0) and
  exercised end-to-end by the integration workflow.

[Unreleased]: https://github.com/msusky/nc-weekendpoll/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/msusky/nc-weekendpoll/releases/tag/v0.1.0
