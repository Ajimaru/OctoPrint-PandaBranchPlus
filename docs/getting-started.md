# Getting started

## Prerequisites

- Python 3.9+ (the CI matrix tests 3.9–3.13)
- Node.js 20 (ESLint/Prettier hooks, JS API docs)
- A Panda Branch Plus on the same LAN (for end-to-end testing)
- An OctoPrint instance whose printer state is fed by any connector
  (a Bambu A1 mini via OctoPrint-BambuConnector, a serial printer, …)

## Development setup

```bash
git clone https://github.com/Ajimaru/OctoPrint-PandaBranchPlus.git
cd OctoPrint-PandaBranchPlus

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
# OctoPrint is not a declared dependency (the plugin installs INTO an
# OctoPrint); install it explicitly for imports, tests and mkdocstrings.
pip install octoprint pytest flake8 pylint pre-commit
pip install -e .

# Wire up the repo's git hooks (do NOT run `pre-commit install`).
git config core.hooksPath .githooks
```

## Running the checks

```bash
pytest tests/                                  # rule engine + hardware tests
flake8 octoprint_pandabranchplus/ tests/       # style gate (88 cols)
pylint octoprint_pandabranchplus tests/*.py    # IDE-grade lint
pre-commit run --all-files                     # the full hook suite
```

## Building a dev zip

The plugin is packaged like any OctoPrint plugin:

```bash
python -m build
```

Install the resulting zip on an OctoPrint instance via
_Settings → Plugin Manager → Install from file_.

## Testing against a real Panda

Point the plugin at the Panda's IP in _Settings → Panda Branch Plus_ and use
**Test connection** — it opens a one-shot WebSocket, reads the state snapshot
and reports the channel count. The tab then shows the live state of all 10
channels.

!!! warning
    Automation switches real power outputs. While testing rules, set the
    channels of devices you care about to **Ignore** (or _Manual_ mode) so
    the engine never touches them.
