# AGENTS.md

Vendor-neutral context for AI coding agents working on this repo. Format:
[agents.md](https://agents.md/). Human docs live in `README.md`; this file is
only the operational context an agent needs.

## Project

`weekendpoll` — a small Python CLI that creates and manages date polls in the
**Polls app for Nextcloud** via its OCS API, to find a free weekend among
several people. Distributed on PyPI as `nc-weekendpoll`; import package and
command are both `weekendpoll`.

Unofficial, not affiliated with Nextcloud GmbH. "Nextcloud" is used only
descriptively. Do not add the Nextcloud trademark to the package name, logo, or
branding.

## Layout

- `src/weekendpoll/cli.py` — argparse CLI, subcommands, handlers
- `src/weekendpoll/client.py` — Nextcloud Polls OCS API client (HTTP only)
- `src/weekendpoll/dates.py` — pure date logic (weekends, exclusions)
- `src/weekendpoll/titles.py` — title suggestions
- `tests/` — pytest, no network access required

## Commands

- Install (dev): `pip install -e ".[dev]"`
- Test (offline unit tests): `pytest` — integration tests skip automatically
- Integration test (live server): set `WEEKENDPOLL_IT_URL/USER/PASSWORD`, then
  `pytest tests/test_integration.py`
- Lint: `ruff check .`
- Build: `python -m build` then `python -m twine check dist/*`

CI: `.github/workflows/ci.yml` runs lint + unit tests on Python 3.10–3.13.
`.github/workflows/integration.yml` starts Nextcloud containers (server 32 and
33, via a matrix), installs the Polls app via `occ app:install polls`, and runs
the live round-trip tests.
`.github/workflows/release.yml` publishes to PyPI on a `v*` tag via Trusted
Publishing. The linter and CI are the source of truth for style and
correctness — do not restate their rules here.

## Hard constraints (verify, don't guess)

- The API target is **Polls v9.1.1, OCS API v1.0**. Endpoints and payloads in
  `client.py` were verified against that release's controller source. If you
  change an API call or target a different Polls version, re-verify against the
  app source (`github.com/nextcloud/polls`, the relevant tag) — do not infer
  shapes from memory. Key facts that already bit us:
  - Base path is `/ocs/v2.php/...`, not `/index.php/...`.
  - Header `OCS-APIRequest: true` is required; responses are wrapped in
    `{"ocs": {"data": ...}}`.
  - Add-option payload is nested: `{"option": {...}}`.
  - Poll-update body key is `pollConfiguration`.
  - Share type is in the URL: `POST /poll/{id}/share/public`.
  - Web-UI links use pretty URLs by default (no `/index.php`); `--index-php`
    opts in to the prefix.
- Keep credentials out of code and logs. They come from `--url/--user/
  --password` flags or `WEEKENDPOLL_URL/USER/PASSWORD` env vars only.
- Destructive actions (`prune`) must keep an explicit confirmation prompt
  unless `--yes` is passed.
- Date logic must stay pure and unit-tested; network calls live only in
  `client.py`.

## Extending

- New subcommand: add a parser in `build_parser()` and a `cmd_*` handler in
  `cli.py`; share connection flags via the `conn` parent parser; add tests.
- New API call: add a method to `PollsClient`, unwrap the OCS envelope with
  `_unwrap`, and check status with `_check`. Document the endpoint in the
  README "API reference" table and note the verified Polls version.
- Every long flag has a single-letter short form; keep that consistent and
  collision-free per subcommand.
- Update `CHANGELOG.md` for user-visible changes; bump the version in both
  `pyproject.toml` and `src/weekendpoll/__init__.py`.
