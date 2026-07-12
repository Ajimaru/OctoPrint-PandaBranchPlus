# HTTP API

The plugin exposes OctoPrint's SimpleAPI under
`/api/plugin/pandabranchplus`. All requests need an authenticated OctoPrint
session or API key; reads require the `STATUS` permission, commands require
`CONTROL`.

## GET — current state

```text
GET /api/plugin/pandabranchplus
```

```json
{
  "connected": true,
  "channels": { "usb": { "1": 1, "2": 0 }, "mx24v": { "1": 0 } },
  "layout": [{ "kind": "usb", "id": 1, "type": "Type-C 5A" }]
}
```

`layout` is the fixed hardware layout (source: `hardware.py`) — the frontend
renders type badges from it instead of persisting types.

## POST commands

`POST /api/plugin/pandabranchplus` with `{"command": "<name>", ...}`.

### `set_channel`

Switch a channel now. `{"command": "set_channel", "kind": "usb", "id": 1,
"on": true}` → `{"ok": true}` or `{"ok": false, "reason": "...",
"detail": "..."}`. On a manual-mode channel the state is remembered as
`manual_on`. Fails with `not_connected` while the Panda is unreachable.

### `set_mode`

`{"command": "set_mode", "kind": "usb", "id": 1, "mode": "auto"|"manual"}` —
persists the mode and immediately re-applies the rules (manual enforces the
remembered state, auto re-applies the matrix).

### `set_label`

`{"command": "set_label", "kind": "usb", "id": 1, "label": "Panda Hub"}` —
strips and caps the label at 64 chars, returns `{"ok": true, "label": "..."}`.

### `set_channel_config`

`{"command": "set_channel_config", "kind": "usb", "id": 1, "rules": {...},
"temp_rule": {...}, "failsafe": "off"}` — any subset of the three fields;
values are validated server-side (see
[Architecture → Settings](../architecture/settings.md)). Re-applies rules on
success.

### `test_connection`

`{"command": "test_connection", "host": "…", "port": 80, "path": "/ws"}` —
one-shot connect independent of the running client; parameters fall back to
the stored settings. Returns `{"ok": true, "channels": 10}` or `{"ok":
false, "reason": "no_host"|"timeout"|"unreachable", "detail": "..."}`.

## Push messages

Live updates arrive over OctoPrint's push socket
(`onDataUpdaterPluginMessage`, plugin id `pandabranchplus`):

```json
{ "type": "connection", "connected": false }
{ "type": "state", "channels": { "usb": { "5": 1 } } }
```
