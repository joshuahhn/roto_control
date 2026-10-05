"""One PLUGIN device with independently acknowledged knobs/buttons."""
import time
from protocol import Host, GENERAL, PLUGIN, digest, raw_value, text13


class Control(Host):
    def __init__(self, send, key, index, identity, label, value, formatter, mode, button_type=None):
        super().__init__(send, lambda value: None, value)
        self.key, self.index, self.mode = key, index, mode
        self.target_id, self.target_label, self.format_value = identity, label, formatter
        self.button_type = button_type
        self.last_pulse = float('-inf')
        self._pulse_state = 0

    def offer_parameter(self):
        result = super().offer_parameter()
        if result:
            self.last_event = f"{self.target_label} offered; select {self.key[0]} {self.key[1]}"
        return result

    def _parameter_details(self):
        value = raw_value(self.value)
        steps = 2 if self.key[0] == 'button' else 0
        labels = ('Ready', 'Trigger') if self.mode == 'pulse' else ('Off', 'On')
        strings = (*text13(labels[0]), *text13(labels[1])) if steps else ()
        self._command(PLUGIN, 10, (self.index >> 7, self.index & 127,
                                   *digest(self.target_id, 6), 0, 0, steps,
                                   value >> 7, value & 127, *text13(self.target_label), *strings))

    def _display(self):
        kind, slot = self.key
        if self.mode == "pulse":
            label = "Trigger" if self._pulse_state >= 64 else "Ready"
        else:
            label = self.format_value(self.value)
        self._command(GENERAL, 24, (int(kind == 'button'), slot-1,
                                    *text13(label)))
        self._display_dirty = False

    def stop(self):
        super().stop()
        self._pulse_state = 0

    def _feedback(self):
        kind, slot = self.key
        if kind == 'knob':
            value = raw_value(self.value)
            self._send((191, 11+slot, value >> 7))
            self._send((191, 43+slot, value & 127))
        else:
            value = self._pulse_state if self.mode == 'pulse' else 127 if self.value >= 0.5 else 0
            self._send((191, 19+slot, value))
        self._display()


