"""Saved MIX descriptions and the existing audioAnalysis band adapter.

Only data lives here. Loading or describing a source never writes a TD parameter.
"""
import math
from pathlib import PurePosixPath


CONTROL_KEYS = {
    'layers': ('opacity', 'brightness', 'black_level', 'gamma', 'operation', 'swap'),
    'analysis': ('threshold', 'gain', 'add', 'smooth', 'active'),
    'audio': ('gain', 'mute'),
}
FLOAT_KEYS = {
    'analysis': ('threshold', 'gain', 'add', 'smooth'),
    'layers': ('opacity', 'brightness', 'black_level', 'gamma'),
}
DETAIL_KEYS = dict(FLOAT_KEYS, layers=FLOAT_KEYS['layers'] + ('operation', 'swap'))
ANALYSIS_BANDS = ('Low', 'Mid', 'High', 'Kick', 'Snare', 'Rhythm')
ANALYSIS_DETECTORS = {
    'Kick': ('Kick', 'math2', 'low', 'kick', 1),
    'Snare': ('Snare', 'math16', 'high', 'snare', 1),
    'Rhythm': ('Rythm', 'math10', 'chan0', 'rythm', 100),
}


def reference(value):
    if (not isinstance(value, str) or not value or '\\' in value
            or value.startswith('/') or '..' in PurePosixPath(value).parts):
        raise ValueError('MIX references must stay within the explicit scope')
    return value


def limits(value):
    if (not isinstance(value, (list, tuple)) or len(value) != 2
            or any(type(x) not in (int, float) or not math.isfinite(x) for x in value)
            or value[0] >= value[1] or not math.isfinite(value[1] - value[0])):
        raise ValueError('MIX range needs two finite increasing numbers')
    return tuple(value)


def operation_choices(value, maximum=24):
    """Ordered existing-menu names. Empty omits Operation; one choice is invalid."""
    if (not isinstance(value, (list, tuple)) or len(value) > maximum
            or any(not isinstance(name, str) or not name for name in value)):
        raise ValueError('Operation choices need at most ' + str(maximum) + ' nonempty names')
    result = list(dict.fromkeys(value))
    if len(result) == 1:
        raise ValueError('Choose at least two different Operation modes, or leave all slots None')
    return result


def operation_presets(value):
    """Validate saved named choice lists independently of an applied MIX profile."""
    if value is None:
        return dict(version=1, records=[])
    _fields(value, ('version', 'records'))
    if type(value['version']) is not int or value['version'] != 1 or not isinstance(value['records'], list):
        raise ValueError('Unsupported Operation preset storage')
    ids, names = set(), set()
    records = []
    for record in value['records']:
        _fields(record, ('id', 'name', 'operations'))
        _name(record['id']); _name(record['name'])
        name = record['name'].strip()
        choices = operation_choices(record['operations'], 6)
        if (not choices or record['id'] in ids or name.casefold() in names):
            raise ValueError('Operation presets need unique ids/names and at least two modes')
        ids.add(record['id']); names.add(name.casefold())
        records.append(dict(id=record['id'], name=name, operations=choices))
    return dict(version=1, records=records)


def _name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('MIX id/label/parameter must be nonempty text')


def _fields(value, required, optional=()):
    if not isinstance(value, dict) or set(required) - set(value) or set(value) - set(required) - set(optional):
        raise ValueError('Unknown or missing MIX descriptor fields')


def _target(value):
    _fields(value, ('op', 'parameter'))
    reference(value['op'])
    _name(value['parameter'])


def _signal(value):
    _fields(value, ('kind', 'op'), ('parameter', 'channels'))
    reference(value['op'])
    if value['kind'] == 'parameter':
        _name(value['parameter'])
    elif value['kind'] == 'chop':
        channels = value['channels']
        if not isinstance(channels, list) or not 1 <= len(channels) <= 2:
            raise ValueError('MIX signal needs one or two named channels')
        for name in channels:
            _name(name)
    else:
        raise ValueError('Unsupported MIX signal kind')


