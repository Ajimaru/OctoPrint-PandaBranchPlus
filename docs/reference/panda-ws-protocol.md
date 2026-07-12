# Panda WS protocol

The reverse engineered control protocol of the Panda Branch Plus firmware,
verified against real hardware. The device is an ESP32-S3 hub with 10
switchable outputs (5× Type-C under the `usb` root, 5× MX3.0 24V under
`mx24v`).

## Endpoint

```text
ws://<panda-ip>/ws        (port 80, no authentication)
```

**Multi-client (verified):** `/ws` accepts multiple concurrent connections
and broadcasts every state change to all of them. Only the device's MQTT
side (port 8883, printer gateway) is single-client.

## Snapshot on connect

Immediately after the handshake the firmware pushes a full state snapshot.
The channel lists are nested under `control`:

```json
{
  "control": {
    "usb": [
      { "id": 1, "on": 1 },
      { "id": 2, "on": 0 }
    ],
    "mx24v": [{ "id": 1, "on": 0 }]
  }
}
```

Later pushes have been observed both nested and with `usb`/`mx24v` at the
top level — parsers should accept either.

## Switching a channel

Send a single JSON object:

```json
{ "usb": { "id": 3, "on": 1 } }
{ "mx24v": { "id": 1, "on": 0 } }
```

The firmware confirms by broadcasting the resulting state to **all**
connected clients — treat the broadcast as the acknowledgement; there is no
per-command reply.

## Keepalive behavior

The firmware **does not answer WebSocket protocol pings** — a client using
`ping_interval`/`ping_timeout` will kill its own healthy connection. The
device's own web UI uses no pings either. Use TCP keepalive for dead-peer
detection instead.

## Hardware ratings

| Channel     | Rating                                           |
| ----------- | ------------------------------------------------ |
| `usb` 1     | Type-C 5 V / 5 A (intended for a Panda Hub Plus) |
| `usb` 2–5   | Type-C 5 V / 1.5 A                               |
| `mx24v` 1–5 | MX3.0 24 V / 2 A                                 |

Input: 24 V / 2.8 A. Source:
[manufacturer wiki](https://global.bttwiki.com/Panda_Branch_Plus.html).

## No sensors

The WS state exposes only channel states — no temperatures or power
readings. A `panda` temperature source was considered for the rule engine
and dropped for that reason.
