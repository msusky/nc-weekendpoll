# Contributing to weekendpoll

Thanks for your interest in improving weekendpoll!

## Getting started

```bash
git clone https://github.com/msusky/nc-weekendpoll
cd weekendpoll
pip install -e ".[dev]"
```

## Before opening a pull request

- Run the tests: `pytest`
- Run the linter: `ruff check .`
- Keep the API client (`src/weekendpoll/client.py`) consistent with the
  Polls version it targets. If you verify against a new Polls version, note
  the version in the module docstring and update the README's API table.
- If you change build/test commands, the layout, or the verified API facts,
  update `AGENTS.md` too — it is the context AI coding agents rely on.

## Reporting issues

Please include your Nextcloud version, your Polls app version, the command you
ran (with credentials removed), and the full error output.

## Versioning

This project follows [Semantic Versioning](https://semver.org/): MAJOR for
incompatible changes, MINOR for backward-compatible features, PATCH for
backward-compatible fixes. Record every user-visible change in `CHANGELOG.md`
under `[Unreleased]` as part of your PR, using the
[Keep a Changelog](https://keepachangelog.com/) sections (Added, Changed,
Deprecated, Removed, Fixed, Security).

## Releasing to the package registry (maintainers)

The package is published to PyPI as **`nc-weekendpoll`**. Releases are
automated: pushing a `v*` tag triggers `.github/workflows/release.yml`, which
builds the sdist + wheel and uploads them to PyPI via
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC, no API
token secrets in the repo).

One-time setup on PyPI: register this repository as a trusted publisher for the
`nc-weekendpoll` project, with workflow `release.yml` and environment `pypi`.

To cut a release:

1. Decide the new version per SemVer based on what changed.
2. Bump it in **both** `pyproject.toml` and `src/weekendpoll/__init__.py`.
3. In `CHANGELOG.md`, move the `[Unreleased]` entries under a new
   `## [X.Y.Z] - YYYY-MM-DD` heading and update the link references at the
   bottom.
4. Commit, then tag and push:

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

5. Optionally verify on TestPyPI first:

   ```bash
   python -m build
   python -m twine check dist/*
   python -m twine upload --repository testpypi dist/*
   ```

## Scope

weekendpoll is intentionally small: create a date poll, fill it with weekends,
share it, and tidy up old polls. Proposals that keep it focused and
dependency-light are most welcome.