def validate(profile):
    """Validate versioned JSON data; return an isolated persistence snapshot."""
    try:
        _fields(profile, ('version', 'style', 'id', 'source', 'items'))
        if type(profile['version']) is not int or profile['version'] != 1:
            raise ValueError('Unsupported MIX descriptor version')
        style = profile['style']
        if style not in CONTROL_KEYS:
            raise ValueError('MIX style must be layers, analysis or audio')
        _name(profile['id'])
        reference(profile['source'])
        items = profile['items']
        if not isinstance(items, list) or len(items) > 8:
            raise ValueError('This MIX page has at most eight items')
        ids = set()
        for item in items:
            _fields(item, ('id', 'label', 'primary', 'controls'), ('meter', 'trigger', 'input'))
            if style == 'layers':
                reference(item['input'])
            elif 'input' in item:
                raise ValueError('Only Layer Mix items have an input reference')
            _name(item['id']); _name(item['label'])
            if item['id'] in ids:
                raise ValueError('Duplicate MIX item id')
            ids.add(item['id'])
            controls = item['controls']
            if not isinstance(controls, dict) or set(controls) - set(CONTROL_KEYS[style]):
                raise ValueError('Unknown control for this MIX style')
            if item['primary'] is not None and item['primary'] not in controls:
                raise ValueError('MIX primary must reference an available control')
            for control in controls.values():
                _fields(control, ('label', 'kind', 'target'), ('range', 'choices'))
                _name(control['label'])
                if control['kind'] not in ('float', 'menu', 'toggle'):
                    raise ValueError('Unsupported MIX control kind')
                _target(control['target'])
                if control['kind'] == 'menu':
                    choices = control.get('choices')
                    if (not isinstance(choices, list) or not 2 <= len(choices) <= 24
                            or any(not isinstance(name, str) or not name for name in choices)
                            or len(set(choices)) != len(choices)):
                        raise ValueError('MIX Menu needs 2..24 unique choice names')
                elif 'choices' in control:
                    raise ValueError('Only MIX Menu controls have choices')
                if 'range' in control:
                    limits(control['range'])
            meter = item.get('meter')
            if meter:
                _fields(meter, ('source', 'measure', 'range', 'stage'), ('overview_reference', 'focus_reference'))
                _signal(meter['source']); limits(meter['range']); _name(meter['stage'])
                if meter['measure'] not in ('scalar', 'rms_dbfs'):
                    raise ValueError('Unsupported MIX measurement')
                if meter['measure'] == 'rms_dbfs' and meter['source']['kind'] != 'chop':
                    raise ValueError('RMS needs CHOP samples')
                for reference_key in ('overview_reference', 'focus_reference'):
                    if reference_key not in meter:
                        continue
                    if (style != 'analysis' or meter[reference_key] != 'threshold'
                            or controls.get('threshold', {}).get('kind') != 'float'
                            or meter['measure'] != 'scalar'
                            or meter['source']['kind'] == 'chop' and len(meter['source']['channels']) != 1):
                        raise ValueError('Meter reference needs an analysis mono scalar level and Float threshold')
            trigger = item.get('trigger')
            if trigger:
                if style != 'analysis':
                    raise ValueError('Trigger feedback belongs to analysis items')
                _fields(trigger, ('source', 'hold_ms'), ('enabled',))
                _signal(trigger['source'])
                if trigger.get('enabled'):
                    _target(trigger['enabled'])
                if type(trigger['hold_ms']) is not int or not 0 <= trigger['hold_ms'] <= 1000:
                    raise ValueError('MIX trigger hold must be 0..1000 ms')
        # Reject callables, OP/Par objects, NaNs and other runtime state.
        import json
        return json.loads(json.dumps(profile, allow_nan=False))
    except (KeyError, TypeError, OverflowError) as exc:
        raise ValueError('Incomplete MIX descriptor') from exc


def analysis_profile(source, bands=('Low', 'Mid'), *, id='analysis.main'):
    """Describe known palette parameters, without enabling detection or audio."""
    reference(source)
    if (not isinstance(bands, (list, tuple)) or not bands
            or any(b not in ANALYSIS_BANDS for b in bands) or len(set(bands)) != len(bands)):
        raise ValueError('Choose unique analysis bands from ' + ', '.join(ANALYSIS_BANDS))
    items = []
    for band in bands:
        controls = {}
        for key, suffix, label, kind in (
                ('threshold', 'thresh', 'Thresh', 'float'),
                ('gain', 'gain', 'Gain', 'float'), ('add', 'add', 'Add', 'float'),
                ('smooth', 'smooth', 'Smooth', 'float'), ('active', 'active', 'Active', 'toggle')):
            if band in ANALYSIS_DETECTORS and key not in ('threshold', 'active'):
                continue
            prefix = ANALYSIS_DETECTORS[band][0] if band in ANALYSIS_DETECTORS else band
            controls[key] = dict(label=label, kind=kind,
                                 target=dict(op=source, parameter=prefix + suffix))
        item = dict(id=band.lower(), label=band, primary='threshold', controls=controls,
                          meter=dict(source=dict(kind='chop', op=source + '/out1', channels=[band.lower()]),
                                     measure='scalar', range=[0, 1], stage='analysis output'))
        if band in ANALYSIS_DETECTORS:
            prefix, level_op, level_channel, pulse_channel, maximum = ANALYSIS_DETECTORS[band]
            item['meter'] = dict(source=dict(kind='chop', op=source + '/' + level_op, channels=[level_channel]),
                                 measure='scalar', range=[0, maximum], stage=band + ' level before threshold',
                                 overview_reference='threshold',focus_reference='threshold')
            item['trigger'] = dict(source=dict(kind='chop', op=source + '/out1', channels=[pulse_channel]),
                                   enabled=dict(op=source, parameter=prefix + 'active'), hold_ms=200)
        items.append(item)
    return validate(dict(version=1, style='analysis', id=id, source=source, items=items))


def projection(profile, view, selected):
    """Eight (item index, control key) addresses. Unsupported views stay empty.

    Focus CI is an offset, not a page number. Only physically accepted CI=0 is
    enabled here; a later page must not alias Send A or a previous control.
    """
    result = [None] * 8
    if view is None:
        return result
    items = profile['items']
    keys = DETAIL_KEYS.get(profile['style'])
    if keys is None:
        return result
    kind, data = view
    if kind == 'all':
        family, knob, button, send = data
        if family != 0:
            return result
        for index, item in enumerate(items):
            if knob == 0:
                key = item['primary']
            elif knob == 1:
                key = keys[1]
            else:
                key = keys[2 + send] if 2 + send < len(keys) else None
            if key in keys and key in item['controls'] and item['controls'][key]['kind'] == {'operation':'menu', 'swap':'toggle'}.get(key, 'float'):
                result[index] = index, key
    elif kind == 'focus' and data == 0 and 0 <= selected < len(items):
        for lane, key in enumerate(keys):
            if key in items[selected]['controls'] and items[selected]['controls'][key]['kind'] == {'operation':'menu', 'swap':'toggle'}.get(key, 'float'):
                result[lane] = selected, key
    return result


def button_projection(profile, view):
    """Overview On/Off is Active. Focus buttons remain firmware item selectors."""
    result = [None] * 8
    if view is not None and view[0] == 'all' and view[1][0] == 0 and view[1][2] == 0:
        for index, item in enumerate(profile['items']):
            if item['controls'].get('active', {}).get('kind') == 'toggle':
                result[index] = index, 'active'
    return result
