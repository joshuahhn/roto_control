"""Control collection adapters. TD handles are supplied by the caller."""
from binding import Binding, parameter_chain
from protocol import format_number


class Controls:
    def __init__(self, specs, *, allow_empty=False):
        self.bindings, self.modes, self.ids, self.paths, self.errors = {}, {}, {}, {}, {}
        self.button_types, self.indices = {}, {}
        parameters = set()
        for spec in specs:
            kind, slot = spec['kind'], spec['slot']
            key = kind, slot
            mode = spec.get('mode', 'value' if kind == 'knob' else 'toggle')
            if kind not in ('knob', 'button') or type(slot) is not int or not 1 <= slot <= 8:
                raise ValueError('Control must be knob/button, slot 1..8')
            if (kind == 'knob' and mode != 'value') or (kind == 'button' and mode not in ('toggle', 'pulse')):
                raise ValueError('Knob uses value; button uses toggle/pulse')
            button_type = spec.get('button_type', 'toggle' if kind == 'button' else None)
            if kind == 'button' and button_type not in ('toggle', 'push') or kind == 'knob' and button_type is not None:
                raise ValueError('button_type is toggle/push for buttons only')
            parameter = spec.get('parameter')
            if parameter is not None:
                styles = ('Float', 'Int') if kind == 'knob' else (('Toggle',) if mode == 'toggle' else ('Pulse',))
                if not parameter.isCustom or parameter.style not in styles:
                    raise ValueError('Custom parameter style does not match control mode')
                keys={(p.owner.path,p.name) for p in parameter_chain(parameter)}
                if keys & parameters:
                    raise ValueError('A parameter or bind master cannot be bound twice')
                parameters.update(keys)
            elif not callable(spec.get('on_change')):
                raise ValueError('Supply a parameter or on_change callback')
            minimum = spec.get('minimum', parameter.normMin if parameter is not None and kind == 'knob' else 0)
            maximum = spec.get('maximum', parameter.normMax if parameter is not None and kind == 'knob' else 1)
            if kind == 'button' and (minimum != 0 or maximum != 1):
                raise ValueError('Button range must be 0..1')
            if parameter is not None and kind == 'knob' and (
                    parameter.clampMin and minimum < parameter.min or
                    parameter.clampMax and maximum > parameter.max):
                raise ValueError('Binding range exceeds target clamp limits')
            value = 0 if mode == 'pulse' else spec.get('value', parameter.eval() if parameter is not None else 0)
            binding = Binding(spec['id'], spec.get('label') or (parameter.label if parameter is not None else spec['id']),
                              minimum, maximum, value, integer=kind == 'button' or parameter is not None and parameter.style == 'Int',
                              parameter=parameter, on_change=spec.get('on_change'))
            binding.check_parameter()
            if key in self.bindings or binding.id in self.ids:
                raise ValueError('Control slots and target IDs must be unique')
            self.bindings[key], self.modes[key], self.ids[binding.id] = binding, mode, key
            self.button_types[key] = button_type
            self.indices[key] = spec.get('index',slot-1+(8 if kind=='button' else 0))
            self.paths[key] = parameter.owner.path if parameter is not None else ''
        if not self.bindings and not allow_empty:
            raise ValueError('Register at least one control')

    def specs(self):
        for key, binding in self.bindings.items():
            mode = self.modes[key]
            yield dict(kind=key[0], slot=key[1], index=self.indices[key], identity=binding.wire_identity + ':' + mode,
                       label=binding.label, mode=mode, button_type=self.button_types[key], value=binding.normalized(binding.value),
                       formatter=lambda value, b=binding, m=mode: ('Ready' if m == 'pulse' else
                                 ('On' if value >= .5 else 'Off') if m == 'toggle' else format_number(b.from_normalized(value))))

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
