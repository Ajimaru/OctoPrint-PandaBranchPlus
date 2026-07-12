"""Test bootstrap helpers.

Unit tests run outside a real OctoPrint runtime. This file provides minimal
module stubs so importing the plugin package does not require OctoPrint or
Flask to be installed.
"""

import sys
import types


def _ensure_module(name):
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    return mod


# Minimal Flask stub (only needed so import succeeds).
_ensure_module("flask")


# Minimal OctoPrint module tree for class definitions in __init__.py.
octoprint = _ensure_module("octoprint")
plugin = _ensure_module("octoprint.plugin")
printer = _ensure_module("octoprint.printer")
filemanager = _ensure_module("octoprint.filemanager")
access = _ensure_module("octoprint.access")
permissions = _ensure_module("octoprint.access.permissions")
events = _ensure_module("octoprint.events")


class _SettingsPlugin:
    pass


class _AssetPlugin:
    pass


class _TemplatePlugin:
    pass


class _StartupPlugin:
    pass


class _EventHandlerPlugin:
    pass


class _SimpleApiPlugin:
    pass


class _PrinterCallback:
    pass


setattr(plugin, "SettingsPlugin", _SettingsPlugin)
setattr(plugin, "AssetPlugin", _AssetPlugin)
setattr(plugin, "TemplatePlugin", _TemplatePlugin)
setattr(plugin, "StartupPlugin", _StartupPlugin)
setattr(plugin, "EventHandlerPlugin", _EventHandlerPlugin)
setattr(plugin, "SimpleApiPlugin", _SimpleApiPlugin)
setattr(printer, "PrinterCallback", _PrinterCallback)
setattr(permissions, "Permissions", object())


class _Events:
    PRINTER_STATE_CHANGED = "PRINTER_STATE_CHANGED"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    PRINT_FAILED = "PRINT_FAILED"


setattr(events, "Events", _Events)


# Wire parent/child references used by attribute access.
setattr(octoprint, "plugin", plugin)
setattr(octoprint, "printer", printer)
setattr(octoprint, "filemanager", filemanager)
setattr(octoprint, "access", access)
setattr(access, "permissions", permissions)
setattr(octoprint, "events", events)
