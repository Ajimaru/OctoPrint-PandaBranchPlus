# OctoPrint integration

## Mixins

`PandaBranchPlusPlugin` implements `SettingsPlugin`, `AssetPlugin`,
`TemplatePlugin`, `StartupPlugin`, `EventHandlerPlugin`, `SimpleApiPlugin`
— plus `octoprint.printer.PrinterCallback`, because the plugin registers
itself as a printer callback for temperature data. The callback base class
matters: it provides no-op defaults for every method the printer pushes
(`on_printer_send_current_data`, …); without it every push raises.

## Event flow

`on_event` reacts to `PRINTER_STATE_CHANGED`, `CONNECTED`, `DISCONNECTED`
and `PRINT_FAILED`. The handler ignores the payload and **re-derives** the
canonical state from `self._printer.get_state_id()` — one source of truth,
no payload parsing.

`on_printer_add_temperature` maps the standard sensors into the engine's
temp dict (`bed`, `tool` ← `tool0`, `chamber`) and re-applies rules — but
only when at least one temp rule is actually enabled, so idle instances do
no work on the 1-Hz temperature stream.

!!! note "Chamber temperature"
    `chamber` only carries data when the active connector reports it through
    OctoPrint's standard temperature interface. OctoPrint-BambuConnector
    does; a bare serial printer usually does not.

## Startup / shutdown

- `on_after_startup`: apply log level, register the printer callback, start
  the WS client (if a host is configured).
- `on_shutdown`: apply per-channel failsafe, then stop the WS client.

## Browser push

Channel state and connection changes are pushed to all open browsers via
`send_plugin_message` (`{"type": "state", ...}` / `{"type": "connection",
...}`); the Knockout view model consumes them in
`onDataUpdaterPluginMessage`. A freshly opened browser pulls the current
picture once via SimpleAPI GET.

## Permissions

The SimpleAPI is protected (`is_api_protected() = True`); reads require
`Permissions.STATUS`, writes (switching, config) require
`Permissions.CONTROL`. No plugin-specific permission — this instance is not
multi-user.
