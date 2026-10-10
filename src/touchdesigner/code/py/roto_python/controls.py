"""Control collection adapters. TD handles are supplied by the caller."""
import copy
import json

from binding import Binding, parameter_chain, parameter_value
from protocol import format_number


class Actions:
    """Runtime-only consumer entry points; IDs are the persistence boundary."""
    def __init__(self):
        self.entries = {}
        self.results = {}
        self.error = ''

    def register(self, id, label, recall, *, replace=False):
        if not isinstance(id, str) or not id.strip() or not isinstance(label, str) or not label.strip():
            raise ValueError('Action needs a stable ID and label')
        if not callable(recall):
            raise TypeError('Action recall must be callable')
        if id in self.entries and not replace:
            raise ValueError('Action ID already registered: ' + id)
        self.entries[id] = (label, recall)
        self.results.pop(id, None)
        return self.state(id)

    def state(self, id):
        entry = self.entries.get(id)
        result = self.results.get(id)
        error = (result['status'] + ': ' + result['error']) if result and result['status'] != 'succeeded' else ''
        return dict(id=id, label=entry[0] if entry else id, available=entry is not None,
                    error=error if entry else self.error or 'Action unavailable: ' + id,
                    result=copy.deepcopy(result))

    def recall(self, id, event):
        entry = self.entries.get(id)
        result = dict(action_id=id, status='unavailable', error=self.error or 'Action unavailable: ' + id)
        if entry is not None:
            try:
                value = entry[1](dict(event, action_id=id))
                if value is None:
                    result = dict(action_id=id, status='succeeded', error='')
                elif (isinstance(value, dict) and value.get('status') in
                      ('succeeded', 'success', 'unavailable', 'failed', 'partial', 'validation_failed', 'execution_failed') and
                      isinstance(value.get('error', ''), str)):
                    # Preserve provider details, but never leak callables/TD
                    # handles into detached diagnostics or saved catalogs.
                    result = json.loads(json.dumps(value, allow_nan=False))
                    result.update(action_id=id, status='succeeded' if value['status']=='success' else value['status'],
                                  error=value.get('error', ''))
                    if result['status'] != 'succeeded' and not result['error']:
                        result['error'] = 'Action ' + result['status'] + ': ' + id
                else:
                    raise ValueError('Action must return None or a status/error result')
            except Exception as exc:
                result = dict(action_id=id, status='failed', error=str(exc) or type(exc).__name__)
        self.results[id] = result
        return copy.deepcopy(result)


