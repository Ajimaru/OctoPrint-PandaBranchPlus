# Security

## Threat model in one paragraph

The plugin switches real power outputs over an **unauthenticated** device
protocol: the Panda Branch Plus firmware exposes `ws://<panda>/ws` without
any credentials — anyone who can reach the device on the LAN can switch
channels, plugin or not. That is a firmware property (report firmware issues
to BIQU); the plugin's job is to not make things worse.

## What the plugin does

- **No credentials stored.** The only connection setting is the Panda's
  host/IP — there is nothing to leak.
- **Permission-gated API.** The SimpleAPI is protected
  (`is_api_protected()`); reads need `STATUS`, writes need `CONTROL`.
- **Server-side validation.** Channel ids are checked against the fixed
  hardware layout; rule/failsafe/sensor values are whitelisted; labels are
  length-capped. Invalid input aborts with HTTP 400.
- **Autoescaped templates.** `is_template_autoescaped()` is enabled; the
  templates render only translated strings and Knockout bindings.
- **High-power confirmation.** Manual switch-ON of 24V channels prompts by
  default.

## Deployment recommendations

- Keep the Panda on a **trusted LAN segment** (or its own VLAN/IoT network).
  Do not port-forward the Panda's web interface.
- Treat channel switching like any physical power switch: if untrusted users
  can reach your OctoPrint, scope their accounts (no `CONTROL` permission —
  they can then see states but not switch).

## Reporting

See [SECURITY.md](https://github.com/Ajimaru/OctoPrint-PandaBranchPlus/blob/main/SECURITY.md)
for the disclosure process.
