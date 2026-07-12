"""Smoke tests for the fixed channel layout.

Keeps CI meaningful while the plugin is still a skeleton: the layout is the
contract between settings defaults, the rule engine and the frontend.
"""

from octoprint_pandabranchplus.hardware import (
    CHANNEL_LAYOUT,
    CHANNEL_TYPES,
    channel_type,
)


def test_layout_has_ten_channels():
    assert len(CHANNEL_LAYOUT) == 10
    assert len(CHANNEL_TYPES) == 10


def test_layout_kinds_and_ids():
    usb = [c["id"] for c in CHANNEL_LAYOUT if c["kind"] == "usb"]
    mx = [c["id"] for c in CHANNEL_LAYOUT if c["kind"] == "mx24v"]
    assert usb == [1, 2, 3, 4, 5]
    assert mx == [1, 2, 3, 4, 5]


def test_layout_types_match_channel_type():
    for channel in CHANNEL_LAYOUT:
        assert channel["type"] == channel_type(channel["kind"], channel["id"])


def test_channel_type_unknown_returns_none():
    assert channel_type("usb", 6) is None
    assert channel_type("relay", 1) is None
