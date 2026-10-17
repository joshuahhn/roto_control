"""Independent analysis MIX routing on the existing external MIDI connection."""
import copy
import math
import time
from binding import Binding, parameter_chain, parameter_value, same_parameter
from mix_descriptor import validate, projection, limits
from midi_queue import discard
from protocol import HEADER, sysex, text13, raw_value


def _identity(operator):
    return getattr(operator, 'id', operator.path)


class Target:
    def __init__(self, scope, description, identity):
        self.scope, self.description = scope, description
        self.operator = scope.op(description['target']['op'])
        if self.operator is None or not self.operator.valid:
            raise ValueError('Missing MIX target')
        self.parameter = self.operator.par[description['target']['parameter']]
        if self.parameter is None or self.parameter.style != 'Float' or description['kind'] != 'float':
            raise ValueError('This slice enables float input only; toggle/menu routing is unavailable')
        if not self.parameter.enable:
            raise ValueError('MIX parameter is disabled')
        self.chain = self.signature()
        minimum, maximum = limits(description.get('range', [self.parameter.normMin, self.parameter.normMax]))
        self.binding = Binding(identity, description['label'], minimum, maximum,
                               parameter_value(self.parameter), parameter=self.parameter)
        self.check()

    def signature(self):
        return tuple((_identity(p.owner), p.name, p.style, p.mode.name,
                      p.normMin, p.normMax, p.min, p.max, p.clampMin, p.clampMax)
                     for p in parameter_chain(self.parameter))

    def check(self):
        operator = self.scope.op(self.description['target']['op'])
        if (operator is None or not operator.valid or _identity(operator) != _identity(self.operator)
                or not same_parameter(operator.par[self.parameter.name], self.parameter)
                or not self.parameter.enable or self.signature() != self.chain):
            raise ValueError('MIX target identity, range or mode changed; reconfigure to resume')
        self.binding.check_parameter()
        return self.binding.clamp(parameter_value(self.parameter))


class Signal:
    def __init__(self, scope, description):
        self.scope, self.description = scope, description
        self.operator = scope.op(description['op'])
        if self.operator is None or not self.operator.valid:
            raise ValueError('Missing MIX signal')
        self.parameter = self.operator.par[description['parameter']] if description['kind'] == 'parameter' else None
        self.channels = tuple(self.operator[name] for name in description.get('channels', ()))
        if description['kind'] == 'chop' and any(c is None for c in self.channels):
            raise ValueError('Missing MIX channel')

    def sample(self, measure):
        current = self.scope.op(self.description['op'])
        if current is None or not current.valid or _identity(current) != _identity(self.operator):
            raise ValueError('MIX signal replaced/deleted')
        if self.description['kind'] == 'parameter':
            if not same_parameter(current.par[self.description['parameter']], self.parameter):
                raise ValueError('MIX signal parameter replaced')
            values = [float(self.parameter.eval())]
        else:
            # A channel layout change invalidates the old source, rather than
            # reusing the old index for a differently named channel.
            channels = [current[name] for name in self.description['channels']]
            if any(c is None for c in channels):
                raise ValueError('MIX signal channel removed')
            values = []
            for channel in channels:
                samples = [float(v) for v in channel.vals] if measure == 'rms_dbfs' else [float(channel[0])]
                if not samples or any(not math.isfinite(v) for v in samples):
                    raise ValueError('Invalid MIX signal sample')
                if measure == 'rms_dbfs':
                    rms = math.sqrt(sum(v * v for v in samples) / len(samples))
                    values.append(20 * math.log10(max(rms, 1e-12)))
                else:
                    values.append(samples[0])
        if any(not math.isfinite(v) for v in values):
            raise ValueError('Invalid MIX signal value')
        return (values * 2)[:2]


