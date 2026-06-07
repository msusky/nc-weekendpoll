# weekendpoll

Find a free weekend among several people, using your own
[Polls app for Nextcloud](https://github.com/nextcloud/polls) instance.

`weekendpoll` is a small command-line tool that talks to the Polls app's API.
It creates a **date poll**, fills in every weekend in a date range,
configures the sharing permissions, and prints a public link you can send to
the group — so you never have to add each Saturday by hand in the web UI.

> **Unofficial project.** Not affiliated with, endorsed by, or sponsored by
> Nextcloud GmbH. "Nextcloud" is a registered trademark of Nextcloud GmbH; it
> is used here only descriptively to state what this tool is compatible with.
> The PyPI distribution is named `nc-weekendpoll`; the installed command is
> `weekendpoll`.

```console
$ weekendpoll create --start 2026-07-01 --end 2026-12-31 --title "Find our free weekend" --yes
Created poll - ID 42
  + 2026-07-04
  + 2026-07-11
  ...
Done. 26 added, 0 skipped.
Internal : https://cloud.example.de/apps/polls/vote/42
Share    : https://cloud.example.de/apps/polls/s/AbC123xyz
```

> **Verified against Polls v9.1.1** (OCS API v1.0). Endpoint paths and payload
> shapes were checked against the app's controller source for that release.
> See [API reference](#api-reference-verified-against-v911).

---

## Compatibility

| Component | Tested / verified | Expected to work |
|---|---|---|
| Polls app | 9.1.1 | 9.x (same OCS API v1.0) |
| Nextcloud server | — (not run end-to-end by the author) | 32–33 (per Polls 9.1.1 `info.xml`) |
| Python | 3.10–3.13 (CI) | 3.10+ |

Notes:

- "Verified" means the API endpoints and payload shapes used by this tool were
  checked against the Polls **9.1.1** source, **and** exercised end-to-end by
  the integration workflow (see below) against live Nextcloud containers
  (server 32 and 33) with the Polls app installed.
- Polls 9.1.1 declares support for Nextcloud server **32–33** in its
  `info.xml`. Other server versions may work if they ship a Polls 9.x app with
  the same API.
- Other Polls major versions (8.x, 10.x, …) may need payload tweaks; the two
  fields most likely to differ are the option payload (nested under `option`)
  and the config key (`pollConfiguration`). See
  [Troubleshooting](#troubleshooting).

---

## Why a local tool?

The Polls web UI has no bulk import for date options, and there is no existing
dedicated CLI for managing polls via the API (the app ships `occ` commands, but
those need server shell access and do not cover bulk date entry).

`weekendpoll` runs **on your machine** and talks directly to your Nextcloud.
Your URL and app password never leave your computer. (A browser-based tool
cannot do this: Nextcloud does not send CORS headers that would allow an
external web page to call its API.)

---

## Installation

Requires Python 3.10+. The only runtime dependency is `requests`.

You do **not** need PyPI to use this tool — installing from a downloaded copy
or running it straight from source both work. Pick whichever fits:

**From a downloaded copy or git clone (no PyPI):**

```bash
# in the unpacked project folder
pip install .            # installs the `weekendpoll` command on your PATH
# or, isolated:
pipx install .
```

**Without installing at all (no PyPI, no install step):**

```bash
pip install requests     # the only dependency
# from the project root (src layout requires PYTHONPATH):
PYTHONPATH=src python -m weekendpoll --help
```

**From PyPI (once published):**

```bash
pip install nc-weekendpoll
# or: pipx install nc-weekendpoll
```

**For development (editable install with test dependencies):**

```bash
pip install -e ".[dev]"
```

In every case the installed command is `weekendpoll` (the PyPI distribution is
named `nc-weekendpoll`; the command and import package stay `weekendpoll`).

---

## Authentication

Use a Nextcloud **app password**, never your account password.

1. In Nextcloud: **Settings → Security → Devices & sessions**
2. Enter a name (e.g. `weekendpoll`) and click **Create new app password**
3. Copy the generated value

Provide credentials in either of two ways (flags take precedence):

```bash
# via environment variables (recommended)
export WEEKENDPOLL_URL="https://cloud.example.de"
export WEEKENDPOLL_USER="your-login"
export WEEKENDPOLL_PASSWORD="xxxxx-xxxxx-xxxxx-xxxxx-xxxxx"

# or via flags on each command
weekendpoll create --url ... --user ... --password ... --start ... --end ...
```

You can revoke the app password any time from the same settings screen.

---

## Usage

Five subcommands: `create`, `fill`, `share`, `list`, `prune`.

### `create` — new poll, filled with weekends

```bash
weekendpoll create \
  --start 2026-07-01 --end 2026-12-31 \
  --mode saturday \
  --title "Find our free weekend"
```

If you omit `--title`, the tool offers a few suggestions to pick from. It
prints a preview of all dates and asks for confirmation before writing
(skip with `--yes`).

To leave out specific weekends — holidays, or dates already taken — use
`--exclude`, which accepts a single date or an inclusive `DATE:DATE` range and
can be given multiple times:

```bash
weekendpoll create \
  --start 2026-07-01 --end 2026-12-31 \
  --exclude 2026-10-03 \
  --exclude 2026-12-19:2027-01-04
```

### `fill` — add weekends to an existing poll

```bash
weekendpoll fill 42 --start 2027-01-01 --end 2027-03-31
```

Useful for extending a poll later. Existing options are skipped, so re-running
never creates duplicates. Add `--no-config` to leave the poll's settings
untouched.

### `share` — create a public link for an existing poll

```bash
weekendpoll share 42
```

Prints the public share URL (useful in scripts).

### `list` — show your polls

```bash
weekendpoll list          # all polls visible to you
weekendpoll list --mine   # only polls you own
```

Each row shows the poll ID, its age, whether you own it, and the title:

```text
3 poll(s):

  [   3]   95d ago  owner=you  Find our free weekend
  [   7]   12d ago  owner=you  Team lunch
  [  11]    2d ago  owner=-    Shared by a colleague
```

### `prune` — delete polls older than a given age

```bash
weekendpoll prune --older-than 90 --mine
```

Lists every poll older than the given number of days and deletes them **after
an explicit confirmation prompt**. The deletion is permanent, so `--mine` is
recommended to avoid touching polls shared with you by others. Use `--yes` to
skip the prompt in scripts (use with care).

### Options reference

Every long option has a single-letter short form (run any subcommand with
`--help` to see both). For example `-s`/`--start`, `-e`/`--end`, `-m`/`--mode`,
`-x`/`--exclude`, `-t`/`--title`, `-o`/`--older-than`, `-i`/`--mine`,
`-y`/`--yes`.

| Flag | Applies to | Meaning |
|---|---|---|
| `--start` / `--end` | create, fill | Date range, `YYYY-MM-DD`, inclusive |
| `--mode` | create, fill | `saturday` (one per weekend) or `both` (Sat + Sun) |
| `--timed` | create, fill | Make timed options instead of all-day |
| `--exclude` | create, fill | Exclude a date or `DATE:DATE` range; repeatable |
| `--title` | create | Poll title (omit for suggestions) |
| `--description` | create | Poll description |
| `--no-proposals` | create, fill | Disallow participants proposing their own dates |
| `--no-comments` | create, fill | Disable comments |
| `--no-maybe` | create, fill | Disable the "maybe" option |
| `--anonymous` | create, fill | Pseudonymise participant names |
| `--no-share` | create | Do not create a public link |
| `--no-config` | fill | Do not modify the poll's configuration |
| `--older-than DAYS` | prune | Delete polls created more than DAYS days ago |
| `--mine` | list, prune | Only consider polls you own |
| `--index-php` | all | Use `/index.php` in web-UI links (see below) |
| `--yes` / `-y` | create, fill, prune | Skip the confirmation prompt |

### Web-UI link style

Most Nextcloud instances use "pretty URLs", so poll links look like
`https://your-instance/apps/polls/vote/3` and shares like
`https://your-instance/apps/polls/s/<token>`. This is the default.

If your instance only works with the `index.php` prefix
(`https://your-instance/index.php/apps/polls/...`), pass `--index-php`.
Either way, the API itself is always reached via `/ocs/v2.php`, so this flag
only affects the links that are printed, not the requests.

---

## How sharing and permissions work in Polls

Polls does **not** use the granular read/write/create permission bitmask of
Nextcloud's general file-sharing API. Its model is simpler:

- A **public link** always allows participants to **vote**.
- "Editing" for participants means **proposing additional dates**, controlled
  by `allowProposals`. `weekendpoll` enables this by default; disable with
  `--no-proposals`.
- `access` is set to `open` so people arriving via the link can take part.
- Full **admin editing** (changing settings, deleting options) is **not**
  available through a public link by design. For co-administrators, invite
  people as Nextcloud users or via an email share instead.

---

## API reference (verified against v9.1.1)

All endpoints are under `/ocs/v2.php/apps/polls/api/v1.0` and require the
header `OCS-APIRequest: true`. Responses are wrapped in
`{"ocs": {"data": ...}}`.

| Action | Method & path | Payload |
|---|---|---|
| Create poll | `POST /poll` | `{"type": "datePoll", "title": "..."}` |
| Update config | `PUT /poll/{id}` | `{"pollConfiguration": { ... }}` |
| Add date option | `POST /poll/{id}/option` | `{"option": {"timestamp": <unix>, "duration": <seconds>}}` |
| Create public link | `POST /poll/{id}/share/public` | `{}` (type is in the URL) |
| Get poll | `GET /poll/{id}` | — |
| List polls | `GET /polls` | — |
| Delete poll | `DELETE /poll/{id}` | — |

Config values used: `access: "open"`, `allowProposals: "allow"|"disallow"`,
plus the booleans `allowComment`, `allowMaybe`, `anonymous`.

---

## Project layout

```
weekendpoll/
├── pyproject.toml          # packaging + console_scripts entry point
├── README.md
├── LICENSE                 # MIT
├── CONTRIBUTING.md
├── CHANGELOG.md
├── AGENTS.md               # context for AI coding agents (agents.md format)
├── .gitignore
├── .github/workflows/
│   ├── ci.yml              # lint + unit tests on push/PR
│   ├── integration.yml     # live Nextcloud + Polls round-trip test
│   └── release.yml         # publish to PyPI on version tag (OIDC)
├── src/weekendpoll/
│   ├── __init__.py
│   ├── __main__.py         # python -m weekendpoll
│   ├── cli.py              # argparse CLI, subcommands
│   ├── client.py           # Polls (Nextcloud) API client
│   ├── dates.py            # weekend computation
│   ├── titles.py           # title suggestions
│   └── py.typed            # marks the package as typed
└── tests/
    ├── test_dates.py
    ├── test_prune.py
    ├── test_urls.py
    └── test_integration.py # live API tests (skipped without IT env vars)
```

---

## Development

```bash
pip install -e ".[dev]"
pytest        # unit tests (offline, no network needed)
ruff check .  # lint
```

The integration tests in `tests/test_integration.py` are skipped unless
`WEEKENDPOLL_IT_URL`, `WEEKENDPOLL_IT_USER`, and `WEEKENDPOLL_IT_PASSWORD` are
set, so the default `pytest` run stays offline. CI runs them automatically:
`.github/workflows/integration.yml` starts a real Nextcloud container (tested
against server versions 32 and 33 via a matrix), installs
the Polls app, and exercises the full create → configure → add options → share
→ delete round-trip against the live OCS API. To run them locally against your
own instance:

```bash
export WEEKENDPOLL_IT_URL="https://your-instance"
export WEEKENDPOLL_IT_USER="your-login"
export WEEKENDPOLL_IT_PASSWORD="your-app-password"
pytest tests/test_integration.py -v
```

## Publishing (maintainers)

Releases go to PyPI automatically via GitHub Actions when a version tag is
pushed, using [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC — no API token secrets stored in the repo).

One-time setup: on PyPI, register this repository as a trusted publisher for
the `nc-weekendpoll` project (workflow `release.yml`, environment `pypi`). Then:

```bash
# bump the version in pyproject.toml and src/weekendpoll/__init__.py,
# update CHANGELOG.md, commit, then:
git tag v0.1.0
git push origin v0.1.0
```

To build and check locally first:

```bash
python -m build
python -m twine check dist/*
# optional dry run against TestPyPI:
python -m twine upload --repository testpypi dist/*
```

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR** — incompatible changes to the CLI or behaviour.
- **MINOR** — new, backward-compatible functionality (e.g. a new flag).
- **PATCH** — backward-compatible bug fixes.

While the version is below `1.0.0`, the CLI may still change between MINOR
versions. The version lives in `pyproject.toml` and
`src/weekendpoll/__init__.py` (kept in sync), and every release is git-tagged
`vMAJOR.MINOR.PATCH`. All notable changes are recorded in
[CHANGELOG.md](CHANGELOG.md), which follows the
[Keep a Changelog](https://keepachangelog.com/) format: land changes under
`[Unreleased]`, then move them under a new version heading when you tag a
release.

---

## Troubleshooting

- **401 Unauthorized** — wrong login or app password, or it was revoked.
- **Poll not found** — check the ID in the poll URL (`.../vote/<id>`).
- **Everything 404s** — confirm the base URL works in a browser and the Polls
  app is enabled; a reverse proxy must not strip the `OCS-APIRequest` header.
- **Config "failed" error** — a field name may differ in your Polls version.
  Compare `GET /ocs/v2.php/apps/polls/api/v1.0/poll/{id}` output with the keys
  in `client.py`.
- **Managed hosting (e.g. hosting.de)** — no `occ` access is needed; everything
  here uses the HTTP API. If your provider uses a non-standard path without
  `/ocs/v2.php`, that is the part to adjust in `client.py`.

---

## Security notes

- Always use an **app password**, never your account password.
- Prefer environment variables over flags so the password is not stored in your
  shell history.
- The public share link lets anyone with it participate; share it only with the
  intended group.

---

## License

MIT — see [LICENSE](LICENSE). The Polls app for Nextcloud itself is AGPL-3.0;
this tool only talks to its API and bundles none of its code.

## Trademark notice

"Nextcloud" and the Nextcloud logo are registered trademarks of Nextcloud GmbH.
This project is an independent, unofficial tool and is not affiliated with,
endorsed by, or sponsored by Nextcloud GmbH. The trademark is used only in a
descriptive (nominative) manner to indicate compatibility, in line with
Nextcloud's [trademark guidelines](https://nextcloud.com/trademarks/). This
project does not use the Nextcloud logo or any Nextcloud marks in its own logo
or branding.
