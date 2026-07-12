/*
 * View model for OctoPrint-PandaBranchPlus
 *
 * Author: Ajimaru
 * License: AGPL-3.0-or-later
 */
$(function () {
    function PandaBranchPlusViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];
        self.settingsViewModel = parameters[1];

        // Live connection state to the Panda (pushed via plugin messages).
        self.connected = ko.observable(false);

        // Channel cards. Seeded from settings on binding; live on/off state is
        // updated from Panda state pushes.
        self.channels = ko.observableArray([]);

        // "Test connection" button state in the settings dialog.
        self.testing = ko.observable(false);
        self.testResult = ko.observable("");
        self.testResultCss = ko.observable("");

        self._pluginSettings = function () {
            return self.settingsViewModel.settings.plugins.pandabranchplus;
        };

        // Build one channel card model from its stored settings entry.
        self._buildChannel = function (c) {
            var kind = ko.utils.unwrapObservable(c.kind);
            var id = ko.utils.unwrapObservable(c.id);
            var storedRules = c.rules || {};
            var storedTemp = c.temp_rule || {};

            var channel = {
                kind: kind,
                id: id,
                idLabel: (kind === "usb" ? "USB " : "MX ") + id,
                // The fixed hardware type arrives with the initial API get
                // (single source: hardware.py on the server).
                type: ko.observable(ko.utils.unwrapObservable(c.type) || ""),
                label: ko.observable(ko.utils.unwrapObservable(c.label)),
                on: ko.observable(false),
                mode: ko.observable(
                    ko.utils.unwrapObservable(c.mode) || "auto",
                ),
                failsafe: ko.observable(
                    ko.utils.unwrapObservable(c.failsafe) || "off",
                ),
                rules: {
                    idle: ko.observable(
                        ko.utils.unwrapObservable(storedRules.idle) || "off",
                    ),
                    prepare: ko.observable(
                        ko.utils.unwrapObservable(storedRules.prepare) || "off",
                    ),
                    printing: ko.observable(
                        ko.utils.unwrapObservable(storedRules.printing) ||
                            "off",
                    ),
                    paused: ko.observable(
                        ko.utils.unwrapObservable(storedRules.paused) || "off",
                    ),
                    error: ko.observable(
                        ko.utils.unwrapObservable(storedRules.error) || "off",
                    ),
                },
                tempRule: {
                    enabled: ko.observable(
                        !!ko.utils.unwrapObservable(storedTemp.enabled),
                    ),
                    sensor: ko.observable(
                        ko.utils.unwrapObservable(storedTemp.sensor) || "bed",
                    ),
                    threshold: ko.observable(
                        ko.utils.unwrapObservable(storedTemp.threshold) || 40,
                    ),
                    above: ko.observable(
                        ko.utils.unwrapObservable(storedTemp.above) || "on",
                    ),
                },
            };

            // Persist renames right away (fires on blur).
            channel.label.subscribe(function (value) {
                OctoPrint.simpleApiCommand("pandabranchplus", "set_label", {
                    kind: channel.kind,
                    id: channel.id,
                    label: value,
                }).done(function (data) {
                    if (c.label && ko.isObservable(c.label)) {
                        c.label(data.label);
                    }
                });
            });

            // Persist any automation config change right away.
            var sendConfig = function () {
                OctoPrint.simpleApiCommand(
                    "pandabranchplus",
                    "set_channel_config",
                    {
                        kind: channel.kind,
                        id: channel.id,
                        rules: {
                            idle: channel.rules.idle(),
                            prepare: channel.rules.prepare(),
                            printing: channel.rules.printing(),
                            paused: channel.rules.paused(),
                            error: channel.rules.error(),
                        },
                        temp_rule: {
                            enabled: channel.tempRule.enabled(),
                            sensor: channel.tempRule.sensor(),
                            threshold:
                                parseFloat(channel.tempRule.threshold()) || 40,
                            above: channel.tempRule.above(),
                        },
                        failsafe: channel.failsafe(),
                    },
                );
            };
            ["idle", "prepare", "printing", "paused", "error"].forEach(
                function (state) {
                    channel.rules[state].subscribe(sendConfig);
                },
            );
            ["enabled", "sensor", "threshold", "above"].forEach(function (key) {
                channel.tempRule[key].subscribe(sendConfig);
            });
            channel.failsafe.subscribe(sendConfig);

            return channel;
        };

        self.onBeforeBinding = function () {
            // The settings template binds against `settings.plugins...`.
            self.settings = self.settingsViewModel.settings;
            var cfg = self._pluginSettings().channels
                ? self._pluginSettings().channels()
                : [];
            self.channels(cfg.map(self._buildChannel));
        };

        // Pull the current connection + channel state once the UI is up, so a
        // freshly opened browser shows reality without waiting for a push.
        self.onStartupComplete = function () {
            OctoPrint.simpleApiGet("pandabranchplus").done(function (data) {
                self.connected(!!data.connected);
                self._applyChannels(data.channels || {});
                (data.layout || []).forEach(function (entry) {
                    self.channels().forEach(function (channel) {
                        if (
                            channel.kind === entry.kind &&
                            channel.id === entry.id
                        ) {
                            channel.type(entry.type);
                        }
                    });
                });
            });
        };

        self._applyChannels = function (channels) {
            self.channels().forEach(function (channel) {
                var states = channels[channel.kind];
                if (states && states[channel.id] !== undefined) {
                    channel.on(!!states[channel.id]);
                }
            });
        };

        // Auto <-> manual. Manual immediately enforces the remembered
        // manual_on state server-side; auto re-applies the matrix.
        self.setMode = function (channel, mode) {
            if (channel.mode() === mode) {
                return;
            }
            channel.mode(mode);
            OctoPrint.simpleApiCommand("pandabranchplus", "set_mode", {
                kind: channel.kind,
                id: channel.id,
                mode: mode,
            });
        };

        // Manual toggle of a channel from the tab. 24V channels ask for
        // confirmation first when the safety setting is on.
        self.toggleChannel = function (channel) {
            var doSwitch = function () {
                OctoPrint.simpleApiCommand("pandabranchplus", "set_channel", {
                    kind: channel.kind,
                    id: channel.id,
                    on: !channel.on(),
                }).done(function (data) {
                    if (!data.ok) {
                        new PNotify({
                            title: gettext("Switching failed"),
                            text: data.detail || data.reason,
                            type: "error",
                            hide: true,
                        });
                    }
                    // The confirmed state arrives via the Panda's broadcast.
                });
            };

            var confirmHighPower = self._pluginSettings().confirm_high_power();
            if (channel.kind === "mx24v" && !channel.on() && confirmHighPower) {
                showConfirmationDialog({
                    title: gettext("Switch on 24V channel?"),
                    message: _.sprintf(
                        gettext(
                            'This switches on "%(label)s" (%(type)s). Make sure the connected device is safe to power.',
                        ),
                        { label: channel.label(), type: channel.type() },
                    ),
                    proceed: gettext("Switch on"),
                    onproceed: doSwitch,
                });
            } else {
                doSwitch();
            }
        };

        // Connection test button in settings. Tests the values currently in
        // the dialog (even unsaved ones), result shown inline next to the
        // button.
        self.testConnection = function () {
            var s = self._pluginSettings();
            self.testing(true);
            self.testResult("");
            self.testResultCss("");
            OctoPrint.simpleApiCommand("pandabranchplus", "test_connection", {
                host: s.host(),
                port: s.ws_port(),
                path: s.ws_path(),
            })
                .done(function (data) {
                    if (data.ok) {
                        self.testResult(
                            _.sprintf(
                                gettext("Panda found — %(count)d channels."),
                                { count: data.channels },
                            ),
                        );
                        self.testResultCss("text-success");
                    } else {
                        var reasons = {
                            no_host: gettext("Please enter a host / IP first."),
                            timeout: gettext("Timeout — host did not answer."),
                            unreachable: gettext(
                                "Panda not reachable at this address.",
                            ),
                        };
                        self.testResult(
                            reasons[data.reason] || data.detail || data.reason,
                        );
                        self.testResultCss("text-error");
                    }
                })
                .fail(function () {
                    self.testResult(
                        gettext("Test failed — see the OctoPrint log."),
                    );
                    self.testResultCss("text-error");
                })
                .always(function () {
                    self.testing(false);
                });
        };

        // Live updates pushed from the plugin (channel state, connection).
        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "pandabranchplus") {
                return;
            }
            if (data.type === "connection") {
                self.connected(!!data.connected);
            } else if (data.type === "state") {
                self.connected(true);
                self._applyChannels(data.channels || {});
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: PandaBranchPlusViewModel,
        dependencies: ["loginStateViewModel", "settingsViewModel"],
        elements: [
            "#tab_plugin_pandabranchplus",
            "#settings_plugin_pandabranchplus",
        ],
    });
});
