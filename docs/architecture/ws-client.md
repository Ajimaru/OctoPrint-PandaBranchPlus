# WebSocket client

`panda_ws.py` holds one long-lived connection to the Panda and exposes two
things upward: a `set_channel()` call and two callbacks (`on_state`,
`on_connection`). Structure mirrors the proven `BambuMqttMonitor` pattern
from OctoPrint-BambuCam.

## Connection lifecycle

- `PandaWsClient.start()` spawns a daemon thread running `_run_loop()`.
- The loop creates a `websocket.WebSocketApp`, runs it until it dies, then
  reconnects with a **doubling backoff** between `reconnect_min` and
  `reconnect_max` (defaults 1–30 s). A successful connect resets the delay.
- `stop()` is idempotent: sets the stop event, closes the socket, joins the
  thread.
- On connect the Panda immediately pushes a **full state snapshot**; every
  subsequent channel change (from any client) is broadcast as a push.

## Why TCP keepalive instead of WS pings

The Panda firmware **never answers WebSocket protocol pings** (verified
against the device — its own web UI uses no pings either). Any
`ping_interval`/`ping_timeout` on `run_forever` therefore kills a perfectly
healthy connection after the timeout ("websocket ping/pong timed out").

Dead peers are detected via TCP keepalive socket options instead
(`SO_KEEPALIVE` plus, where the platform defines them, `TCP_KEEPIDLE=30`,
`TCP_KEEPINTVL=10`, `TCP_KEEPCNT=3` — roughly 60 s to detection on Linux).

## State parsing

`_parse_channel_state()` accepts both frame shapes the firmware produces —
channel lists nested under `control` (snapshot) and at the top level (pushes)
— and normalizes them to `{"usb": {id: 0|1}, "mx24v": {id: 0|1}}`.

## Error classification

All failures surface as `PandaWsError` with a machine-readable `reason`
(`unreachable` / `timeout` / `send_failed`) so the frontend can translate
them without parsing raw socket errors. The one-shot
`test_connection()` helper (settings dialog button) uses the same
classification.
