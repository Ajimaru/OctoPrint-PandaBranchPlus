# Release process

## Versioning

The single version source is `octoprint_pandabranchplus/_version.py`, bumped
with the local toolkit (`bump_control.sh`, which drives `bump-my-version`).
`pyproject.toml` and the plugin's `__plugin_version__` follow from it.

Dev builds carry a `devN` suffix; a `+unknown` local part appears when the
build runs outside a git checkout with history.

## Flow

1. Develop on `dev` (PRs land there).
2. Bump the version, update `CHANGELOG.md`.
3. Fast-forward `main` to the release state (rebase-only repo — no merge
   commits).
4. Tag the release; the `release.yml` workflow builds the distributable zip
   (`OctoPrint-PandaBranchPlus-latest.zip`) and attaches it, with release
   notes grouped by the categories in `.github/release.yml`.

## Update channel for users

Installed plugins update through OctoPrint's Software Update plugin — the
plugin registers a `github_release` check against
`Ajimaru/OctoPrint-PandaBranchPlus`, installing
`https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/archive/{target_version}.zip`.
