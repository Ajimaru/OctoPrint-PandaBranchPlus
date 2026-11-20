"""Rule engine: switching against the Panda's (possibly stale) live state.

The Panda confirms a switch by broadcasting its new state, so for a moment
after a command the live snapshot still shows the old value. These tests pin
down how apply_channel_rules behaves in that window.
"""

import logging

import pytest

import octoprint_pandabranchplus as plugin_module
from octoprint_pandabranchplus import PandaBranchPlusPlugin


class _Settings:
    def __init__(self, channels, min_switch_interval=3):
        self._values = {
            "automation_enabled": True,
            "combine_logic": "temp_override",
            "temp_hysteresis": 2,
            "min_switch_interval": min_switch_interval,
            "channels": channels,
        }

    def get(self, path):
        return self._values[path[0]]

    def get_boolean(self, path):
        return bool(self._values[path[0]])

    def get_int(self, path):
        return int(self._values[path[0]])


class _Ws:
    """Panda client stand-in: records commands, never broadcasts by itself."""

    connected = True

    def __init__(self, state):
        self.state = state
        self.sent = []

    def current_state(self):
        return {kind: dict(states) for kind, states in self.state.items()}

    def set_channel(self, kind, channel_id, on):
        self.sent.append((kind, int(channel_id), on))


class _Clock:
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now


@pytest.fixture(name="engine")
def fixture_engine(monkeypatch):
    channel = plugin_module._default_channel("mx24v", 3)
    channel["rules"].update({"prepare": "on", "printing": "on"})
    plugin = PandaBranchPlusPlugin()
    plugin._settings = _Settings([channel])
    plugin._logger = logging.getLogger("test.pandabranchplus")
    plugin._ws = _Ws({"mx24v": {3: 1}})
    plugin.printer_state = "idle"
    plugin._current_printer_state = lambda: plugin.printer_state
    plugin.scheduled = []
    plugin._schedule_reapply = plugin.scheduled.append
    clock = _Clock(100.0)
    monkeypatch.setattr(plugin_module.time, "monotonic", clock)
    plugin.clock = clock
    return plugin


def test_switches_back_on_before_the_panda_confirmed_the_off(engine):
    # Bambu double start: idle switches the channel off ...
    engine.apply_channel_rules("event PrinterStateChanged")
    assert engine._ws.sent == [("mx24v", 3, 0)]

    # ... and "prepare" follows 0.7 s later, before the Panda broadcast "off".
    engine.clock.now = 100.7
    engine.printer_state = "prepare"
    engine.apply_channel_rules("event PrinterStateChanged")
    assert engine._ws.sent == [("mx24v", 3, 0)]  # rate limited, not dropped
    assert engine.scheduled, "the switch back on must be retried"

    # The retry fires after min_switch_interval; by now the Panda confirmed.
    engine.clock.now = 103.2
    engine._ws.state = {"mx24v": {3: 0}}
    engine.apply_channel_rules("rate-limit retry")
    assert engine._ws.sent == [("mx24v", 3, 0), ("mx24v", 3, 1)]


def test_no_second_command_while_the_first_is_unconfirmed(engine):
    engine.apply_channel_rules("event PrinterStateChanged")
    engine.clock.now = 100.5
    engine.apply_channel_rules("temperatures")
    assert engine._ws.sent == [("mx24v", 3, 0)]
    assert engine.scheduled == []


def test_live_state_counts_again_after_the_confirm_window(engine):
    engine.apply_channel_rules("event PrinterStateChanged")
    # The "off" never took effect (lost command): the Panda still reports on.
    engine.clock.now = 100.0 + plugin_module.COMMAND_CONFIRM_WINDOW + 1
    engine.apply_channel_rules("temperatures")
    assert engine._ws.sent == [("mx24v", 3, 0), ("mx24v", 3, 0)]
