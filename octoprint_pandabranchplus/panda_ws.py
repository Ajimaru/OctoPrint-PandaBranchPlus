"""WebSocket client to the Panda Branch Plus.

The Panda serves a JSON control WebSocket at ``ws://<host>/ws``. Channels are
switched with ``{"usb"|"mx24v": {"id": N, "on": 0|1}}``; on connect it pushes a
full state snapshot including ``control.usb`` / ``control.mx24v`` (the live
on/off state of every channel), and it broadcasts every channel change to all
connected clients (verified — the Panda's /ws accepts multiple concurrent
clients; only its MQTT side is single-client).

Structure mirrors the proven ``BambuMqttMonitor`` pattern from
OctoPrint-BambuCam (one long-lived socket, reconnect with backoff, on_change
callback). Full protocol in ``.ideas/panda-branch-plus-recon.md``.
"""

import json
import socket
import threading
from contextlib import suppress

import websocket


class PandaWsError(Exception):
    """A Panda WebSocket operation failed, carrying a classified ``reason``.

    ``reason`` is one of ``unreachable`` / ``timeout`` / ``send_failed`` so the
    UI can translate it without parsing raw socket errors.
    """

    def __init__(self, reason, message=""):
        super().__init__(message or reason)
        self.reason = reason


def _parse_channel_state(data):
    """Extract ``{"usb": {id: 0|1}, "mx24v": {id: 0|1}}`` from a Panda frame.

    The snapshot nests the channel lists under ``control``; later pushes have
    been observed both nested and at the top level, so accept either. Returns
    ``None`` when the frame carries no channel information at all.
    """
    control = data.get("control", data)
    if not isinstance(control, dict):
        return None
    result = {}
    for kind in ("usb", "mx24v"):
        entries = control.get(kind)
        if not isinstance(entries, list):
            continue
        states = {}
        for entry in entries:
            if isinstance(entry, dict) and "id" in entry:
                states[int(entry["id"])] = 1 if entry.get("on") else 0
        if states:
            result[kind] = states
    return result or None


def test_connection(host, port=80, path="/ws", timeout=5):
    """One-shot connect: open the socket, read the snapshot, close.

    Returns ``{"channels": {...}, "raw_keys": [...]}`` on success. Raises
    :class:`PandaWsError` with a classified reason on failure. Used by the
    settings dialog's "Test connection" button — runs against the entered
    values, independent of the long-lived client.
    """
    url = f"ws://{host}:{int(port)}{path}"
    try:
        ws = websocket.create_connection(url, timeout=timeout)
    except (websocket.WebSocketTimeoutException, socket.timeout) as exc:
        raise PandaWsError("timeout", str(exc)) from exc
    except (OSError, websocket.WebSocketException) as exc:
        raise PandaWsError("unreachable", str(exc)) from exc

    try:
        try:
            frame = ws.recv()
        except (websocket.WebSocketTimeoutException, socket.timeout) as exc:
            raise PandaWsError("timeout", f"connected, but no snapshot: {exc}") from exc
        except (OSError, websocket.WebSocketException) as exc:
            raise PandaWsError("unreachable", str(exc)) from exc
        try:
            data = json.loads(frame)
        except ValueError as exc:
            raise PandaWsError(
                "unreachable", "connected, but got a non-JSON frame"
            ) from exc
        channels = _parse_channel_state(data)
        if channels is None:
            raise PandaWsError(
                "unreachable",
                "connected, but the snapshot has no usb/mx24v channels"
                " — is this really a Panda Branch Plus?",
            )
        return {"channels": channels, "raw_keys": sorted(data.keys())}
    finally:
        with suppress(Exception):
            ws.close()


