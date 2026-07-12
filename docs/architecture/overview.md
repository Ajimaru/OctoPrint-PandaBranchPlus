# Architecture overview

Three layers, deliberately separated:

```text
OctoPrint events / temps        Panda Branch Plus (ESP32-S3)
        │                                ▲
        ▼                                │ ws://<panda>/ws
┌──────────────────────┐   targets   ┌───────────────────┐
│ __init__.py (plugin) │────────────▶│ panda_ws.py       │
│  mixins, settings,   │             │  PandaWsClient    │
│  SimpleAPI, engine   │◀────────────│  reconnect,       │
└──────────┬───────────┘  state push │  keepalive        │
           │                         └───────────────────┘
           │ pure function calls
           ▼
┌──────────────────────┐
│ rules.py             │  no OctoPrint imports, unit-tested
│  resolve_target()    │
│  evaluate_temp_rule()│
│  map_octoprint_state │
└──────────────────────┘
```

## Design decisions

- **State source is OctoPrint, not the printer.** The plugin never talks to
  the printer directly; it consumes OctoPrint's standard state machine and
  temperature callbacks. Any connector that feeds OctoPrint works.
- **The rule engine is pure.** `rules.py` has no OctoPrint imports and no
  side effects — it maps `(channel config, state, temps, hysteresis latch)`
  to a target (`"on"` / `"off"` / `None`). All 18 rule tests run without an
  OctoPrint install.
- **Only switch on target ≠ actual.** The engine compares the resolved target
  against the live state from the Panda snapshot and only then sends a
  command — no command spam, no relay chatter.
- **The Panda broadcasts to all clients.** `/ws` is multi-client (verified);
  external switches (Panda web UI, physical button) arrive as state pushes.
  Channels in auto mode may be switched back by the engine; channels in
  manual mode or on _Ignore_ keep the external state.

## Component pages

- [WebSocket client](ws-client.md) — connection lifecycle, keepalive story.
- [Rule engine](rule-engine.md) — matrix, temp rules, combine logic,
  rate limiting, failsafe.
- [OctoPrint integration](octoprint-integration.md) — mixins, events,
  printer callback.
- [Settings](settings.md) — storage model and validation.
