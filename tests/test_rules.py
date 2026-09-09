"""Unit tests for the pure rule engine (octoprint_pandabranchplus.rules)."""

from octoprint_pandabranchplus.rules import (
    evaluate_temp_rule,
    map_octoprint_state,
    resolve_target,
)


def channel(**overrides):
    base = {
        "kind": "mx24v",
        "id": 1,
        "mode": "auto",
        "manual_on": False,
        "rules": {
            "idle": "off",
            "prepare": "on",
            "printing": "on",
            "paused": "ignore",
            "error": "off",
        },
        "temp_rule": {
            "enabled": False,
            "sensor": "bed",
            "threshold": 40,
            "above": "on",
        },
    }
    base.update(overrides)
    return base


class TestStateMatrix:
    def test_state_rule_on(self):
        target, _ = resolve_target(channel(), "printing", {}, False)
        assert target == "on"

    def test_state_rule_off(self):
        target, _ = resolve_target(channel(), "idle", {}, False)
        assert target == "off"

    def test_ignore_leaves_channel_alone(self):
        target, _ = resolve_target(channel(), "paused", {}, False)
        assert target is None

    def test_unknown_state_defaults_off(self):
        target, _ = resolve_target(channel(rules={}), "printing", {}, False)
        assert target == "off"


class TestManualMode:
    def test_manual_on_wins_over_rules(self):
        target, _ = resolve_target(
            channel(mode="manual", manual_on=True), "idle", {}, False
        )
        assert target == "on"

    def test_manual_off_wins_over_rules(self):
        target, _ = resolve_target(
            channel(mode="manual", manual_on=False), "printing", {}, False
        )
        assert target == "off"


class TestTempRule:
    def rule(self, **overrides):
        base = {"enabled": True, "sensor": "bed", "threshold": 40, "above": "on"}
        base.update(overrides)
        return base

    def test_disabled_has_no_opinion(self):
        active, target = evaluate_temp_rule(
            self.rule(enabled=False), {"bed": 99}, False, 2
        )
        assert (active, target) == (False, None)

    def test_activates_at_threshold(self):
        active, target = evaluate_temp_rule(self.rule(), {"bed": 40}, False, 2)
        assert (active, target) == (True, "on")

    def test_inactive_below_threshold(self):
        active, target = evaluate_temp_rule(self.rule(), {"bed": 39.9}, False, 2)
        assert (active, target) == (False, None)

    def test_hysteresis_holds_until_dead_band(self):
        # active at 41, drops to 38.5 -> still active (40 - 2 = 38 dead band)
        active, _ = evaluate_temp_rule(self.rule(), {"bed": 38.5}, True, 2)
        assert active is True
        # drops to 38 -> released
        active, target = evaluate_temp_rule(self.rule(), {"bed": 38}, True, 2)
        assert (active, target) == (False, None)

    def test_missing_sensor_keeps_previous_verdict(self):
        active, target = evaluate_temp_rule(self.rule(), {}, True, 2)
        assert (active, target) == (True, "on")
        active, target = evaluate_temp_rule(self.rule(), {}, False, 2)
        assert (active, target) == (False, None)

    def test_above_off_acts_as_cutoff(self):
        active, target = evaluate_temp_rule(
            self.rule(above="off"), {"bed": 80}, False, 2
        )
        assert (active, target) == (True, "off")


class TestCombineLogic:
    def hot_channel(self, **overrides):
        return channel(
            temp_rule={
                "enabled": True,
                "sensor": "bed",
                "threshold": 40,
                "above": "on",
            },
            **overrides,
        )

    def test_temp_override_replaces_state_verdict(self):
        # idle says off, active temp rule says on -> on
        target, active = resolve_target(
            self.hot_channel(), "idle", {"bed": 50}, False, "temp_override"
        )
        assert (target, active) == ("on", True)

    def test_temp_override_falls_back_when_inactive(self):
        target, active = resolve_target(
            self.hot_channel(), "printing", {"bed": 20}, False, "temp_override"
        )
        assert (target, active) == ("on", False)

    def test_and_needs_both(self):
        # printing says on, temp active says on -> on
        target, _ = resolve_target(
            self.hot_channel(), "printing", {"bed": 50}, False, "and"
        )
        assert target == "on"
        # idle says off, temp says on -> off
        target, _ = resolve_target(
            self.hot_channel(), "idle", {"bed": 50}, False, "and"
        )
        assert target == "off"

    def test_or_needs_one(self):
        target, _ = resolve_target(self.hot_channel(), "idle", {"bed": 50}, False, "or")
        assert target == "on"

    def test_manual_ignores_temp_rule(self):
        target, _ = resolve_target(
            self.hot_channel(mode="manual", manual_on=False),
            "printing",
            {"bed": 99},
            False,
        )
        assert target == "off"


class TestStateMapping:
    def test_mapping(self):
        assert map_octoprint_state("STARTING") == "prepare"
        assert map_octoprint_state("PRINTING") == "printing"
        assert map_octoprint_state("RESUMING") == "printing"
        assert map_octoprint_state("PAUSED") == "paused"
        assert map_octoprint_state("ERROR") == "error"
        assert map_octoprint_state("CLOSED_WITH_ERROR") == "error"
        assert map_octoprint_state("OPERATIONAL") == "idle"
        assert map_octoprint_state("OFFLINE") == "idle"
        assert map_octoprint_state(None) == "idle"

    def test_busy_states_are_not_idle(self):
        # The printer is still parking and cooling down while cancelling,
        # and still receiving the job while transferring -- neither may
        # fall through to "idle" and cut the power.
        assert map_octoprint_state("CANCELLING") == "printing"
        assert map_octoprint_state("FINISHING") == "printing"
        assert map_octoprint_state("PAUSING") == "paused"
        assert map_octoprint_state("TRANSFERRING_FILE") == "prepare"

    def test_every_connected_printer_state_is_covered(self):
        # Every member of OctoPrint's ConnectedPrinterState enum, mirrored
        # here because importing it standalone trips a circular import.
        # Guards against states silently mapping to "idle"; only genuinely
        # non-busy ones may do so.
        idle_states = {"DETECTING", "CONNECTING", "OPERATIONAL", "CLOSED"}
        busy_states = {
            "STARTING",
            "PRINTING",
            "PAUSING",
            "PAUSED",
            "RESUMING",
            "CANCELLING",
            "FINISHING",
            "ERROR",
            "CLOSED_WITH_ERROR",
            "TRANSFERRING_FILE",
        }
        for name in idle_states:
            assert map_octoprint_state(name) == "idle", name
        for name in busy_states:
            assert map_octoprint_state(name) != "idle", name
