"""Pure rule engine for the channel automation.

Kept free of OctoPrint imports so the decision logic is unit-testable in
isolation. The plugin resolves the current printer state and temperatures,
then asks :func:`resolve_target` what each channel should do.

Semantics (see .ideas/channel-automation-plan.md):

- ``mode: "manual"`` always wins: the channel follows ``manual_on``,
  automation never touches it.
- ``mode: "auto"``: the state matrix ``rules[state]`` decides — ``"on"``,
  ``"off"`` or ``"ignore"`` (= leave the channel exactly as it is).
- An enabled ``temp_rule`` fires when the sensor crosses ``threshold`` (with
  hysteresis on the falling edge) and contributes ``above`` ("on"/"off")
  while active; while inactive it has no opinion.
- ``combine_logic`` merges the two verdicts:
  - ``temp_override``: an active temp rule replaces the state verdict.
  - ``and``: on only if both say on, otherwise off.
  - ``or``: on if either says on, otherwise off.
"""


def evaluate_temp_rule(rule, temps, was_active, hysteresis):
    """Evaluate a channel's temperature rule.

    Parameters
    ----------
    rule:
        The channel's ``temp_rule`` dict (``enabled``, ``sensor``,
        ``threshold``, ``above``).
    temps:
        Last known temperatures, e.g. ``{"bed": 62.1, "tool": 210.4}``.
        Missing sensors simply keep the previous verdict (no flapping on
        gaps in the data).
    was_active:
        Whether the rule was active after the previous evaluation (needed
        for the hysteresis dead band).
    hysteresis:
        Dead band in degrees applied on the falling edge.

    Returns ``(active, target)`` where ``target`` is ``rule["above"]`` while
    active and ``None`` (no opinion) while inactive.
    """
    if not rule or not rule.get("enabled"):
        return False, None

    action = rule.get("above") or "on"
    temp = temps.get(rule.get("sensor") or "bed")
    if temp is None:
        # No reading for this sensor -> keep the previous verdict.
        return was_active, (action if was_active else None)

    threshold = float(rule.get("threshold") or 0)
    if was_active:
        active = temp > threshold - float(hysteresis)
    else:
        active = temp >= threshold
    return active, (action if active else None)


def resolve_target(
    channel, state, temps, was_active, combine_logic="temp_override", hysteresis=2
):
    """Resolve what a channel should do right now.

    Parameters
    ----------
    channel:
        The channel's stored config (``mode``, ``manual_on``, ``rules``,
        ``temp_rule``).
    state:
        Canonical printer state: ``idle``/``prepare``/``printing``/
        ``paused``/``error``.
    temps / was_active / hysteresis:
        See :func:`evaluate_temp_rule`.
    combine_logic:
        ``temp_override`` | ``and`` | ``or``.

    Returns ``(target, temp_active)`` where ``target`` is ``"on"``, ``"off"``
    or ``None`` (= leave the channel untouched).
    """
    if channel.get("mode") == "manual":
        return ("on" if channel.get("manual_on") else "off"), was_active

    state_rule = (channel.get("rules") or {}).get(state, "off")
    state_target = None if state_rule == "ignore" else state_rule

    temp_active, temp_target = evaluate_temp_rule(
        channel.get("temp_rule") or {}, temps, was_active, hysteresis
    )

    if temp_target is None:
        return state_target, temp_active

    if combine_logic == "and":
        target = "on" if (state_target == "on" and temp_target == "on") else "off"
    elif combine_logic == "or":
        target = "on" if (state_target == "on" or temp_target == "on") else "off"
    else:  # temp_override (default)
        target = temp_target
    return target, temp_active


def map_octoprint_state(state_id):
    """Map an OctoPrint state id to the plugin's five canonical states.

    ``STARTING`` is what BambuConnector reports for Bambu's PREPARE phase.
    Anything unknown (offline, detecting, ...) counts as ``idle`` — no
    printer means no print is running (see the plan's state resolution).
    """
    mapping = {
        "STARTING": "prepare",
        "PRINTING": "printing",
        "RESUMING": "printing",
        "FINISHING": "printing",
        "PAUSED": "paused",
        "PAUSING": "paused",
        "ERROR": "error",
        "CLOSED_WITH_ERROR": "error",
    }
    return mapping.get(state_id, "idle")
