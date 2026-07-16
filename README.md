<!-- markdownlint-disable MD041 MD033 -->
<p align="center">
  <img
    src="assets/img/pandabranchplus.svg"
    alt="OctoPrint PandaBranchPlus Logo"
    width="64"
    height="64"
  />
</p>
<h1 align="center">OctoPrint‑PandaBranchPlus</h1>
<!-- markdownlint-enable MD041 MD033 -->

[![License][badge-license]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/blob/main/LICENSE)
[![Python][badge-python]](https://python.org)
[![OctoPrint][badge-octoprint]](https://octoprint.org)
[![Latest Release][badge-release]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/releases/latest)
[![Latest Prerelease][badge-prerelease]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/releases)
[![Downloads][badge-downloads]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/releases)
[![Made with Love][badge-love]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus)

[badge-license]: https://img.shields.io/github/license/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[badge-python]: https://img.shields.io/badge/python-3.9%2B-blue.svg?style=flat-square
[badge-octoprint]: https://img.shields.io/badge/OctoPrint-1.10.0%2B-blue.svg?style=flat-square
[badge-release]: https://img.shields.io/github/v/release/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[badge-prerelease]: https://img.shields.io/github/v/release/Ajimaru/OctoPrint-PandaBranchPlus?include_prereleases&label=prerelease&style=flat-square
[badge-downloads]: https://img.shields.io/github/downloads/Ajimaru/OctoPrint-PandaBranchPlus/total.svg?style=flat-square
[badge-love]: https://img.shields.io/badge/made_with-%E2%9D%A4%EF%B8%8F-ff69b4?style=flat-square

### Automate the 10 power channels of the BIQU Panda Branch Plus — from inside OctoPrint

[![100% Vibe_Coded](https://img.shields.io/badge/100%25-Vibe_Coded-ff69b4?style=flat-square&logo=claude&logoColor=white)](https://github.com/ai-ecoverse/vibe-coded-badge-action)

> [!NOTE]
> **About this project.** I built this for my own printer setup with AI, and if
> it helps others, even better. The plugin is functional and tested against
> real hardware (Panda Branch Plus + A1 mini), but still **early in its
> release cycle** — expect rough edges. Disclosed here per the OctoPrint
> plugin guidelines. Issues and PRs are welcome.

## Highlights

- 🔌 **10 switchable channels** — All five Type‑C and five MX3.0 24V outputs
  of the Panda Branch Plus, controlled from a dedicated OctoPrint tab
- 🏷️ **Nameable channels with fixed type badges** — Call it "LED strip" or
  "Chamber fan"; the hardware type (Type‑C 5A, Type‑C 1.5A, MX3.0 24V) is
  always visible
- 🤖 **State‑driven automation** — Per channel, decide what happens in each
  printer state: idle, preparing, printing, paused, error — on, off, or leave
  alone
- 🌡️ **Temperature rules** — Switch a channel above/below a bed, tool or
  chamber temperature threshold, with hysteresis against flapping
- 🎛️ **Manual override** — Flip any channel to manual and toggle it directly;
  automation takes over again when you hand it back
- 🛟 **Fail‑safe on shutdown** — When OctoPrint shuts down, each channel is
  set to its configured fail‑safe state (off / on / hold); after a lost
  connection the reconnect re-applies the rules
- ⚡ **Live state** — Channel on/off state is pushed to the browser as it
  changes, no page reload
- 📋 **Sidebar status** — Minimal sidebar panel with one chip per channel:
  red border = on, green = off, yellow = state unknown; can be disabled in
  the settings
- 🧪 **Connection test** — Verify the Panda's host/IP before saving settings
- 🔒 **Permission‑gated** — Switching power is restricted through OctoPrint's
  access control
- 🌐 **English & German UI** — Follows OctoPrint's own language setting, with
  (?) tooltips on every setting

## Supported hardware

<!-- markdownlint-disable MD013 -->

| Channel group | Count | Type             | Switchable | Tested |
| ------------- | :---: | ---------------- | :--------: | :----: |
| `usb` 1       |   1   | Type‑C 5V / 5A   |     ✅     |   ✅   |
| `usb` 2–5     |   4   | Type‑C 5V / 1.5A |     ✅     |   ✅   |
| `mx24v` 1–5   |   5   | MX3.0 24V / 2A   |     ✅     |   ✅   |

Ratings per the
[manufacturer wiki](https://global.bttwiki.com/Panda_Branch_Plus.html)

<!-- markdownlint-enable MD013 -->

The plugin talks to the **Panda Branch Plus** itself (ESP32‑S3 power hub by
BIQU/BigTreeTech) over its local WebSocket interface. The printer state that
drives the automation comes from OctoPrint's own state machine — for Bambu Lab
printers fed by
[OctoPrint-BambuConnector](https://github.com/OctoPrint/OctoPrint-BambuConnector).
Verified with an **A1 mini** behind the Panda; any printer whose state
OctoPrint tracks should work.

## Compatibility

PandaBranchPlus requires **OctoPrint ≥ 1.10.0**.

<!-- markdownlint-disable MD033 -->
<details>
<summary>OctoPrint 1.x vs. 2.0 — feature breakdown</summary>
</br>

The plugin itself runs on the OctoPrint 1.x series. The automation reacts to
OctoPrint's standard printer state, so what matters is _where that state comes
from_: for Bambu Lab printers it is provided by
[OctoPrint-BambuConnector](https://github.com/OctoPrint/OctoPrint-BambuConnector),
which is part of OctoPrint's 2.0 connector architecture.

<!-- markdownlint-disable MD013 -->

| Feature                                           | OctoPrint 1.x | OctoPrint 2.0 + Bambu Connector |
| ------------------------------------------------- | :-----------: | :-----------------------------: |
| Channel tab, naming, type badges                  |      ✅       |               ✅                |
| Manual channel control                            |      ✅       |               ✅                |
| Per‑channel fail‑safe on shutdown                 |      ✅       |               ✅                |
| Connection test                                   |      ✅       |               ✅                |
| State‑driven automation (classic serial printers) |      ✅       |               ✅                |
| State‑driven automation (Bambu Lab printers)      |      ❌       |               ✅                |
| Temperature rules (bed / tool)                    |      ✅       |               ✅                |
| Temperature rules (chamber)                       |      ❌       |               ✅                |

<!-- markdownlint-enable MD013 -->

Without a state source the automation simply treats the printer as idle;
manual control keeps working. Nothing errors.

</details>
<!-- markdownlint-enable MD033 -->

## Installation

### Via Plugin Manager (Recommended)

1. Open the OctoPrint web interface
2. Navigate to **Settings** → **Plugin Manager**
3. Click **Get More...**
4. Click **Install from URL** and enter:

   ```text
   https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/releases/latest/download/OctoPrint-PandaBranchPlus-latest.zip
   ```

5. Click **Install**
6. Restart OctoPrint

### Manual Installation

<!-- markdownlint-disable MD033 -->
<details>
<summary>Manual pip install</summary>

```bash
pip install https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/releases/latest/download/OctoPrint-PandaBranchPlus-latest.zip
```

The `releases/latest` URL always points to the newest stable release.

</details>
<!-- markdownlint-enable MD033 -->

## Configuration

Open **Settings → Plugins → Panda Branch Plus**, enter the Panda's host/IP
(the hub itself, **not** the printer — there is no auto-detect) and hit
**Test connection**. Everything else has sensible defaults and is optional;
the per‑channel rules live in the plugin tab.

<!-- markdownlint-disable MD033 -->
<details>
<summary>Required &amp; optional settings</summary>
</br>

| Setting             | Description                                         |
| ------------------- | --------------------------------------------------- |
| **Panda host / IP** | LAN address of the Panda hub, e.g. `192.168.73.42`. |

Use **Test connection** to verify the value before saving.

> ⚠️ The Panda's own WebSocket interface has **no authentication** — anyone on
> your network who can reach the hub's IP can switch its channels, plugin or
> not. Keep the Panda on a trusted network segment. See
> [SECURITY.md](SECURITY.md).

<h4>Optional settings</h4>

<!-- markdownlint-disable MD013 -->

| Setting             | Default         | Description                                     |
| ------------------- | --------------- | ----------------------------------------------- |
| WebSocket port      | `80`            | Advanced — only if the firmware differs.        |
| WebSocket path      | `/ws`           | Advanced — only if the firmware differs.        |
| Reconnect min/max   | `1 s` / `30 s`  | Backoff window for automatic reconnects.        |
| Automation enabled  | on              | Master switch for all state/temperature rules.  |
| Combine logic       | `temp_override` | How temperature rules combine with state rules. |
| Temp hysteresis     | `2 °C`          | Dead band around thresholds against flapping.   |
| Min switch interval | `3 s`           | Rate limit per channel against rapid toggling.  |
| Confirm high power  | on              | Ask before manually switching on 24V channels.  |
| Startup behaviour   | `leave`         | First connect: apply rules / all off / restore. |
| Debug logging       | off             | Verbose plugin log.                             |
| Frame log           | off             | Log raw WebSocket frames (diagnostics only).    |

Per‑channel fail‑safe, the state matrix and temperature rules are configured
directly **in the plugin tab**, next to the live channel state.

<!-- markdownlint-enable MD013 -->

</details>
<!-- markdownlint-enable MD033 -->

## Channel automation

Every channel has a small **state matrix**: for each printer state — _idle_,
_preparing_, _printing_, _paused_, _error_ — pick **on**, **off** or
**ignore** (leave the channel as it is). Typical setups:

- **LED strip** on `usb`: on while preparing/printing, off when idle.
- **Exhaust fan** on `mx24v`: on while printing, keep running on pause, off a
  few states later via the idle rule.
- **Drying box**: driven purely by a temperature rule, independent of the
  print state.

Rules are evaluated on every state change and only send a switch command when
the target differs from the channel's live state — no command spam. An
optional **temperature rule** per channel (bed / tool / chamber threshold with
hysteresis) can override or combine with the state matrix.

## Manual control & fail-safe

- Each channel can be flipped to **manual mode**; the toggle in the tab then
  switches it immediately, and automation leaves it alone until you switch
  back to auto.
- Manual switching of **24V channels** asks for confirmation first
  (configurable) — that is where heaters and pumps live.
- If the WebSocket connection to the Panda drops, a **"Panda disconnected"**
  banner appears; the channels physically hold their last state (an
  unreachable hub cannot be commanded). On reconnect the plugin re-syncs and
  re-applies the rules.
- On OctoPrint **shutdown**, each channel is set to its per‑channel
  **fail‑safe** state — off, on, or hold (default: **off**).

## Security notes

The plugin stores no credentials — the Panda's interface has none. Switching
channels through the plugin is permission‑gated via OctoPrint's access
control; the unauthenticated device interface itself is a property of the
Panda firmware, not of this plugin. See the
**[Security model](SECURITY.md#security-model)** in [SECURITY.md](SECURITY.md)
for the full posture and how to report a vulnerability.

## How it works

The plugin keeps **one persistent WebSocket connection** to the Panda Branch
Plus (`ws://<panda-host>/ws`) with automatic reconnect and backoff. Channels
are switched with small JSON commands (`{"usb": {"id": 2, "on": 1}}`), and the
Panda answers every connection with a full state snapshot, which the plugin
mirrors live into the browser.

The **printer state** that drives the automation is read entirely from
OctoPrint's standard events and printer interface — the plugin never talks to
the printer itself. For Bambu Lab printers that state is provided by
[OctoPrint-BambuConnector](https://github.com/OctoPrint/OctoPrint-BambuConnector).

(The Panda additionally acts as a transparent MQTT proxy between a Bambu Lab
printer and the LAN — the plugin doesn't use that path, but it is documented
for the curious.)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for
detailed guidelines and instructions.

Please also follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

AGPL-3.0-or-later — see [LICENSE](LICENSE) for details.

See [AUTHORS.md](AUTHORS.md) for acknowledgements and [CHANGELOG.md](CHANGELOG.md)
for release history.

## Support

- 🐛 **Bug Reports**: [GitHub Issues][issues]
- 💬 **Discussion**: [GitHub Discussions][discussions]
- 📚 **Developer docs**: [ajimaru.github.io/OctoPrint-PandaBranchPlus](https://ajimaru.github.io/OctoPrint-PandaBranchPlus/)

[issues]: https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/issues
[discussions]: https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/discussions

For troubleshooting, check the PandaBranchPlus log at
**Settings → Logging → octoprint.plugins.pandabranchplus** and attach the
OctoPrint systeminfo bundle when opening a bug report.

## Credits

- **Development**: Built following
  [OctoPrint Plugin Guidelines](https://docs.octoprint.org/en/main/plugins/index.html)
- **Hardware**: [Panda Branch Plus](https://global.bttwiki.com/Panda_Branch_Plus.html)
  by BIQU / BigTreeTech
- **Patterns**: Connection handling and live-push patterns adapted from
  [OctoPrint-BambuCam](https://github.com/Ajimaru/OctoPrint-BambuCam)
- **Contributors**: See [AUTHORS.md](AUTHORS.md)

## 100% Badge Coverage

<!-- markdownlint-disable MD033 -->
<details>
<summary>Show all badges</summary>

### 🏗️ 1. Build & Test Status

[![CI][b-ci]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/actions/workflows/ci.yml?query=branch%3Amain)
[![Docs workflow][b-docs]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/actions/workflows/docs.yml?query=branch%3Amain)
[![i18n][b-i18n]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/actions/workflows/i18n.yml?query=branch%3Amain)
[![Lint][b-lint]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/actions/workflows/lint.yml?query=branch%3Amain)
[![Bandit SARIF][b-bandit]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/actions/workflows/bandit-sarif.yml?query=branch%3Amain)

[b-ci]: https://img.shields.io/github/actions/workflow/status/Ajimaru/OctoPrint-PandaBranchPlus/ci.yml?branch=main&style=flat-square&label=CI
[b-docs]: https://img.shields.io/github/actions/workflow/status/Ajimaru/OctoPrint-PandaBranchPlus/docs.yml?branch=main&style=flat-square&label=Docs
[b-i18n]: https://img.shields.io/github/actions/workflow/status/Ajimaru/OctoPrint-PandaBranchPlus/i18n.yml?branch=main&style=flat-square&label=i18n
[b-lint]: https://img.shields.io/github/actions/workflow/status/Ajimaru/OctoPrint-PandaBranchPlus/lint.yml?branch=main&style=flat-square&label=Lint
[b-bandit]: https://img.shields.io/github/actions/workflow/status/Ajimaru/OctoPrint-PandaBranchPlus/bandit-sarif.yml?branch=main&style=flat-square&label=Bandit%20SARIF

### 🧪 2. Code Quality & Formatting

[![Code style: black][b-black]](https://github.com/psf/black)
[![Imports: isort][b-isort]](https://pycqa.github.io/isort/)
[![Prettier][b-prettier]](https://github.com/prettier/prettier)
[![pre-commit][b-precommit]](https://pre-commit.com/)
[![Codacy][b-codacy]](https://app.codacy.com/gh/Ajimaru/OctoPrint-PandaBranchPlus/dashboard)
[![Coverage][b-coverage]](https://codecov.io/gh/Ajimaru/OctoPrint-PandaBranchPlus)
[![Pylint Score][b-pylint]](https://www.pylint.org/)
[![Bandit Security][b-sec]](https://bandit.readthedocs.io/en/latest/)
[![Depfu][b-depfu]](https://depfu.com/)
[![Known Vulnerabilities][b-snyk]](https://snyk.io/test/github/Ajimaru/OctoPrint-PandaBranchPlus)

[b-black]: https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square
[b-isort]: https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat-square&labelColor=ef8336
[b-prettier]: https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square
[b-precommit]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=flat-square&logo=pre-commit&logoColor=white
[b-codacy]: https://img.shields.io/badge/codacy-pending-lightgrey?style=flat-square
[b-coverage]: https://img.shields.io/codecov/c/github/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-pylint]: https://img.shields.io/badge/pylint-10.0-green.svg?style=flat-square
[b-sec]: https://img.shields.io/badge/bandit-security-green.svg?style=flat-square
[b-depfu]: https://img.shields.io/badge/depfu-monitored-blue?style=flat-square
[b-snyk]: https://snyk.io/test/github/Ajimaru/OctoPrint-PandaBranchPlus/badge.svg

### 🔄 3. CI/CD & Release

[![SemVer][b-semver]](https://semver.org/)
[![Release Date][b-reldate]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/releases)
[![Latest Release][b-latest]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/releases/latest)
[![Downloads][b-dl]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/releases)
[![Pre‑Release][b-pre]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/releases)
[![Python][b-py]](https://python.org)
[![OctoPrint][b-op]](https://octoprint.org)
[![Maintenance][b-maint]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/graphs/commit-activity)

[b-semver]: https://img.shields.io/badge/semver-2.0.0-blue?style=flat-square
[b-reldate]: https://img.shields.io/github/release-date/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-latest]: https://img.shields.io/github/v/release/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-dl]: https://img.shields.io/github/downloads/Ajimaru/OctoPrint-PandaBranchPlus/total.svg?style=flat-square
[b-pre]: https://img.shields.io/github/v/release/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square&include_prereleases&label=pre-release
[b-py]: https://img.shields.io/badge/python-3.9%2B-blue.svg?style=flat-square
[b-op]: https://img.shields.io/badge/OctoPrint-1.10.0%2B-blue.svg?style=flat-square
[b-maint]: https://img.shields.io/maintenance/yes/2026?style=flat-square

### 📊 4. Repository Activity

[![Open Issues][b-oi]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/issues?q=is%3Aissue%20state%3Aopen)
[![Closed Issues][b-ci2]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/issues?q=is%3Aissue%20state%3Aclosed)
[![Open PRs][b-opr]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/pulls?q=is%3Apr+is%3Aopen)
[![Closed PRs][b-cpr]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/pulls?q=is%3Apr+is%3Aclosed)
[![Last Commit][b-lc]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/commits/main)
[![Commit Activity][b-ca]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/graphs/commit-activity)
[![Contributors][b-con]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/graphs/contributors)

[b-oi]: https://img.shields.io/github/issues/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-ci2]: https://img.shields.io/github/issues-closed-raw/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-opr]: https://img.shields.io/github/issues-pr/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-cpr]: https://img.shields.io/github/issues-pr-closed/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-lc]: https://img.shields.io/github/last-commit/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-ca]: https://img.shields.io/github/commit-activity/y/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-con]: https://img.shields.io/github/contributors/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square

### 🧾 5. Metadata

![Code Size][b-size]
[![Security][b-secp]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/blob/main/SECURITY.md)
[![Snyk][b-snyks]](https://app.snyk.io)
![Languages Count][b-langc]
![Top Language][b-top]
[![License][b-lic]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/blob/main/LICENSE)
[![PRs Welcome][b-prs]](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/pulls)

[b-size]: https://img.shields.io/github/languages/code-size/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-secp]: https://img.shields.io/badge/security-policy-blue?style=flat-square
[b-snyks]: https://img.shields.io/badge/security-snyk-blueviolet?style=flat-square
[b-langc]: https://img.shields.io/github/languages/count/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-top]: https://img.shields.io/github/languages/top/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-lic]: https://img.shields.io/github/license/Ajimaru/OctoPrint-PandaBranchPlus?style=flat-square
[b-prs]: https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square

</details>
<!-- markdownlint-enable MD033 -->

---

![Stars][b-stars] ![Forks][b-forks] ![Watchers][b-watch]

[b-stars]: https://img.shields.io/github/stars/Ajimaru/OctoPrint-PandaBranchPlus?style=social
[b-forks]: https://img.shields.io/github/forks/Ajimaru/OctoPrint-PandaBranchPlus?style=social
[b-watch]: https://img.shields.io/github/watchers/Ajimaru/OctoPrint-PandaBranchPlus?style=social

**Like this plugin?** ⭐ Star the repo and share it with the OctoPrint community!
