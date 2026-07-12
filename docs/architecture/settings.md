# Settings

All configuration lives in OctoPrint's standard settings store
(`config.yaml → plugins.pandabranchplus`). Global settings are edited in the
settings dialog; **per-channel config is edited in the tab** (where the live
state is visible) and persisted immediately through the SimpleAPI — there is
no per-channel form in the settings dialog by design.

## Per-channel model

```yaml
channels:
  - kind: usb # fixed: "usb" | "mx24v"
    id: 1 # fixed: 1-5 per kind
    label: "Panda Hub" # user text, max 64 chars
    mode: auto # "auto" | "manual"
    manual_on: false # remembered manual state
    rules: # state matrix, per printer state
      idle: off
      prepare: off
      printing: off
      paused: off
      error: off
    temp_rule:
      enabled: false
      sensor: bed # "bed" | "tool" | "chamber"
      threshold: 40
      above: on # action while active: "on" | "off"
    failsafe: off # on OctoPrint shutdown: "off" | "on" | "hold"
```

The hardware **type** of a channel (badge in the UI) is _not_ stored — it is
fixed in `hardware.py` and delivered to the frontend via the API `layout`
field, so stale persisted data can never disagree with the hardware.

## Validation

Channel config writes go through `_validated_config_fields()`: rule values
are whitelisted (`on`/`off`/`ignore`), sensors and failsafe values likewise,
thresholds coerced to float with a safe fallback. Unknown channels and empty
payloads abort with HTTP 400.

## Save behavior

`on_settings_save` compares the connection tuple (host, port, path) before
and after: if it changed, the WS client is restarted; otherwise the rule
engine re-runs immediately so changed automation settings take effect
without a reconnect. The debug-log toggle switches the plugin logger level
live.
