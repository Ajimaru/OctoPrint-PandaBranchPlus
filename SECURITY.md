# Security Policy

## Supported versions

Security fixes are provided for the latest released version. Please make sure
you are running the most recent release before reporting an issue.

## Security model

How PandaBranchPlus handles connections and privileged actions:

- **Panda WebSocket.** The plugin controls the Panda Branch Plus over its
  local WebSocket interface (`ws://<panda-host>/ws`). The device firmware
  itself exposes this interface **without authentication** — anyone on the
  LAN who can reach the Panda's IP can switch its channels, with or without
  this plugin. Keep the Panda on a trusted network segment.
- **No credentials.** The plugin stores only the Panda's host/IP. It never
  handles printer access codes; the printer state is read from OctoPrint's
  own state machine (fed by a connector plugin such as
  OctoPrint-BambuConnector).
- **Privileged actions.** Switching channels and changing channel
  configuration via the plugin's API is permission-gated through OctoPrint's
  access control; unauthenticated browser sessions cannot toggle power
  channels through the plugin.
- **Fail-safe.** If the WebSocket connection to the Panda is lost, each
  channel falls back to its configured fail-safe state (default: off) so a
  dead link never leaves heaters or pumps in an undefined state.
- **Logging.** Diagnostic frame logging is off by default and never includes
  credentials (the protocol contains none).

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities by email to **ajimaru_gdr [at] pm [dot] me**. Include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce or a proof-of-concept (if safe to share).
- Any suggested mitigations you are aware of.

You will receive an acknowledgement of your report, followed by a status update
once it has been reviewed. If the issue is confirmed, a patch and coordinated
disclosure will follow as quickly as possible.

## Scope

Issues in scope for this project:

- Authentication or authorization bypasses in the plugin's API endpoints.
- Arbitrary file read/write via plugin settings or API.
- Unsafe shell command execution triggered by user-controlled input.
- Channel state manipulation by users without the required OctoPrint
  permission.
- Denial of service caused by the plugin's connection management logic.

Out of scope:

- Vulnerabilities in OctoPrint itself — please report those to the
  [OctoPrint project](https://github.com/OctoPrint/OctoPrint/security).
- Vulnerabilities in the Panda Branch Plus firmware (including its
  unauthenticated WebSocket and web interface) — please report those to
  [BIQU / BigTreeTech](https://github.com/bigtreetech). The plugin cannot add
  authentication the device does not have.
- Issues that require physical access to the OctoPrint host.