class MixRuntime:
    def __init__(self, extension):
        self.e = extension
        self.profile = None
        self.scope = self.source = None
        self.targets, self.errors, self.meters = {}, {}, {}
        self.active = self.returning = False
        self.epoch = 0
        self.view = None
        self.selected = 0
        self.select_pending = True
        self.family = 0
        self.ready = False
        self.touched, self.blocked, self.armed = set(), set(), set()
        self.parts, self.last_motor, self.last_text = {}, {}, {}
        self.dirty = True
        self.next_feedback = 0
        self.writes = 0
        self.error = ''
        saved = extension.ownerComp.fetch('mix_profile', None, search=False)
        if saved:
            try:
                self.configure(extension.ownerComp.op(saved['scope']), saved['descriptor'], save=False)
            except (ValueError, KeyError, TypeError) as exc:
                self.error = str(exc)

    def configure(self, scope, profile, *, save=True):
        if self.e._dispatching:
            raise ValueError('Do not configure MIX during parameter dispatch')
        if self.touched or self.e._host.touched or self.e._host.learning:
            raise ValueError('Exit LEARN and release knobs before MIX configuration')
        profile = validate(profile)
        if profile['style'] != 'analysis':
            raise ValueError('Only analysis is implemented; layers/audio remain planned')
        if any(item.get('trigger') for item in profile['items']):
            raise ValueError('Trigger feedback is not enabled in the Low/Mid slice')
        if scope is None or not scope.valid or not scope.isCOMP:
            raise ValueError('MIX needs an existing COMP scope')
        source = scope.op(profile['source'])
        if source is None or not source.valid:
            raise ValueError('MIX source is unavailable')
        targets, errors, meters = {}, {}, {}
        for index, item in enumerate(profile['items']):
            for key, control in item['controls'].items():
                try:
                    targets[index, key] = Target(scope, control, profile['id'] + ':' + item['id'] + ':' + key)
                except (ValueError, AttributeError, TypeError, KeyError) as exc:
                    errors[index, key] = str(exc)
            if item.get('meter'):
                try:
                    meters[index] = Signal(scope, item['meter']['source'])
                except (ValueError, AttributeError, TypeError, KeyError):
                    pass  # invalid feedback clears bars; other controls remain usable
        self.scope, self.source, self.profile = scope, source, profile
        self.targets, self.errors, self.meters = targets, errors, meters
        self.error = ''
        self.selected = 0
        self.select_pending = True
        self.invalidate()
        if save:
            self.e.ownerComp.store('mix_profile', dict(scope=self.e.ownerComp.relativePath(scope), descriptor=copy.deepcopy(profile)))

    def invalidate(self):
        self.epoch += 1
        self.ready = False
        self.blocked.update(self.touched)
        self.armed.clear(); self.parts.clear()
        self.last_motor.clear(); self.last_text.clear()
        self.dirty = True; self.next_feedback = 0
        if self.active:
            self.e._pending = discard(self.e._pending, self.feedback_output)

    @staticmethod
    def feedback_output(message):
        return ((len(message) == 3 and message[0] == 191)
                or len(message) >= 8 and tuple(message[:5]) == HEADER
                and (message[5] == 12 or message[5] == 10 and message[6] in (4, 5, 7, 8, 0x18)))

    def stop(self):
        self.active = self.returning = False
        self.view = None; self.family = 0; self.selected = 0
        self.select_pending = True
        self.invalidate()
        self.touched.clear(); self.blocked.clear()

    def receive(self, message, token=None, now=None):
        """Return True when MIX owns the event, including unsupported MIX input."""
        now = time.monotonic() if now is None else now
        message = tuple(message)
        valid = (len(message) >= 8 and message[:5] == HEADER and message[-1] == 247
                 and all(type(v) is int and 0 <= v < 128 for v in message[1:-1]))
        stale = token is not None and (len(token) < 3 or token[2] != self.epoch)
        if (not valid and self.active and len(message) >= 7 and message[:5] == HEADER
                and message[5] == 12 and message[6] in (1, 2, 5)):
            self.view = None; self.invalidate()
            return True
        if valid:
            group, command, data = message[5], message[6], message[7:-1]
            if (group, command) == (11, 1) and self.active:
                self.active = False; self.returning = True; self.view = None
                self.invalidate(); self.e._mix_mode_boundary()
                return False  # existing PLUGIN page/ACK/session path handles it
            if group == 12 and command in (1, 2, 5):
                if not self.e._host.connected:
                    return True
                entering = not self.active
                self.active = True; self.returning = False
                if entering:
                    self.select_pending = True
                    self.e._mix_mode_boundary()
                    # Reset the established PLUGIN parser, without admitting any
                    # MIX CC through it or pretending an assignment was learned.
                    self.e._host.receive(message, control_only=True)
                self.view = None
                if command == 1 and len(data) == 4 and data[0] in (0, 1) and data[1] in (0, 1, 2) and data[2] in (0, 1, 2):
                    self.family = data[0]; self.view = 'all', data
                elif command == 2 and len(data) == 1 and data[0] == 0 and self.family == 0:
                    self.view = 'focus', 0
                elif command == 5 and data == (0,):
                    self.family = 0  # await actual 01/02 view readback
                else:
                    self.family = 1 if command == 5 else self.family
                self.invalidate()
                if command == 5:
                    self.command(12, 9)  # request readback; never force 01/02
                return True
            if not self.active:
                return False
            if group == 10 and command in (6, 9):
                if not stale and len(data) != 2:
                    self.selected = -1; self.invalidate()
                if not stale and len(data) == 2:
                    index = data[0] * 128 + data[1]
                    if command == 9:
                        self.select(index)
                    elif index == 0:
                        self.dirty = True
                    else:
                        self.view = None; self.invalidate()
                return True
            if group == 12:
                if command == 7 and len(data) == 1:
                    self.send_names(data[0])
                    self.last_text.clear()
                return True
            # Only session handshake/PING reaches Host while MIX owns routing.
            return not (group == 10 and command in (2, 0x0C))
        if not self.active:
            return False
        if len(message) != 3 or message[0] != 191 or any(type(v) is not int or not 0 <= v < 128 for v in message[1:]):
            return True
        cc, value = message[1:]
        if 52 <= cc <= 59:
            lane = cc - 52
            if not value:
                self.touched.discard(lane); self.blocked.discard(lane)
                self.armed.discard(lane); self.parts.pop(lane, None)
            else:
                fresh = lane not in self.touched
                self.touched.add(lane)
                if fresh and self.ready and not stale and lane not in self.blocked:
                    if self.view and self.view[0] == 'all' and lane != self.selected:
                        if self.profile and lane < len(self.profile['items']):
                            self.select(lane, send=True)  # first touch selects, never writes
                    else:
                        self.armed.add(lane)
            return True
        if not self.ready or stale or self.e._dispatching or not self.source_valid():
            return True
        if 12 <= cc <= 19 or 44 <= cc <= 51:
            lane = cc - 12 if cc < 32 else cc - 44
            if lane not in self.armed or lane not in self.touched:
                return True
            address = self.addresses()[lane]
            target = self.targets.get(address)
            if target is None:
                return True
            parts = self.parts.setdefault(lane, {})
            parts[cc < 32] = value, now
            if True in parts and False in parts:
                msb, lsb = parts[True], parts[False]
                self.parts.pop(lane, None)
                if abs(msb[1] - lsb[1]) > .25:
                    return True
                try:
                    before = target.check()
                    raw = msb[0] * 128 + lsb[0]
                    self.e._dispatching = True
                    target.binding.write(target.binding.from_normalized(raw / 16383), 'hardware')
                    self.writes += int(before != target.binding.value)
                    self.last_motor[lane] = raw  # don't move against the gesture
                except Exception as exc:
                    self.suspend(address, exc)
                finally:
                    self.e._dispatching = False
        # Buttons, transport, unknown CCs never fall back to PLUGIN controls.
        return True

    def select(self, index, *, send=False):
        if not self.profile or not 0 <= index < len(self.profile['items']):
            self.selected = -1; self.invalidate()
        elif index != self.selected:
            self.selected = index
            self.select_pending |= send
            self.invalidate()

    def source_valid(self):
        if self.profile is None or self.scope is None or not self.scope.valid:
            return False
        current = self.scope.op(self.profile['source'])
        return current is not None and current.valid and _identity(current) == _identity(self.source)

    def addresses(self):
        return projection(self.profile, self.view, self.selected) if self.profile else [None] * 8

    def suspend(self, address, error):
        self.targets.pop(address, None)
        self.errors[address] = str(error)
        self.invalidate()

    def command(self, group, command, data=()):
        self.e._send(sysex(group, command, data), mix=True)

    def metadata(self):
        self.last_motor.clear(); self.last_text.clear()
        items = self.profile['items'] if self.profile else []
        self.command(12, 3, (2,))
        self.command(10, 4, (0, len(items))); self.command(10, 5, (0, 0))
        for index, item in enumerate(items):
            self.command(10, 7, (0, index, *text13(item['label']), 0, 0))
        self.command(10, 8)
        if self.select_pending and 0 <= self.selected < len(items):
            self.command(12, 4, (0, self.selected, *text13(items[self.selected]['label']), 0, 0))
        self.select_pending = False
        self.send_names()
        self.command(12, 11, (87, 113))  # global meter colors, not item thresholds
        enabled = [int(bool(self.view and self.family == 0 and i < len(items))) for i in range(8)]
        if self.view and self.view[0] == 'focus':
            enabled = [int(0 <= self.selected < len(items))] + [0] * 7
        self.command(12, 12, enabled)
        self.dirty = False

    def send_names(self, start=0):
        names = ('Add', 'Smooth')
        self.command(12, 8, (start, *(byte for index in range(start, start + 8)
                                    for byte in text13(names[index] if index < len(names) else ''))))

    def tick(self, *, backlog=False, now=None):
        if not self.active:
            if not backlog:
                self.returning = False
            return
        if backlog or not self.e._host.connected:
            return
        now = time.monotonic() if now is None else now
        if not self.source_valid():
            if self.ready:
                self.invalidate()
            self.error = 'MIX source unavailable; reconfigure to resume'
        if self.dirty:
            self.metadata()
        selected_valid = self.profile is not None and 0 <= self.selected < len(self.profile['items'])
        if self.view is not None and self.family == 0 and selected_valid and self.source_valid():
            self.ready = True
        if now < self.next_feedback:
            return
        self.next_feedback = now + .1  # no catch-up queue of obsolete samples
        addresses = self.addresses() if self.ready else [None] * 8
        for lane, address in enumerate(addresses):
            target = self.targets.get(address)
            text = 'Unavailable' if address else ''
            if target is not None:
                try:
                    value = target.check()
                    raw = raw_value(target.binding.normalized(value))
                    text = f'{target.binding.label} {value:.3f}'
                    if lane not in self.touched and self.last_motor.get(lane) != raw:
                        self.e._pending = discard(self.e._pending, lambda m: len(m) == 3 and m[0] == 191 and m[1] in (12 + lane, 44 + lane))
                        self.e._send((191, 12 + lane, raw >> 7), mix=True)
                        self.e._send((191, 44 + lane, raw & 127), mix=True)
                        self.last_motor[lane] = raw
                except (ValueError, AttributeError, TypeError) as exc:
                    self.suspend(address, exc)
                    return
            # API 2.23 returns to native names after a timeout. Renew assigned
            # text on the bounded feedback tick, even when its value is stable.
            if address is not None or self.last_text.get(lane) != text:
                self.e._pending = discard(self.e._pending, lambda m: len(m) >= 10 and tuple(m[:7]) == (*HEADER, 10, 0x18) and m[7:9] == [0, lane])
                self.command(10, 0x18, (0, lane, *text13(text)))
                self.last_text[lane] = text
        # Remove complete old meter frames, retaining an in-flight line tail.
        self.e._pending = discard(self.e._pending, lambda m: len(m) == 3 and m[0] == 191 and 65 <= m[1] <= 80)
        for lane in range(8):
            item_index = self.selected if self.view and self.view[0] == 'focus' and lane == 0 else lane if self.view and self.view[0] == 'all' else -1
            values = (0, 0)
            if self.ready and item_index in self.meters:
                try:
                    meter = self.profile['items'][item_index]['meter']
                    low, high = meter['range']
                    values = tuple(round(127 * min(1, max(0, (v - low) / (high - low)))) for v in self.meters[item_index].sample(meter['measure']))
                except (ValueError, AttributeError, TypeError):
                    pass
            for side, value in enumerate(values):
                self.e._send((191, 65 + 2 * lane + side, value), mix=True)

    def state(self):
        return dict(active=self.active, ready=self.ready, view=copy.deepcopy(self.view),
                    selected=self.selected, epoch=self.epoch, writes=self.writes,
                    error=self.error, controls=[dict(item=i, control=k, error=v) for (i, k), v in self.errors.items()])

    def refresh_scope(self):
        """Retain an explicitly configured scope through a live rename/save."""
        if self.source_valid():
            self.e.ownerComp.store('mix_profile', dict(scope=self.e.ownerComp.relativePath(self.scope),
                                                       descriptor=copy.deepcopy(self.profile)))
