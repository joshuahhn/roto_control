"""One-parameter host; wire formats follow the official Ableton ROTO script.

Reference: joshuahhn/roto_control commit 2d43a72c6699983080f8765292498502ff08be57.
No Live, TouchDesigner, or legacy nin-lab host dependency.
"""

import hashlib
import math


HEADER = (0xF0, 0, 0x22, 3, 2)
GENERAL, PLUGIN = 0x0A, 0x0B


def sysex(group, command, data=()):
    payload = (group, command, *data)
    if any(type(x) is not int or not 0 <= x < 128 for x in payload):
        raise ValueError("SysEx payload must contain seven-bit integers")
    return (*HEADER, *payload, 0xF7)


def digest(text, length):
    return tuple(x & 127 for x in hashlib.sha1(text.encode("utf-8")).digest()[:length])


def text13(text):
    return tuple(text.encode("ascii", "replace")[:12].ljust(13, b"\0"))


def display_name(value):
    """Validate a hardware name without truncation or replacement."""
    if not isinstance(value, str):
        raise ValueError("Hardware name must be a string")
    try:
        data = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("Hardware name must use ASCII") from exc
    if len(data) > 12 or any(x < 32 or x > 126 for x in data):
        raise ValueError("Hardware name must contain at most 12 printable ASCII bytes")
    return value


