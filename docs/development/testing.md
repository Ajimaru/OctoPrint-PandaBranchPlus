# Testing

## Unit tests

```bash
pytest tests/
```

- `tests/test_rules.py` — the rule engine: state matrix, manual mode,
  temperature rules (threshold, hysteresis, missing sensor, `above: off`),
  combine logic (override/AND/OR), OctoPrint state mapping.
- `tests/test_hardware.py` — the fixed channel layout.

Both test modules import only the pure modules, so they run without an
OctoPrint installation. CI runs them on Python 3.9–3.13 plus an OctoPrint
smoke import (1.10.x and devel).

## What is deliberately not unit-tested

The plugin class itself (mixin glue) and the WebSocket client's network
behavior — those are covered by the end-to-end checklist below against real
hardware. Mocking a firmware that was reverse engineered is a good way to
test the mock.

## End-to-end checklist (real Panda + printer)

1. Configure the Panda IP, **Test connection** reports 10 channels.
2. Tab shows live state; manual toggle switches the physical output.
3. Rule `printing → on, idle → off` on a scratch channel: start/stop a print
   — the channel follows (including the deferred retry when the rate limit
   window swallows the first attempt).
4. Temperature rule bed ≥ threshold: heat the bed — channel on; cool below
   threshold minus hysteresis — channel off.
5. Disconnect the Panda: banner appears, no crash-loop in the log;
   reconnect: initial sync restores rule targets.
6. Restart OctoPrint: labels, modes and rules survive.

!!! tip
    Use a channel with nothing attached (or an LED) for rule testing, and
    put everything you care about on **Ignore** first.