class CollectionHost(Host):
    def __init__(self, send, assign, specs, group_id, clock=time.monotonic, *, allow_empty=False):
        super().__init__(send, lambda value: None, 0)
        if not isinstance(group_id, str) or not group_id.strip():
            raise ValueError('A stable group ID is required')
        self.device_id = 'TD controls:' + group_id
        self.assign_control, self.clock = assign, clock
        self.controls = {}
        self.pending_unmaps=set()
        indices, hashes = set(), set()
        for spec in specs:
            kind, slot = spec['kind'], spec['slot']
            if kind not in ('knob','button') or type(slot) is not int or not 1 <= slot <= 8:
                raise ValueError('Control must be knob/button, slot 1..8')
            key = kind, slot
            index = spec.get('index',slot-1 + (8 if kind == 'button' else 0))
            if type(index) is not int or not 0 <= index < 16384:
                raise ValueError('Parameter index must be 0..16383')
            identity = spec['identity']
            hashed = digest(identity,6)
            if index in indices or hashed in hashes:
                raise ValueError('Control slots and wire identities must be unique')
            indices.add(index)
            hashes.add(hashed)
            mode = spec.get('mode','value')
            if (kind == 'knob' and mode != 'value') or (kind == 'button' and mode not in ('toggle','pulse')):
                raise ValueError('Knob uses value; button uses toggle/pulse')
            button_type = spec.get('button_type', 'toggle' if kind == 'button' else None)
            if kind == 'button' and button_type not in ('toggle', 'push') or kind == 'knob' and button_type is not None:
                raise ValueError('button_type is toggle/push for buttons only')
            self.controls[key] = Control(self._send, key, index, identity, spec['label'],
                                          spec['value'], spec['formatter'], mode, button_type)
        if not self.controls and not allow_empty:
            raise ValueError('Register at least one control')

    def _sync(self):
        self.mapped = bool(self.controls) and all(t.mapped and t.enabled for t in self.controls.values())
        self.touched = any(t.touched for t in self.controls.values())
        self.echo_blocked = sum(t.echo_blocked for t in self.controls.values())
        self.value = self.controls[('knob',1)].value if ('knob',1) in self.controls else 0
        for target in self.controls.values():
            target.connected, target.plugin = self.connected, self.plugin
            if target.learning != self.learning:
                target._offered_in_learn = False
            target.learning = self.learning

    def stop(self):
        super().stop()
        for target in self.controls.values():
            target.stop()
            target.last_pulse = float('-inf')
            target._pulse_state = 0

    def offer_parameter(self, key=None):
        key = key or ('knob',1)
        if key not in self.controls:
            raise ValueError('No target at this control')
        self._sync()
        result = self.controls[key].offer_parameter() if self.enabled else False
        self.last_event = self.controls[key].last_event
        return result

    def clear_learn(self, key):
        if key not in self.controls:
            raise ValueError('No target at this control')
        target = self.controls[key]
        if not self.connected or not self.plugin:
            raise ValueError('Connect to PLUGIN before clearing LEARN')
        if self.learning or target.touched:
            raise ValueError('Exit LEARN and release the control before clearing')
        self._command(PLUGIN, 14, (int(key[0]=='button'), key[1]-1))
        target._clear_mapping_state()
        target._pulse_state = 0
        target.last_pulse = float('-inf')
        self.last_event = f'{key[0].capitalize()} {key[1]} unmap requested'
        self._sync()
        return True

    def parameter_changed(self, value, key=None):
        key = key or ('knob',1)
        if key not in self.controls:
            raise ValueError('No target at this control')
        if not self.enabled:
            return
        self._sync()
        self.controls[key].parameter_changed(value)
        self.last_event = self.controls[key].last_event
        self._sync()

    def flush_display(self, now):
        self._sync()
        if self.enabled:
            for target in self.controls.values():
                target.flush_display(now)

    def receive(self, message):
        message = tuple(message)
        # Let the proven parser validate and count the message first. Handle
        # mapped/unmap commands here because single-target routing differs.
        is_sysex = (len(message)>=8 and message[:5] == (240,0,34,3,2)
                    and message[-1] == 247 and all(type(x) is int and 0<=x<128 for x in message[1:-1]))
        if is_sysex and message[5:7] in ((11,11),(11,14)):
            self.rx += 1
            data = message[7:-1]
            if not self.enabled or not self.plugin:
                return
            if message[6] == 14:
                if len(data) != 2 or data[0] not in (0,1) or not 0<=data[1]<8:
                    self.rejected += 1
                    return
                key = ('button' if data[0] else 'knob', data[1]+1)
                if key in self.controls:
                    self.controls[key].mapped = False
                    self.controls[key]._parts.clear()
                self._sync()
                return
            if len(data)!=11 or data[8] not in (0,1) or not 0<=data[9]<8 or data[10]!=0:
                self.rejected += 1
                return
            key = ('button' if data[8] else 'knob', data[9]+1)
            target = self.controls.get(key)
            index = (data[0]<<7)|data[1]
            if (target is None or not target.enabled or index != target.index
                    or data[2:8] != digest(target.target_id,6)):
                self.rejected += 1
                self.last_event = 'Mapping does not match configured control/target'
                return
            target.mapped = True
            target._parts.clear()
            target.last_pulse = float('-inf')
            target._pulse_state = 0
            target.last_event = "Mapped; target ready"
            target._parameter_details()
            target._feedback()
            self.last_event = f'{target.target_label} mapped to {key[0]} {key[1]}'
            self._sync()
            return
        if is_sysex:
            reset = message[5:7] == (11,1) or message[5] == 12
            # Avoid single-target handling of CCs and mappings; session control
            # still uses Host's handshake, track and device announcements.
            super().receive(message)
            if reset:
                for target in self.controls.values():
                    target.stop()
            self._sync()
            if message[5:7]==(PLUGIN,1) and self.connected and self.plugin:
                for kind,slot in sorted(self.pending_unmaps):
                    if (kind,slot) not in self.controls:
                        self._command(PLUGIN,14,(int(kind=='button'),slot-1))
            return
        # Validate/count non-SysEx separately so Host cannot route Knob 1.
        if not message or any(type(x) is not int or not 0<=x<=255 for x in message):
            self.rejected += 1
            return
        self.rx += 1
        if message[0] == 240:
            self.rejected += 1
            return
        if len(message)!=3 or message[0]!=191 or any(x>127 for x in message[1:]):
            return
        self._sync()
        cc, value = message[1:]
        if 52<=cc<=59 and self.enabled:
            slot = cc-51
            target = self.controls.get(('knob',slot))
            if target is not None:
                target.touched = value>0
                if target.enabled and target.mapped and self.plugin and self.connected:
                    if target.touched:
                        target._display()
                    elif target._deferred_value:
                        target._deferred_value = False
                        target._feedback()
            button = self.controls.get(('button',slot))
            if value and button is not None and button.mapped and button.enabled:
                button._display()
            self._sync()
            return
        if not (self.enabled and self.connected and self.plugin) or self.learning:
            return
        if 12<=cc<=19 or 44<=cc<=51:
            slot = cc-11 if cc<32 else cc-43
            key = ('knob',slot)
            target = self.controls.get(key)
            if target is None or not target.mapped or not target.enabled:
                return
            target._parts[cc] = value
            msb, lsb = 11+slot, 43+slot
            if msb in target._parts and lsb in target._parts:
                raw = (target._parts[msb]<<7)|target._parts[lsb]
                target._parts.clear()
                target._input_value = raw
                target._deferred_value = False
                target.value = raw/16383
                self.assign_control(key,target.value)
        elif 20<=cc<=27:
            key = ('button',cc-19)
            target = self.controls.get(key)
            if target is None or not target.mapped or not target.enabled:
                return
            # Action mode belongs to the consumer; button_type declares RX semantics.
            if target.mode == 'pulse':
                now = self.clock()
                pressed = value >= 64
                if target.button_type == 'push':
                    if pressed == (target._pulse_state >= 64):
                        return  # duplicate held/released state, not another action
                    fire = pressed
                else:
                    if now-target.last_pulse < .04:
                        return
                    fire = True  # every latched TOGGLE press, including zero
                if fire:
                    target.last_pulse = now
                    self.assign_control(key,1)
                    target.value = 0
                if target.enabled and target.mapped:
                    # TOGGLE is an action source: confirm idle immediately.
                    # PUSH retains its RX state to distinguish press/release.
                    target._pulse_state = value if target.button_type == 'push' else 0
                    target._feedback()
            else:
                target.value = float(value>=64)
                target._input_value = raw_value(target.value)
                self.assign_control(key,target.value)
                # Buttons require host state confirmation after the adapter write.
                # Knob motor echo suppression must not suppress the button LED.
                if target.enabled and target.mapped:
                    target._feedback()
        self._sync()