def format_number(value):
    """Compact LCD text; preserve numeric precision outside the display."""
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def raw_value(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Value must be finite")
    return round(min(1.0, max(0.0, value)) * 16383)


class Host:
    """Small interface: start, receive, offer_parameter, parameter_changed, stop.

    send accepts a complete MIDI message. assign accepts a normalized Value.
    Runtime flags reset on each session; no controller mappings are inferred.
    """

    def __init__(self, send, assign, value=0.5, *, track_name="EFFECT", plugin_name="CUSTOM"):
        self.track_name = display_name(track_name)
        self.plugin_name = display_name(plugin_name)
        self.send = send
        self.assign = assign
        self.value = float(value)
        self.enabled = True
        self.target_id = "Value"
        self.target_label = "Value"
        self.device_id = "TD Python Value Prototype"
        self.format_value = format_number
        self.connected = False
        self.plugin = False
        self.learning = False
        self.mapped = False
        self.touched = False
        self.rx = self.tx = self.rejected = self.echo_blocked = 0
        self._offered_in_learn = False
        self._parts = {}
        self._input_value = None
        self._deferred_value = False
        self._display_dirty = False
        self._display_deadline = 0.0
        self.last_event = "Disconnected"

    def configure_target(self, identity, label, value, format_value, *, default=False):
        if self.learning or self.touched:
            raise ValueError("Cannot replace target while learning or touched")
        self.enabled = True
        self.target_id = "Value" if default else identity
        self.target_label = label
        self.device_id = "TD Python Value Prototype" if default else "TD binding:" + identity
        self.format_value = format_value
        self.value = raw_value(value) / 16383
        self.mapped = False
        self._parts.clear()
        self._input_value = None
        self._deferred_value = self._display_dirty = False
        self._offered_in_learn = False
        if self.connected and self.plugin:
            self._devices()
        self.last_event = "Target ready; await mapping or LEARN"

    def _send(self, message):
        if self.send(tuple(message)) is False:
            return False
        self.tx += 1
        return True

    def _command(self, group, command, data=()):
        self._send(sysex(group, command, data))

    def clear_learn(self):
        if not self.connected or not self.plugin:
            raise ValueError("Connect to PLUGIN before clearing LEARN")
        if self.learning or self.touched:
            raise ValueError("Exit LEARN and release the control before clearing")
        self._command(PLUGIN, 14, (0, 0))
        self._clear_mapping_state()
        self.last_event = "Knob 1 unmap requested"
        return True

    def _clear_mapping_state(self):
        self.mapped = False
        self._parts.clear()
        self._input_value = None
        self._deferred_value = self._display_dirty = False
        self._offered_in_learn = False

    def start(self):
        self.stop()
        self.last_event = "Waiting for controller"
        self._command(GENERAL, 1)  # DAW_STARTED

    def stop(self):
        self.connected = self.plugin = self.learning = self.mapped = False
        self.touched = False
        self._offered_in_learn = False
        self._parts.clear()
        self._input_value = None
        self._deferred_value = False
        self._display_dirty = False
        self._display_deadline = 0.0
        self.last_event = "Disconnected"

    def set_display_names(self, track_name, plugin_name):
        track_name, plugin_name = display_name(track_name), display_name(plugin_name)
        if (track_name, plugin_name) == (self.track_name, self.plugin_name):
            return False
        if self.learning:
            raise ValueError("Exit hardware LEARN before changing display names")
        self.track_name, self.plugin_name = track_name, plugin_name
        if self.connected:
            self._command(GENERAL, 0x16, text13(self.track_name))
            if self.plugin:
                self._device_details()
                self._command(PLUGIN, 6)
        return True

    def _device_details(self):
        self._command(PLUGIN, 5, (getattr(self, "plugin_index", 0), *digest(self.device_id, 8),
                                 1, *text13(self.plugin_name), 0, 0))

    def _devices(self):
        callback = getattr(self, "devices_callback", None)
        if callback is not None:
            callback()
            return
        self._command(PLUGIN, 2, (1,))  # NUM_DEVICES
        self._command(PLUGIN, 3, (0,))  # FIRST_DEVICE
        self._device_details()
        self._command(PLUGIN, 6)  # PLUGIN_DETAILS_END
        self._command(PLUGIN, 8, (0, 0, 0))  # select device, no forced macro pages

    def _tracks(self):
        callback = getattr(self, "tracks_callback", None)
        if callback is not None:
            callback()
            return
        # PLUGIN selection still belongs to a track, even in this one-target host.
        detail = (0, 0, *text13(self.track_name), 0, 0)
        self._command(GENERAL, 4, (0, 1))
        self._command(GENERAL, 5, (0, 0))
        self._command(GENERAL, 7, detail)
        self._command(GENERAL, 8)
        self._command(0x0C, 4, detail)

    def offer_parameter(self):
        if not (self.enabled and self.connected and self.plugin and self.learning):
            self.last_event = "Enable hardware LEARN first"
            return False
        self._parameter_details()
        self._offered_in_learn = True
        self.last_event = f"{self.target_label} offered; assign hardware Knob 1"
        return True

    def _parameter_details(self):
        value = raw_value(self.value)
        self._command(PLUGIN, 0x0A, (0, 0, *digest(self.target_id, 6),
                                    0, 0, 0, value >> 7, value & 127,
                                    *text13(self.target_label)))

    def _display(self):
        self._command(GENERAL, 0x18, (0, 0, *text13(self.format_value(self.value))))
        self._display_dirty = False

    def flush_display(self, now):
        if (self.enabled and self.connected and self.plugin and self.mapped and self._display_dirty
                and now >= self._display_deadline):
            self._display()
            self._display_deadline = now + 1 / 12

    def _feedback(self):
        value = raw_value(self.value)
        self._send((0xBF, 12, value >> 7))
        self._send((0xBF, 44, value & 127))
        self._display()

    def parameter_changed(self, value):
        if not self.enabled:
            return
        self.value = raw_value(value) / 16383
        if self._input_value == raw_value(value):
            self._input_value = None
            self.echo_blocked += 1
            self._display_dirty = True
            return
        self._input_value = None
        if self.learning and not self._offered_in_learn:
            self.offer_parameter()
        if self.enabled and self.connected and self.plugin and self.mapped:
            if self.touched:
                self._deferred_value = True
            else:
                self._feedback()

    def receive(self, message, control_only=False):
        message = tuple(message)
        if not message or any(type(x) is not int or not 0 <= x <= 255 for x in message):
            self.rejected += 1
            return
        self.rx += 1
        if message[0] == 0xF0:
            if (len(message) < 8 or message[:5] != HEADER or message[-1] != 0xF7
                    or any(x > 127 for x in message[1:-1])):
                self.rejected += 1
                return
            group, command, data = message[5], message[6], message[7:-1]
            if control_only and group == PLUGIN and command in (0x0B, 0x0E):
                return
            if group == GENERAL and command == 2:
                # Ableton-compatible host identity, not a registered TD DAW ID.
                self._command(GENERAL, 3, (1,))
            elif group == GENERAL and command == 0x0C:
                self.connected = True
                self._tracks()
                self.last_event = "Controller handshake complete"
            elif group == PLUGIN and command == 1 and self.connected:
                self.plugin = True
                self.mapped = self.learning = False
                self._offered_in_learn = False
                self._parts.clear()
                self._devices()
                self.last_event = "PLUGIN ready; use LEARN"
            elif group == PLUGIN and command in (4, 7) and self.plugin:
                if data and data[0] == 0:
                    self._devices()
            elif group == PLUGIN and command == 9 and self.plugin:
                if len(data) != 1 or data[0] not in (0, 1):
                    self.rejected += 1
                    return
                if bool(data[0]) != self.learning:
                    self._offered_in_learn = False
                self.learning = bool(data[0])
                self.last_event = "LEARN on" if self.learning else "LEARN off"
            elif group == PLUGIN and command == 0x0B and self.plugin and self.enabled:
                if (len(data) != 11 or data[:2] != (0, 0)
                        or data[2:8] != digest(self.target_id, 6)
                        or data[8:] != (0, 0, 0)):
                    self.rejected += 1
                    self.last_event = "Mapping does not match active target / Knob 1"
                    return
                self.mapped = True
                self._parts.clear()
                self.last_event = f"{self.target_label} mapped to Knob 1"
                self._parameter_details()
                self._feedback()
            elif group == PLUGIN and command == 0x0E:
                self.mapped = False
                self._parts.clear()
            elif group == 0x0C:  # MIX is outside this prototype
                self.plugin = self.mapped = self.learning = False
                self._parts.clear()
            return
        if len(message) != 3 or message[0] != 0xBF or any(x > 127 for x in message[1:]):
            return
        cc, value = message[1:]
        if control_only:
            if cc == 52:
                self.touched = value > 0
            return
        if cc == 52:
            self.touched = value > 0
            if self.touched and self.enabled and self.connected and self.plugin and self.mapped:
                self._display()
            if not self.touched and self._deferred_value and self.mapped:
                self._deferred_value = False
                self._feedback()
        elif self.enabled and self.connected and self.plugin and self.mapped and cc in (12, 44):
            self._parts[cc] = value
            if 12 in self._parts and 44 in self._parts:
                raw = (self._parts[12] << 7) | self._parts[44]
                self._parts.clear()
                self._input_value = raw
                # A later physical gesture supersedes any deferred TD edit.
                self._deferred_value = False
                self.value = raw / 16383
                self.assign(self.value)
