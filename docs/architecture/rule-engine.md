# Rule engine

The engine lives in two places: the **pure logic** in `rules.py` (what should
this channel be?) and the **application loop** in the plugin
(`apply_channel_rules()` — compare against reality, rate-limit, switch).

## Resolution order (per channel)

1. **Manual mode wins.** A channel in manual mode always resolves to its
   remembered `manual_on` state; automation never touches it — no timeout,
   no auto-fallback.
2. **State matrix.** In auto mode, `rules[state]` decides: `on`, `off`, or
   `ignore` (= no opinion, the channel keeps whatever state it has).
3. **Temperature rule** (optional, per channel): activates when the sensor
   reaches the threshold, releases only below `threshold − hysteresis`
   (falling-edge dead band, prevents flapping). While active it contributes
   its `above` action; while inactive it has no opinion. A missing sensor
   value keeps the previous verdict.
4. **Combine logic** (global): how matrix and temp rule merge —
   `temp_override` (temp wins while active), `and`, or `or`.

## Application loop

`apply_channel_rules(reason)` runs on every printer state change, temperature
update (only when at least one temp rule is enabled), settings save, and
reconnect. It:

- skips entirely when automation is disabled or the WS is down,
- resolves each channel's target and compares it to the **live state** from
  the Panda,
- enforces the per-channel **rate limit** (`min_switch_interval`): a switch
  that falls inside the window is not dropped but **deferred** — a coalesced
  timer re-runs the engine right after the window expires,
- sends the switch and records the timestamp.

## Initial sync

On every (re)connect the current state is evaluated and applied, so channels
switched externally while the plugin was away come back to a defined state.
On the _first_ connect after OctoPrint starts, `startup_behaviour` runs
first: `leave` (default), `all_off`, or `restore` (re-assert manual
channels' remembered state).

## Failsafe

Each channel has a failsafe (`off` / `on` / `hold`) applied **on OctoPrint
shutdown** — the last moment the plugin can still talk to the Panda. A lost
connection cannot be failsafed (there is nothing to send to); that case is
covered by the initial sync on reconnect. This is an honest limitation of a
network-controlled hub, not a bug.

## State mapping

`map_octoprint_state()` folds OctoPrint's state ids into the five matrix
states:

| OctoPrint state id                  | Matrix state |
| ----------------------------------- | ------------ |
| `STARTING`                          | `prepare`    |
| `PRINTING`, `RESUMING`, `FINISHING` | `printing`   |
| `PAUSED`, `PAUSING`                 | `paused`     |
| `ERROR`, `CLOSED_WITH_ERROR`        | `error`      |
| everything else (incl. no printer)  | `idle`       |
