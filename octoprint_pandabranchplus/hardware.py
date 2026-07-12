"""Fixed hardware layout of the Panda Branch Plus.

The Panda has 10 switchable outputs the firmware exposes under two WebSocket
roots: ``usb`` (5x Type-C) and ``mx24v`` (5x MX3.0 24V). The channel *type* is
fixed by the hardware and is shown as a badge in the UI; only the label is
user-editable. Verified layout: see ``.ideas/panda-branch-plus-recon.md``.
"""

# (kind, id) -> human-readable type shown as a badge. Ratings per the
# manufacturer wiki (https://global.bttwiki.com/Panda_Branch_Plus.html):
# all Type-C ports are 5V; port 1 delivers 5A (meant for a Panda Hub Plus),
# ports 2-5 deliver 1.5A. MX3.0 ports are 24V/2A.
CHANNEL_TYPES = {
    ("usb", 1): "Type-C 5A",
    ("usb", 2): "Type-C 1.5A",
    ("usb", 3): "Type-C 1.5A",
    ("usb", 4): "Type-C 1.5A",
    ("usb", 5): "Type-C 1.5A",
    ("mx24v", 1): "MX3.0 24V",
    ("mx24v", 2): "MX3.0 24V",
    ("mx24v", 3): "MX3.0 24V",
    ("mx24v", 4): "MX3.0 24V",
    ("mx24v", 5): "MX3.0 24V",
}

# Ordered list used to render the tab and seed default settings.
CHANNEL_LAYOUT = [
    {"kind": kind, "id": channel_id, "type": type_name}
    for (kind, channel_id), type_name in CHANNEL_TYPES.items()
]


def channel_type(kind, channel_id):
    """Return the fixed type string for a channel, or ``None`` if unknown."""
    return CHANNEL_TYPES.get((kind, channel_id))
