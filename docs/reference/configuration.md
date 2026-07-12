# Configuration reference

All settings live under `plugins.pandabranchplus` in OctoPrint's
`config.yaml`. Everything here is editable in the UI; the YAML paths are for
reference and provisioning.

## Connection

| Key             | Default | Meaning                                       |
| --------------- | ------- | --------------------------------------------- |
| `host`          | `""`    | Panda host/IP. Empty = WS client not started. |
| `ws_port`       | `80`    | WebSocket port.                               |
| `ws_path`       | `/ws`   | WebSocket path.                               |
| `reconnect_min` | `1`     | Reconnect backoff floor (seconds).            |
| `reconnect_max` | `30`    | Reconnect backoff ceiling (seconds).          |

## Automation (global)

| Key                   | Default         | Meaning                                                                            |
| --------------------- | --------------- | ---------------------------------------------------------------------------------- |
| `automation_enabled`  | `true`          | Master switch for the rule engine. Manual control keeps working when off.          |
| `combine_logic`       | `temp_override` | How matrix and temp rule merge: `temp_override` \| `and` \| `or`.                  |
| `temp_hysteresis`     | `2`             | Dead band (°C) below the threshold before a temp rule releases.                    |
| `min_switch_interval` | `3`             | Per-channel rate limit (seconds); rate-limited switches are deferred, not dropped. |

## Safety

| Key                  | Default | Meaning                                                                |
| -------------------- | ------- | ---------------------------------------------------------------------- |
| `confirm_high_power` | `true`  | Confirmation dialog before manually switching ON an MX3.0 24V channel. |
| `startup_behaviour`  | `leave` | First connect after start: `leave` \| `all_off` \| `restore`.          |

## Diagnostics

| Key             | Default | Meaning                                                             |
| --------------- | ------- | ------------------------------------------------------------------- |
| `debug_logging` | `false` | Plugin logger at DEBUG (rule evaluations, reconnects).              |
| `frame_log`     | `false` | Log every raw WS frame at DEBUG — noisy, protocol diagnostics only. |

## Per-channel (`channels[]`)

See [Architecture → Settings](../architecture/settings.md) for the full
channel model and validation rules.