class PandaWsClient:
    """Long-lived WebSocket client for the Panda's channel control.

    Parameters
    ----------
    logger:
        A logger instance.
    host, port, path:
        Panda address and WebSocket endpoint (default port 80, path ``/ws``).
    on_state:
        Callback ``on_state(channels: dict)`` invoked with the parsed channel
        state of every push (``{"usb": {id: 0|1}, "mx24v": {id: 0|1}}``).
    on_connection:
        Callback ``on_connection(connected: bool)`` invoked on every
        connect/disconnect of the socket.
    reconnect_min, reconnect_max:
        Backoff window (seconds) between reconnect attempts; the delay doubles
        from min up to max after each failed attempt and resets on success.
    frame_log:
        When true, log every raw frame at DEBUG level (diagnostics).
    """

    def __init__(
        self,
        logger,
        host,
        port=80,
        path="/ws",
        on_state=None,
        on_connection=None,
        reconnect_min=1,
        reconnect_max=30,
        frame_log=False,
    ):
        self._logger = logger
        self._host = host
        self._port = int(port)
        self._path = path
        self._on_state = on_state
        self._on_connection = on_connection
        self._reconnect_min = max(1, int(reconnect_min))
        self._reconnect_max = max(self._reconnect_min, int(reconnect_max))
        self._frame_log = frame_log

        self._ws = None
        self._thread = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._connected = False
        self._delay = self._reconnect_min  # current reconnect backoff
        self._state = {"usb": {}, "mx24v": {}}  # last known channel states

    @property
    def url(self):
        return f"ws://{self._host}:{self._port}{self._path}"

    @property
    def connected(self):
        return self._connected

    def current_state(self):
        """Return the last known channel state snapshot."""
        with self._lock:
            return {kind: dict(states) for kind, states in self._state.items()}

    # lifecycle

    def start(self):
        """Open the connection and start the background receive/reconnect loop."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_loop, name="PandaWsClient", daemon=True
            )
            self._thread.start()

    def stop(self):
        """Close the connection and stop the loop. Idempotent."""
        self._stop_event.set()
        ws = self._ws
        if ws is not None:
            with suppress(Exception):
                ws.close()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=5)
        self._thread = None

    # commands

    def set_channel(self, kind, channel_id, on):
        """Switch a channel on/off.

        Sends ``{"<kind>": {"id": id, "on": 0|1}}``. ``kind`` is ``"usb"`` or
        ``"mx24v"``. Raises :class:`PandaWsError` on send failure. The Panda
        confirms by broadcasting the new state, which arrives via ``on_state``.
        """
        if kind not in ("usb", "mx24v"):
            raise ValueError(f"unknown channel kind: {kind!r}")
        payload = json.dumps({kind: {"id": int(channel_id), "on": 1 if on else 0}})
        ws = self._ws
        if ws is None or not self._connected:
            raise PandaWsError("send_failed", "not connected to the Panda")
        try:
            ws.send(payload)
        except Exception as exc:
            raise PandaWsError("send_failed", str(exc)) from exc

    # internals

    @staticmethod
    def _keepalive_sockopts():
        """TCP keepalive options for dead-peer detection without WS pings.

        On Linux this probes an idle connection after 30s, then every 10s,
        and declares it dead after 3 missed probes (~60s total). The
        per-option constants are platform-dependent, so each is guarded.
        """
        opts = [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)]
        for name, value in (
            ("TCP_KEEPIDLE", 30),
            ("TCP_KEEPINTVL", 10),
            ("TCP_KEEPCNT", 3),
        ):
            if hasattr(socket, name):
                opts.append((socket.IPPROTO_TCP, getattr(socket, name), value))
        # run_forever's signature types sockopt as a tuple.
        return tuple(opts)

    def _run_loop(self):
        """Reconnect loop: run one WebSocketApp until it dies, back off, retry."""
        self._delay = self._reconnect_min
        while not self._stop_event.is_set():
            app = websocket.WebSocketApp(
                self.url,
                on_open=self._handle_open,
                on_message=self._handle_message,
                on_close=self._handle_close,
                on_error=self._handle_error,
            )
            self._ws = app
            try:
                # No WebSocket protocol pings: the Panda firmware never
                # answers them (verified — its own web UI doesn't use pings
                # either), so any ping_interval kills a healthy connection
                # after ping_timeout. Dead connections are detected via TCP
                # keepalive instead (~60s on Linux with the options below).
                app.run_forever(sockopt=self._keepalive_sockopts())
            except Exception as exc:
                self._logger.debug("Panda WS run_forever raised: %s", exc)
            finally:
                self._ws = None
                self._set_connected(False)
            if self._stop_event.is_set():
                break
            self._logger.info(
                "Panda WS disconnected, reconnecting to %s in %ds",
                self.url,
                self._delay,
            )
            if self._stop_event.wait(self._delay):
                break
            self._delay = min(self._delay * 2, self._reconnect_max)

    def _set_connected(self, connected):
        if connected == self._connected:
            return
        self._connected = connected
        if self._on_connection is not None:
            try:
                self._on_connection(connected)
            except Exception:
                self._logger.exception("on_connection callback failed")

    def _handle_open(self, _ws):
        self._logger.info("Panda WS connected: %s", self.url)
        self._delay = self._reconnect_min  # successful session resets the backoff
        self._set_connected(True)

    def _handle_message(self, _ws, message):
        if self._frame_log:
            self._logger.debug("Panda WS frame: %s", message)
        try:
            data = json.loads(message)
        except ValueError:
            self._logger.debug("Panda WS: ignoring non-JSON frame")
            return
        channels = _parse_channel_state(data)
        if channels is None:
            return
        with self._lock:
            for kind, states in channels.items():
                self._state.setdefault(kind, {}).update(states)
            snapshot = {k: dict(v) for k, v in self._state.items()}
        if self._on_state is not None:
            try:
                self._on_state(snapshot)
            except Exception:
                self._logger.exception("on_state callback failed")

    def _handle_close(self, _ws, code, reason):
        self._logger.debug("Panda WS closed (code=%s reason=%s)", code, reason)
        self._set_connected(False)

    def _handle_error(self, _ws, error):
        self._logger.debug("Panda WS error: %s", error)
