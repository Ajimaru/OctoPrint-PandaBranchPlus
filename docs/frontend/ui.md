# Tab, sidebar and settings UI

One Knockout view model (`PandaBranchPlusViewModel`) binds the tab, the
sidebar panel and the settings dialog. Dependencies: `loginStateViewModel`,
`settingsViewModel`.

## Tab

One card per channel:

- **Header:** channel id, fixed type badge (from the API `layout`), editable
  label (auto-saved on blur via `set_label`), live ON/OFF state, Auto/Manual
  toggle, manual switch button.
- **Body** (visible in auto mode): the state matrix (five selects:
  idle/preparing/printing/paused/error), the failsafe select, and the
  optional temperature rule row (sensor, threshold, action).

Every matrix/temp/failsafe change is persisted immediately through
`set_channel_config` — there is no save button. Manual switch-ON of an
`mx24v` channel shows a confirmation dialog when `confirm_high_power` is
enabled (that is where heaters and pumps live).

A warning banner appears while the Panda WebSocket is down; the live state
then reflects the last known snapshot.

## Sidebar

A minimal status panel: one chip per channel, showing the channel label with
a colored border — **red = on**, **green = off**, **yellow = state unknown**
(Panda disconnected, or no state received yet). The chip tooltip spells the
state out.

The panel can be turned off with the `sidebar_enabled` checkbox in the
settings dialog (default: on). The view model hides the whole sidebar
wrapper (`#sidebar_plugin_pandabranchplus_wrapper`) and reacts live to the
setting — no restart needed.

## Settings dialog

Global configuration only: connection (host, port/path, reconnect window,
test button), automation (master enable, combine logic, hysteresis, switch
interval), safety (24V confirmation, startup behavior), interface (sidebar
panel), diagnostics (debug log, frame log). Every field carries a `(?)`
tooltip.

The **Test connection** button tests the values currently in the dialog —
including unsaved ones — via the `test_connection` API command and shows the
classified result inline.

## Live updates

- `onStartupComplete` pulls the current picture once (SimpleAPI GET:
  connected flag, channel states, hardware layout).
- `onDataUpdaterPluginMessage` consumes pushes: `connection` toggles the
  banner, `state` updates the per-channel observables.
