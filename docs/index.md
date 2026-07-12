# OctoPrint-PandaBranchPlus

Channel automation for the **BIQU Panda Branch Plus** power hub in OctoPrint:
name each of the 10 switchable outputs, switch them manually from a tab, and
let a per-channel rule matrix follow the printer state (with optional
temperature rules on top).

These are the **developer docs** — architecture, APIs, and the reverse
engineered Panda WebSocket protocol. For installation and day-to-day usage see
the [README](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus#readme).

## What the plugin does

- Keeps **one long-lived WebSocket** to the Panda (`ws://<panda>/ws`),
  reconnecting with backoff and detecting dead peers via TCP keepalive
  (the firmware never answers WebSocket pings).
- Mirrors the **live on/off state** of all 10 channels into the OctoPrint UI
  via `send_plugin_message` pushes.
- Derives a canonical **printer state** (`idle` / `prepare` / `printing` /
  `paused` / `error`) from OctoPrint's standard events — any connector that
  feeds OctoPrint's state machine works, including OctoPrint-BambuConnector.
- Applies a per-channel **rule matrix** (state → on/off/ignore), optional
  **temperature rules** with hysteresis, per-channel **manual override**,
  rate limiting, and a **failsafe** state on shutdown.

## Repository layout

| Path                                    | Contents                                                   |
| --------------------------------------- | ---------------------------------------------------------- |
| `octoprint_pandabranchplus/__init__.py` | Plugin: mixins, settings, SimpleAPI, rule application      |
| `octoprint_pandabranchplus/panda_ws.py` | WebSocket client (reconnect, keepalive, state parsing)     |
| `octoprint_pandabranchplus/rules.py`    | Pure rule engine — no OctoPrint imports, fully unit-tested |
| `octoprint_pandabranchplus/hardware.py` | Fixed channel layout (kinds, ids, type badges)             |
| `octoprint_pandabranchplus/static/js/`  | Knockout view model for tab + settings                     |
| `octoprint_pandabranchplus/templates/`  | Jinja2 templates (tab, settings dialog)                    |
| `tests/`                                | Unit tests for the rule engine and hardware layout         |
| `docs/`                                 | This documentation                                         |

## Where to start

- [Getting started](getting-started.md) — dev environment and first build.
- [Architecture overview](architecture/overview.md) — how the pieces fit.
- [Panda WS protocol](reference/panda-ws-protocol.md) — the verified firmware
  protocol.
