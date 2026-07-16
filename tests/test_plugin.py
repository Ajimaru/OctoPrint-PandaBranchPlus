"""Plugin-level surface: settings defaults and template registration.

Runs against the OctoPrint stubs from conftest.py — only pure methods of the
plugin class are exercised (no settings/printer injection needed).
"""

import octoprint_pandabranchplus as plugin_module
from octoprint_pandabranchplus import PandaBranchPlusPlugin
from octoprint_pandabranchplus.hardware import CHANNEL_LAYOUT


def _plugin():
    return PandaBranchPlusPlugin()


class TestSettingsDefaults:
    def test_sidebar_enabled_default_on(self):
        assert _plugin().get_settings_defaults()["sidebar_enabled"] is True

    def test_channels_match_hardware_layout(self):
        channels = _plugin().get_settings_defaults()["channels"]
        assert [(c["kind"], c["id"]) for c in channels] == [
            (c["kind"], c["id"]) for c in CHANNEL_LAYOUT
        ]

    def test_channel_defaults_are_safe(self):
        for channel in _plugin().get_settings_defaults()["channels"]:
            assert channel["mode"] == "auto"
            assert channel["manual_on"] is False
            assert channel["failsafe"] == "off"
            assert set(channel["rules"]) == set(plugin_module.PRINTER_STATES)
            assert all(v == "off" for v in channel["rules"].values())


class TestTemplateConfigs:
    def test_registers_tab_settings_and_sidebar(self):
        configs = _plugin().get_template_configs()
        assert [c["type"] for c in configs] == ["tab", "settings", "sidebar"]

    def test_sidebar_config(self):
        sidebar = [
            c for c in _plugin().get_template_configs() if c["type"] == "sidebar"
        ][0]
        assert sidebar["name"] == "Panda Branch Plus"
        assert sidebar["icon"] == "fas fa-plug"

    def test_template_vars_expose_layout_and_states(self):
        template_vars = _plugin().get_template_vars()
        assert template_vars["channel_layout"] == CHANNEL_LAYOUT
        assert template_vars["printer_states"] == plugin_module.PRINTER_STATES
