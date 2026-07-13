import logging
import threading
import time
from typing import TYPE_CHECKING

import flask
import octoprint.plugin

try:
    import octoprint.printer
except ImportError:
    # OctoPrint 2.0.x: octoprint.printer has a circular import with
    # octoprint.filemanager when it is the first octoprint module imported
    # (only hit outside a running server, e.g. in tests). Importing
    # filemanager first breaks the cycle; the retry below then succeeds.
    import octoprint.filemanager  # noqa: F401
    import octoprint.printer
from octoprint.access.permissions import Permissions
from octoprint.events import Events

from . import panda_ws, rules
from ._version import VERSION as _PLUGIN_VERSION
from .hardware import CHANNEL_LAYOUT

if TYPE_CHECKING:
    from octoprint.plugin import PluginSettings
    from octoprint.plugin.core import PluginManager
    from octoprint.printer import PrinterInterface

# The five printer states the automation matrix maps to on/off/ignore.
PRINTER_STATES = ["idle", "prepare", "printing", "paused", "error"]


def _default_channel(kind, channel_id):
    """Build the default per-channel config for a hardware channel.

    ``rules`` default to "off" for every state, ``mode`` to auto. New channels
    inherit the global safe-default (applied at runtime, not stored here).
    """
    return {
        "kind": kind,
        "id": channel_id,
        "label": f"{'USB' if kind == 'usb' else 'MX'} {channel_id}",
        "mode": "auto",  # "auto" | "manual"
        "manual_on": False,
        "rules": {state: "off" for state in PRINTER_STATES},  # "on"|"off"|"ignore"
        "temp_rule": {
            "enabled": False,
            "sensor": "bed",  # "bed"|"tool"|"chamber"|"panda"
            "threshold": 40,
            "above": "on",  # "on"|"off"
        },
        "failsafe": "off",  # "off"|"on"|"hold"
    }


class PandaBranchPlusPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.SimpleApiPlugin,
    # Registered as printer callback in on_after_startup; the base class
    # provides no-op defaults for every method the printer pushes (we only
    # override on_printer_add_temperature).
    octoprint.printer.PrinterCallback,
):
    # Injected by OctoPrint when the plugin loads (the base class initializes
    # them to None, which is what type checkers would otherwise infer).
    _identifier: str
    _logger: logging.Logger
    _settings: "PluginSettings"
    _plugin_manager: "PluginManager"
    _printer: "PrinterInterface"
    _plugin_version: str

    def __init__(self):
        super().__init__()
        # Long-lived WebSocket client to the Panda (see panda_ws.py). Created in
        # on_after_startup once the host is configured.
        self._ws = None
        # Rule-engine runtime state (never persisted).
        self._temps = {}  # last known temps: {"bed": .., "tool": .., "chamber": ..}
        self._temp_active = {}  # per-channel hysteresis latch: {(kind, id): bool}
        self._last_switch = {}  # per-channel rate limit: {(kind, id): timestamp}
        self._startup_synced = False  # startup_behaviour applied on first connect
        self._reapply_timer = None  # pending re-run after a rate-limited switch

    # SettingsPlugin mixin

    def get_settings_defaults(self):
        return {
            # Connection
            "host": "",
            "ws_port": 80,
            "ws_path": "/ws",
            "reconnect_min": 1,
            "reconnect_max": 30,
            # Automation (global)
            "automation_enabled": True,
            "combine_logic": "temp_override",  # "temp_override" | "and" | "or"
            "temp_hysteresis": 2,
            "min_switch_interval": 3,
            # Safety
            "confirm_high_power": True,
            "startup_behaviour": "leave",  # "leave" | "all_off" | "restore"
            # Diagnostics
            "debug_logging": False,
            "frame_log": False,
            # Per-channel config (10 channels, order = CHANNEL_LAYOUT)
            "channels": [_default_channel(c["kind"], c["id"]) for c in CHANNEL_LAYOUT],
        }

    # TemplatePlugin mixin

    def get_template_configs(self):
        return [
            {"type": "tab", "name": "Panda Branch Plus"},
            {"type": "settings", "name": "Panda Branch Plus"},
        ]

    def is_template_autoescaped(self):
        # Our templates only ever render _() strings and KO bindings.
        return True

    def get_template_vars(self):

        # Expose the fixed hardware layout so the tab can render type badges
        # without hardcoding them in the template.
        return {
            "channel_layout": CHANNEL_LAYOUT,
            "printer_states": PRINTER_STATES,
        }

    # AssetPlugin mixin

    def get_assets(self):
        return {
            "js": ["js/pandabranchplus.js"],
            "css": ["css/pandabranchplus.css"],
            "less": ["less/pandabranchplus.less"],
        }

    def on_settings_save(self, data):
        old = self._connection_settings()
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self._apply_log_level()
        if self._connection_settings() != old:
            self._logger.info("Panda connection settings changed, reconnecting")
            self._restart_ws()
        else:
            # Automation settings may have changed -> re-evaluate immediately.
            self.apply_channel_rules("settings saved")

    # StartupPlugin mixin

    def on_after_startup(self):
        self._apply_log_level()
        # Temperature feed for the temp rules (on_printer_add_temperature).
        self._printer.register_callback(self)
        self._restart_ws()

    def on_shutdown(self):
        self._apply_failsafe("shutdown")
        self._stop_ws()

    def _apply_log_level(self):
        level = (
            logging.DEBUG
            if self._settings.get_boolean(["debug_logging"])
            else logging.INFO
        )
        self._logger.setLevel(level)

    # Panda WebSocket client lifecycle

    def _connection_settings(self):
        return (
            self._settings.get(["host"]),
            self._settings.get_int(["ws_port"]),
            self._settings.get(["ws_path"]),
        )

    def _restart_ws(self):
        self._stop_ws()
        host = (self._settings.get(["host"]) or "").strip()
        if not host:
            self._logger.info("No Panda host configured, WS client not started")
            self._push_connection(False)
            return
        self._ws = panda_ws.PandaWsClient(
            self._logger,
            host,
            port=self._settings.get_int(["ws_port"]),
            path=self._settings.get(["ws_path"]) or "/ws",
            on_state=self._on_ws_state,
            on_connection=self._on_ws_connection,
            reconnect_min=self._settings.get_int(["reconnect_min"]),
            reconnect_max=self._settings.get_int(["reconnect_max"]),
            frame_log=self._settings.get_boolean(["frame_log"]),
        )
        self._ws.start()

    def _stop_ws(self):
        if self._ws is not None:
            self._ws.stop()
            self._ws = None

    def _on_ws_state(self, channels):
        # Live channel state push from the Panda -> browser.
        self._plugin_manager.send_plugin_message(
            self._identifier, {"type": "state", "channels": channels}
        )

    def _on_ws_connection(self, connected):
        self._push_connection(connected)
        if connected:
            # Bring channels back to a defined state (channels may have been
            # switched externally while we were away).
            self._initial_sync()

    def _push_connection(self, connected):
        self._plugin_manager.send_plugin_message(
            self._identifier, {"type": "connection", "connected": connected}
        )

    # EventHandlerPlugin mixin

    def on_event(self, event, payload):
        # PrinterStateChanged covers the whole print lifecycle (the canonical
        # state is re-derived from the printer anyway); Connected/Disconnected
        # matter because "no printer" counts as idle.
        if event in (
            Events.PRINTER_STATE_CHANGED,
            Events.CONNECTED,
            Events.DISCONNECTED,
            Events.PRINT_FAILED,
        ):
            self.apply_channel_rules(f"event {event}")

    # PrinterCallback (registered in on_after_startup)

    def on_printer_add_temperature(self, data):
        # data: {"time": .., "bed": {"actual": ..}, "tool0": {..}, "chamber": {..}}
        for source, key in (("bed", "bed"), ("tool0", "tool"), ("chamber", "chamber")):
            entry = data.get(source)
            if isinstance(entry, dict) and entry.get("actual") is not None:
                self._temps[key] = entry["actual"]
        # Only run the engine on temp ticks if some channel actually has a
        # temp rule — this callback fires roughly once a second.
        if any(
            (c.get("temp_rule") or {}).get("enabled")
            for c in self._settings.get(["channels"])
        ):
            self.apply_channel_rules("temperatures")

    # SimpleApiPlugin mixin

    def get_api_commands(self):
        return {
            "set_channel": ["kind", "id", "on"],  # manual toggle
            "set_mode": ["kind", "id", "mode"],  # auto <-> manual
            "set_label": ["kind", "id", "label"],  # rename a channel
            "set_channel_config": ["kind", "id"],  # rules / temp_rule / failsafe
            "test_connection": [],
        }

    def is_api_protected(self):
        # Power switching stays behind OctoPrint's authentication.
        return True

    def on_api_get(self, request):
        # Initial state for the tab: connection status + last known channels.
        if not Permissions.STATUS.can():
            flask.abort(403)
        connected = self._ws is not None and self._ws.connected
        channels = self._ws.current_state() if self._ws is not None else {}
        return flask.jsonify(
            connected=connected, channels=channels, layout=CHANNEL_LAYOUT
        )

    def on_api_command(self, command, data):
        if not Permissions.CONTROL.can():
            flask.abort(403)

        if command == "test_connection":
            # Test against the values from the dialog (possibly unsaved),
            # falling back to the stored settings.
            host = (data.get("host") or self._settings.get(["host"]) or "").strip()
            if not host:
                return flask.jsonify(ok=False, reason="no_host")
            port = data.get("port") or self._settings.get_int(["ws_port"])
            path = data.get("path") or self._settings.get(["ws_path"]) or "/ws"
            try:
                result = panda_ws.test_connection(host, port=port, path=path)
            except panda_ws.PandaWsError as exc:
                self._logger.warning("Panda connection test failed: %s", exc)
                return flask.jsonify(ok=False, reason=exc.reason)
            channel_count = sum(len(v) for v in result["channels"].values())
            return flask.jsonify(ok=True, channels=channel_count)

        if command == "set_channel":
            if self._ws is None or not self._ws.connected:
                return flask.jsonify(ok=False, reason="not_connected")
            kind, channel_id = data["kind"], data["id"]
            if not any(
                c["kind"] == kind and c["id"] == int(channel_id) for c in CHANNEL_LAYOUT
            ):
                flask.abort(400, description="unknown channel")
            on = bool(data["on"])
            try:
                self._ws.set_channel(kind, channel_id, on)
            except panda_ws.PandaWsError as exc:
                self._logger.warning(
                    "Panda set_channel failed for %s/%s: %s", kind, channel_id, exc
                )
                return flask.jsonify(ok=False, reason=exc.reason)
            # A toggle on a manual channel is remembered so the state survives
            # restarts (startup_behaviour "restore") and reconnect syncs.
            channel = self._find_channel(kind, channel_id)
            if channel is not None and channel.get("mode") == "manual":
                self._update_channel_config(kind, channel_id, {"manual_on": on})
            return flask.jsonify(ok=True)

        if command == "set_mode":
            mode = data["mode"]
            if mode not in ("auto", "manual"):
                flask.abort(400, description="unknown mode")
            self._update_channel_config(data["kind"], data["id"], {"mode": mode})
            # Mode changes take effect immediately (manual enforces manual_on,
            # auto re-applies the matrix).
            self.apply_channel_rules("mode changed")
            return flask.jsonify(ok=True)

        if command == "set_label":
            label = str(data["label"]).strip()[:64]
            self._update_channel_config(data["kind"], data["id"], {"label": label})
            return flask.jsonify(ok=True, label=label)

        if command == "set_channel_config":
            fields = self._validated_config_fields(data)
            self._update_channel_config(data["kind"], data["id"], fields)
            self.apply_channel_rules("channel config changed")
            return flask.jsonify(ok=True)

        # Unreachable: OctoPrint validates commands against get_api_commands.
        return None

    def _validated_config_fields(self, data):
        """Whitelist and validate the editable fields of set_channel_config."""
        fields = {}
        if "rules" in data:
            rules_in = data["rules"] or {}
            fields["rules"] = {
                state: (
                    rules_in.get(state)
                    if rules_in.get(state) in ("on", "off", "ignore")
                    else "off"
                )
                for state in PRINTER_STATES
            }
        if "temp_rule" in data:
            rule = data["temp_rule"] or {}
            try:
                threshold = float(rule.get("threshold", 40))
            except (TypeError, ValueError):
                threshold = 40
            fields["temp_rule"] = {
                "enabled": bool(rule.get("enabled")),
                "sensor": (
                    rule.get("sensor")
                    if rule.get("sensor") in ("bed", "tool", "chamber")
                    else "bed"
                ),
                "threshold": threshold,
                "above": (
                    rule.get("above") if rule.get("above") in ("on", "off") else "on"
                ),
            }
        if "failsafe" in data:
            fields["failsafe"] = (
                data["failsafe"] if data["failsafe"] in ("off", "on", "hold") else "off"
            )
        if not fields:
            flask.abort(400, description="no valid fields")
        return fields

    def _find_channel(self, kind, channel_id):
        for channel in self._settings.get(["channels"]):
            if channel["kind"] == kind and channel["id"] == int(channel_id):
                return channel
        return None

    def _update_channel_config(self, kind, channel_id, fields):
        """Set fields of a channel's stored config and persist them."""
        channels = self._settings.get(["channels"])
        for channel in channels:
            if channel["kind"] == kind and channel["id"] == int(channel_id):
                channel.update(fields)
                break
        else:
            flask.abort(400, description="unknown channel")
        self._settings.set(["channels"], channels)
        self._settings.save()

    # Rule engine

    def _current_printer_state(self):
        """The plugin's canonical printer state (no printer = idle)."""
        try:
            state_id = self._printer.get_state_id()
        except Exception:
            state_id = None
        return rules.map_octoprint_state(state_id)

    def apply_channel_rules(self, reason=""):
        """Resolve every channel's target on/off and switch where needed.

        Manual channels follow manual_on; auto channels follow the state
        matrix combined with their temp rule (see rules.py). Only channels
        whose target differs from the live state get a WS command, rate
        limited per channel by min_switch_interval.
        """
        if not self._settings.get_boolean(["automation_enabled"]):
            return
        if self._ws is None or not self._ws.connected:
            return

        state = self._current_printer_state()
        combine = self._settings.get(["combine_logic"])
        hysteresis = self._settings.get_int(["temp_hysteresis"])
        min_interval = self._settings.get_int(["min_switch_interval"])
        live = self._ws.current_state()
        self._logger.debug(
            "Applying channel rules (state=%s, reason=%s)", state, reason
        )

        for channel in self._settings.get(["channels"]):
            key = (channel["kind"], int(channel["id"]))
            target, temp_active = rules.resolve_target(
                channel,
                state,
                self._temps,
                self._temp_active.get(key, False),
                combine_logic=combine,
                hysteresis=hysteresis,
            )
            self._temp_active[key] = temp_active
            if target is None:
                continue
            current = live.get(channel["kind"], {}).get(int(channel["id"]))
            want = 1 if target == "on" else 0
            if current == want:
                continue
            now = time.monotonic()
            remaining = min_interval - (now - self._last_switch.get(key, 0))
            if remaining > 0:
                # Rate limited: don't drop the switch, retry once the
                # interval has passed (coalesced into a single timer).
                self._logger.debug(
                    "Rate limit: deferring %s %s for %.1fs", key[0], key[1], remaining
                )
                self._schedule_reapply(remaining)
                continue
            try:
                self._ws.set_channel(channel["kind"], channel["id"], want)
                self._last_switch[key] = now
                self._logger.info(
                    "Rule engine: %s %s -> %s (state=%s)",
                    channel["kind"],
                    channel["id"],
                    target,
                    state,
                )
            except panda_ws.PandaWsError as exc:
                self._logger.warning(
                    "Switching %s %s failed: %s", channel["kind"], channel["id"], exc
                )

    def _schedule_reapply(self, delay):
        """Re-run the rules once after ``delay`` seconds (single pending timer)."""
        if self._reapply_timer is not None and self._reapply_timer.is_alive():
            return

        def _fire():
            self._reapply_timer = None
            self.apply_channel_rules("rate-limit retry")

        self._reapply_timer = threading.Timer(delay + 0.1, _fire)
        self._reapply_timer.daemon = True
        self._reapply_timer.start()

    def _initial_sync(self):
        """Bring channels to a defined state after (re)connecting to the Panda.

        On the first connect after plugin start, startup_behaviour is applied
        first (all_off switches everything off, restore enforces manual
        channels' remembered state). Then the normal rules run.
        """
        ws = self._ws
        if ws is None:
            # A settings-save reconnect can tear the client down between the
            # connect callback and this point.
            return
        if not self._startup_synced:
            self._startup_synced = True
            behaviour = self._settings.get(["startup_behaviour"])
            if behaviour == "all_off":
                for channel in self._settings.get(["channels"]):
                    try:
                        ws.set_channel(channel["kind"], channel["id"], 0)
                    except panda_ws.PandaWsError:
                        pass
            elif behaviour == "restore":
                for channel in self._settings.get(["channels"]):
                    if channel.get("mode") == "manual":
                        try:
                            ws.set_channel(
                                channel["kind"],
                                channel["id"],
                                1 if channel.get("manual_on") else 0,
                            )
                        except panda_ws.PandaWsError:
                            pass
        self.apply_channel_rules("initial sync")

    def _apply_failsafe(self, reason):
        """Best-effort: bring channels to their failsafe state.

        Only possible while the Panda is still reachable — used on plugin/host
        shutdown. A lost connection cannot be failsafed from here (nothing to
        send to); the reconnect's initial sync covers that case instead.
        """
        if self._ws is None or not self._ws.connected:
            return
        for channel in self._settings.get(["channels"]):
            failsafe = channel.get("failsafe", "off")
            if failsafe == "hold":
                continue
            try:
                self._ws.set_channel(
                    channel["kind"], channel["id"], 1 if failsafe == "on" else 0
                )
            except panda_ws.PandaWsError:
                pass
        self._logger.info("Failsafe applied (%s)", reason)

    # Softwareupdate hook

    def get_update_information(self):
        return {
            "pandabranchplus": {
                "displayName": "Panda Branch Plus",
                "displayVersion": self._plugin_version,
                "type": "github_release",
                "user": "Ajimaru",
                "repo": "OctoPrint-PandaBranchPlus",
                "current": self._plugin_version,
                "pip": "https://github.com/Ajimaru/OctoPrint-PandaBranchPlus"
                "/archive/{target_version}.zip",
            }
        }


__plugin_name__ = "Panda Branch Plus"
__plugin_version__ = _PLUGIN_VERSION
__plugin_pythoncompat__ = ">=3,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PandaBranchPlusPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": (
            __plugin_implementation__.get_update_information
        )
    }