class Controls:
    def __init__(self, specs, *, allow_empty=False):
        self.bindings, self.modes, self.ids, self.paths, self.errors = {}, {}, {}, {}, {}
        self.button_types, self.indices = {}, {}
        parameters, wire_indices = set(), set()
        for spec in specs:
            kind, slot = spec['kind'], spec['slot']
            key = kind, slot
            mode = spec.get('mode', 'value' if kind == 'knob' else 'cycle' if getattr(spec.get('parameter'), 'style', '') == 'Menu' else 'toggle')
            if kind not in ('knob', 'button') or type(slot) is not int or not 1 <= slot <= 8:
                raise ValueError('Control must be knob/button, slot 1..8')
            if (kind == 'knob' and mode != 'value') or (kind == 'button' and mode not in ('toggle', 'pulse', 'cycle')):
                raise ValueError('Knob uses value; button uses toggle/pulse')
            button_type = spec.get('button_type', 'toggle' if kind == 'button' else None)
            if kind == 'button' and button_type not in ('toggle', 'push') or kind == 'knob' and button_type is not None:
                raise ValueError('button_type is toggle/push for buttons only')
            action_id = spec.get('action_id')
            if action_id is not None and (not isinstance(action_id, str) or not action_id.strip() or
                                          kind != 'button' or mode != 'pulse' or spec.get('parameter') is not None):
                raise ValueError('Action presets require a Button in Pulse mode')
            parameter = spec.get('parameter')
            if parameter is not None:
                styles = ('Float', 'Int', 'Menu') if kind == 'knob' else (('Toggle',) if mode == 'toggle' else ('Menu',) if mode == 'cycle' else ('Pulse',))
                if not parameter.isCustom or parameter.style not in styles:
                    raise ValueError('Custom parameter style does not match control mode')
                keys={(p.owner.path,p.name) for p in parameter_chain(parameter)}
                if keys & parameters:
                    raise ValueError('A parameter or bind master cannot be bound twice')
                parameters.update(keys)
            elif not callable(spec.get('on_change')):
                raise ValueError('Supply a parameter or on_change callback')
            menu = parameter is not None and parameter.style == 'Menu'
            minimum = spec.get('minimum', 0 if menu else parameter.normMin if parameter is not None and kind == 'knob' else 0)
            maximum = spec.get('maximum', len(parameter.menuNames)-1 if menu else parameter.normMax if parameter is not None and kind == 'knob' else 1)
            if kind == 'button' and mode != 'cycle' and (minimum != 0 or maximum != 1):
                raise ValueError('Button range must be 0..1')
            if parameter is not None and not menu and kind == 'knob' and (
                    parameter.clampMin and minimum < parameter.min or
                    parameter.clampMax and maximum > parameter.max):
                raise ValueError('Binding range exceeds target clamp limits')
            value = 0 if mode == 'pulse' else spec.get('value', parameter_value(parameter) if parameter is not None else 0)
            binding = Binding(spec['id'], spec.get('label') or (parameter.label if parameter is not None else spec['id']),
                              minimum, maximum, value, integer=kind == 'button' or parameter is not None and parameter.style == 'Int',
                              parameter=parameter, on_change=spec.get('on_change'))
            binding.action_id = action_id
            binding.check_parameter()
            if key in self.bindings or binding.id in self.ids:
                raise ValueError('Control slots and target IDs must be unique')
            self.bindings[key], self.modes[key], self.ids[binding.id] = binding, mode, key
            self.button_types[key] = button_type
            index = spec.get('index',slot-1+(8 if kind=='button' else 0))
            if type(index) is not int or not 0 <= index < 16384 or index in wire_indices:
                raise ValueError('Parameter indices must be unique integers in 0..16383')
            wire_indices.add(index)
            self.indices[key] = index
            self.paths[key] = parameter.owner.path if parameter is not None else ''
        if not self.bindings and not allow_empty:
            raise ValueError('Register at least one control')

    def specs(self):
        for key, binding in self.bindings.items():
            mode = self.modes[key]
            yield dict(kind=key[0], slot=key[1], index=self.indices[key], identity=binding.wire_identity + (':action:' + repr(binding.action_id) if binding.action_id else '') + ':' + mode,
                       label=binding.label, mode=mode, button_type=self.button_types[key], value=binding.normalized(binding.value),
                       formatter=binding.format_value if mode in ('value','cycle') else lambda value, b=binding, m=mode: ('Ready' if m == 'pulse' else
                                 ('On' if value >= .5 else 'Off') if m == 'toggle' else b.format_value(value)))

    def key(self, id=None):
        if id is None:
            if ('knob', 1) not in self.bindings:
                raise ValueError('Specify a target ID; Knob 1 is not configured')
            return 'knob', 1
        if id not in self.ids:
            raise ValueError('Unknown target ID: ' + str(id))
        return self.ids[id]

    def pulse(self, key):
        binding = self.bindings[key]
        if not binding.valid:
            raise ValueError('Binding suspended')
        binding.check_parameter()
        if binding.parameter is not None:
            # TD coalesces onPulse callbacks within one frame; acknowledge
            # that callback once rather than leaving an accumulated counter.
            binding.pulse_expected = 1
            binding.parameter.pulse()
        else:
            binding.on_change(dict(id=binding.id, value=1, origin='hardware', kind='pulse'))

    def suspend(self, key, exc):
        self.bindings[key].valid = False
        self.errors[key] = str(exc)


def from_table(controller):
    table = controller.op('base_targets/targets')
    columns = [cell.val for cell in table.row(0)]
    specs = []
    for row in table.rows()[1:]:
        data = dict(zip(columns, (cell.val for cell in row)))
        target = controller.op(data['comp'])
        parameter = getattr(target.par, data['parameter'], None) if target is not None else None
        if parameter is None:
            raise ValueError('Target parameter missing: ' + data['comp'] + '.' + data['parameter'])
        spec = dict(kind=data['kind'], slot=int(data['slot']), id=data['id'],
                    parameter=parameter, mode=data['mode'], label=data['label'])
        if data.get('button_type', '').strip():
            spec['button_type'] = data['button_type'].strip()
        for field in ('minimum', 'maximum'):
            if data[field].strip():
                spec[field] = float(data[field])
        specs.append(spec)
    return specs
