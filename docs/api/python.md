# Python API

Automatically generated from the source docstrings with
[mkdocstrings](https://mkdocstrings.github.io/). Run `mkdocs serve` to render
this page locally.

## Plugin

The OctoPrint plugin implementation: mixins, settings, SimpleAPI and the
rule application loop.

::: octoprint_pandabranchplus.PandaBranchPlusPlugin
options:
show_root_heading: true
members_order: source

## WebSocket client

The long-lived connection to the Panda: reconnect with backoff, TCP
keepalive, state parsing, error classification.

::: octoprint_pandabranchplus.panda_ws.PandaWsClient
options:
show_root_heading: true
members_order: source

::: octoprint_pandabranchplus.panda_ws.PandaWsError
options:
show_root_heading: true

::: octoprint_pandabranchplus.panda_ws.test_connection
options:
show_root_heading: true

## Rule engine

Pure functions — no OctoPrint imports, fully unit-tested.

::: octoprint_pandabranchplus.rules
options:
show_root_heading: true
members_order: source

## Hardware layout

::: octoprint_pandabranchplus.hardware
options:
show_root_heading: true
members_order: source
