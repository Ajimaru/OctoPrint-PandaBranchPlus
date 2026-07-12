---
layout: plugin

id: pandabranchplus
title: OctoPrint-PandaBranchPlus
description: Assign functions to the 10 power channels of the BIQU Panda Branch Plus and automate them based on the printer state.
authors:
  - Ajimaru
license: AGPL-3.0-or-later

date: 2026-07-12

homepage: https://github.com/Ajimaru/OctoPrint-PandaBranchPlus
source: https://github.com/Ajimaru/OctoPrint-PandaBranchPlus
archive: https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/archive/main.zip

tags:
  - power
  - automation
  - psu
  - relay
  - bigtreetech
  - biqu
  - panda branch plus
  - bambu

# TODO before registering on plugins.octoprint.org: upload real screenshots
# (tab with channel cards, settings dialog) to /assets/img/ and list them here.
# screenshots:
#   - url: /assets/img/plugins/pandabranchplus/tab.png
#     alt: Channel cards with state matrix
#     caption: The plugin tab with per-channel automation rules
# featuredimage: /assets/img/plugins/pandabranchplus/tab.png

compatibility:
  octoprint:
    - 1.10.0

  os:
    - linux
    - windows
    - macos
    - freebsd

  python: ">=3.9,<4"
---

Control and automate the **BIQU Panda Branch Plus** power hub from OctoPrint:
all 10 outputs (5× Type-C, 5× MX3.0 24V) get a name, a live on/off state and
a small automation matrix in a dedicated tab.

## Features

- **State-driven automation** — per channel, choose what happens in each
  printer state (idle, preparing, printing, paused, error): on, off, or
  leave alone.
- **Temperature rules** — switch a channel at a bed/tool/chamber threshold,
  with hysteresis against flapping.
- **Manual override** — flip a channel to manual and toggle it directly;
  automation keeps its hands off until you switch back.
- **Live state** — the hub broadcasts every change; the tab updates without
  reload, including switches made outside OctoPrint.
- **Safety** — confirmation before switching on 24V outputs, per-channel
  fail-safe on shutdown, rate limiting, permission-gated API.
- **English & German UI**, following OctoPrint's language setting.

## Setup

Enter the Panda's host/IP under _Settings → Panda Branch Plus_ (the hub
itself, not the printer) and hit **Test connection**. Everything else has
sensible defaults; the per-channel rules live in the plugin tab.

The automation follows OctoPrint's standard printer state — for Bambu Lab
printers provide it via
[OctoPrint-BambuConnector](https://github.com/OctoPrint/OctoPrint-BambuConnector)
(OctoPrint 2.0). Without a state source the printer counts as idle and manual
control keeps working.

**Note:** the Panda's own WebSocket interface has no authentication — anyone
on your LAN who can reach the hub can switch its channels, plugin or not.
Keep it on a trusted network segment.
