"""Durable slot values, routed through the Device's current control mappings.

Snapshots intentionally follow replacement mappings and the current control page.
Only JSON data persists; no target handles, paths, descriptors or callbacks.
"""
import copy
import json
import math
import uuid
from binding import parameter_value

STORE = 'snapshot_presets'
PREFIX = 'snapshot.'


def plain(value):
    return json.loads(json.dumps(value, allow_nan=False))


def slot_key(slot):
    if (not isinstance(slot, (list, tuple)) or len(slot) != 2
            or slot[0] != 'knob' or type(slot[1]) is not int
            or not 1 <= slot[1] <= 8):
        raise ValueError('Snapshot captures Knobs only: (knob, 1..8)')
    return tuple(slot)


def normalized(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('Snapshot control value must be finite in 0..1')
    return float(value)


class Snapshots:
    def __init__(self, extension):
        self.ext = extension
        self.owner = extension.ownerComp

    def database(self):
        data = plain(self.owner.fetch(STORE, dict(version=2, records=[], deleted=[])))
        if (not isinstance(data, dict) or data.get('version') != 2
                or not isinstance(data.get('records'), list) or not isinstance(data.get('deleted'), list)):
            raise ValueError('Unsupported Snapshot database; retain it for recovery')
        ids = set()
        for record in data['records']:
            if (not isinstance(record, dict) or not isinstance(record.get('id'), str)
                    or not record['id'].startswith(PREFIX) or record['id'] in ids
                    or not isinstance(record.get('label'), str) or not record['label'].strip()
                    or type(record.get('revision')) is not int or record['revision'] < 1
                    or not isinstance(record.get('scope'), dict) or not isinstance(record.get('entries'), list)
                    or not record['entries']):
                raise ValueError('Invalid Snapshot record; retain it for recovery')
            keys = [slot_key((e['kind'], e['slot'])) for e in record['entries']]
            if len(set(keys)) != len(keys):
                raise ValueError('Duplicate Snapshot slots')
            for entry in record['entries']:
                normalized(entry['value'])
            ids.add(record['id'])
        return data

    def record(self, id):
        record = next((r for r in self.database()['records'] if r['id'] == id), None)
        if record is None:
            raise ValueError('Snapshot deleted or unavailable: ' + str(id))
        return record

    def scope(self, context=None):
        manager = getattr(self.ext, '_layouts', None)
        if manager is None or manager.legacy and context is None:
            return dict(category='REGISTRATION', context=None, owner_id=None)
        context = tuple(context or manager.context()['key'])
        if len(context) != 3:
            raise ValueError('Snapshot scope needs full Layout/Track/Device IDs')
        manager.record(*context)
        manager.owner_ready(context[0], required=True)
        layout = manager.layout(context[0])
        return dict(category=layout.get('category', 'LEGACY'), context=list(context),
                    owner_id=(layout.get('owner') or {}).get('id'))

    def active(self, scope):
        if self.scope() != scope:
            raise ValueError('Activate the saved Snapshot Device before capture/recall')
        manager = getattr(self.ext, '_layouts', None)
        if manager is not None and manager.quarantined and not manager.legacy:
            raise ValueError('Activate the repaired Layout before Snapshot recall')

    def binding(self, key):
        collection = self.ext._collection
        binding = collection.bindings.get(key) if collection is not None else None
        if binding is None:
            raise ValueError('Snapshot slot is currently unassigned: ' + str(key))
        par = binding.parameter
        if (collection.modes[key] == 'pulse' or par is None or getattr(binding, 'action_id', None)
                or par.style not in ('Float', 'Int', 'Toggle', 'Menu')):
            raise ValueError('Snapshot slots need real Float/Int/Toggle/Menu mappings; no Pulse/actions/callbacks')
        if not binding.valid or not getattr(par, 'valid', True):
            raise ValueError('Snapshot slot mapping is suspended or unavailable: ' + str(key))
        binding.check_parameter()  # Existing mapping's current Menu/range/write policy.
        return binding

    def selected(self, slots):
        if slots is None:
            collection = self.ext._collection
            slots = [key for key in (collection.bindings if collection is not None else ()) if key[0] == 'knob']
        keys = [slot_key(slot) for slot in slots]
        if not keys or len(set(keys)) != len(keys):
            raise ValueError('Select nonempty unique current-page slots')
        return keys

    def capture(self, slots):
        entries = []
        for key in self.selected(slots):
            binding = self.binding(key)
            value = normalized(binding.normalized(parameter_value(binding.parameter)))
            entries.append(dict(kind=key[0], slot=key[1], value=value))
        return entries

    def save(self, label, slots=None, context=None, id=None, expected_revision=None):
        if not isinstance(label, str) or not label.strip():
            raise ValueError('Snapshot needs a nonempty name')
        data = self.database()
        old = self.record(id) if id is not None else None
        if old and expected_revision != old['revision']:
            raise ValueError('Snapshot revision changed; reopen confirmation')
        scope = old['scope'] if old else self.scope(context)
        self.active(scope)
        if any(r['id'] != id and r['scope'] == scope and r['label'] == label.strip() for r in data['records']):
            raise ValueError('Snapshot name exists; explicit overwrite required')
        if old and slots is None:
            slots = [(e['kind'], e['slot']) for e in old['entries']]
        record = dict(id=id or PREFIX + uuid.uuid4().hex, label=label.strip(), scope=scope,
                      revision=old['revision'] + 1 if old else 1, entries=self.capture(slots))
        data['records'] = [r for r in data['records'] if r['id'] != record['id']] + [record]
        self.owner.store(STORE, plain(data))
        self.install(record)
        return copy.deepcopy(record)

    def install(self, record):
        def recall(event):
            return self.recall(record['id'])
        recall._snapshot_provider = True
        self.ext.RegisterAction(record['id'], record['label'], recall, replace=True)

    def restore(self):
        for record in self.database()['records']:
            self.install(record)

    def delete(self, id, expected_revision):
        record = self.record(id)
        if expected_revision != record['revision']:
            raise ValueError('Snapshot revision changed; reopen confirmation')
        data = self.database()
        data['records'] = [r for r in data['records'] if r['id'] != id]
        data['deleted'].append(dict(id=id, label=record['label'], revision=record['revision']))
        self.owner.store(STORE, plain(data))
        self.ext.UnregisterAction(id)
        return True

    def plan(self, record):
        self.active(record['scope'])
        if self.ext._host.touched:
            raise ValueError('Release touched controls before Snapshot recall')
        return [(entry, self.binding((entry['kind'], entry['slot']))) for entry in record['entries']]

    def validate(self, id):
        record = self.record(id)
        try:
            self.plan(record)
            return dict(preset_id=id, revision=record['revision'], status='succeeded', error='')
        except Exception as exc:
            return dict(preset_id=id, revision=record['revision'], status='validation_failed', error=str(exc))

    def inspect(self, id):
        record = self.record(id)
        for entry in record['entries']:
            try:
                self.active(record['scope'])
                binding = self.binding((entry['kind'], entry['slot']))
                entry.update(mapping_id=binding.id, current_value=normalized(binding.normalized(parameter_value(binding.parameter))),
                             target_value=parameter_value(binding.parameter), label=binding.label, error='')
            except Exception as exc:
                entry.update(mapping_id=None, current_value=None, target_value=None, error=str(exc))
        record['validation'] = self.validate(id)
        return plain(record)

    def actual(self, binding):
        binding.check_parameter()
        if not getattr(binding.parameter, 'valid', True):
            raise ValueError('Current mapping parameter is unavailable')
        value = parameter_value(binding.parameter)
        if type(value) not in (bool, int, float) or not math.isfinite(value):
            raise ValueError('Current mapping readback is nonfinite/non-numeric')
        return value

    def recall(self, id):
        record = self.record(id)
        result = dict(preset_id=id, revision=record['revision'], status='validation_failed', error='',
                      entries=[dict(kind=e['kind'], slot=e['slot'], value=e['value'], attempted=False,
                                    verified=False, actual_value=None, error='Not attempted') for e in record['entries']])
        try:
            plan = self.plan(record)  # Only current mapping readiness; no historical target checks.
        except Exception as exc:
            result['error'] = str(exc)
            return result
        collection = self.ext._collection
        failed = None
        try:
            for (entry, binding), state in zip(plan, result['entries']):
                failed = state
                key = (entry['kind'], entry['slot'])
                self.active(record['scope'])
                if (self.ext._collection is not collection or collection.bindings.get(key) is not binding
                        or self.record(id)['revision'] != record['revision']):
                    raise ValueError('Snapshot/mappings changed during recall')
                wanted = binding.from_normalized(entry['value'])
                state.update(mapping_id=binding.id, output_value=wanted, attempted=True, error='')
                binding.write(wanted, 'snapshot')
                state['actual_value'] = self.actual(binding)
                state['verified'] = math.isclose(state['actual_value'], wanted, rel_tol=1e-12, abs_tol=1e-12)
                if not state['verified']:
                    raise ValueError('Current mapping readback mismatch')
            # Report late callback changes honestly; this is readback, not rollback.
            for (entry, binding), state in zip(plan, result['entries']):
                failed = state
                self.active(record['scope'])
                if (self.ext._collection is not collection
                        or self.binding((entry['kind'], entry['slot'])) is not binding
                        or self.record(id)['revision'] != record['revision']):
                    raise ValueError('Snapshot/mappings changed during recall')
                state['actual_value'] = self.actual(binding)
                state['verified'] = math.isclose(state['actual_value'], state['output_value'], rel_tol=1e-12, abs_tol=1e-12)
                if not state['verified']:
                    raise ValueError('Final current mapping readback mismatch')
            result.update(status='succeeded', error='')
        except Exception as exc:
            result.update(status='partial' if any(s['attempted'] for s in result['entries']) else 'execution_failed', error=str(exc))
            for (_, binding), state in zip(plan, result['entries']):
                try:
                    state['actual_value'] = self.actual(binding)
                    state['verified'] = state['verified'] and math.isclose(state['actual_value'], state.get('output_value', 0), rel_tol=1e-12, abs_tol=1e-12)
                except Exception as read_error:
                    state.update(actual_value=None, verified=False, error=str(read_error))
            if failed is not None:
                failed.update(error=str(exc), verified=False)
        # Binding.write sets its expected echo; explicitly feed the existing Host
        # here so its suppression does not hide Snapshot motor/LCD updates.
        for (entry, binding), state in zip(plan, result['entries']):
            key = (entry['kind'], entry['slot'])
            if (state['actual_value'] is not None and self.ext._collection is collection
                    and collection.bindings.get(key) is binding):
                try:
                    value = binding.normalized(state['actual_value'])
                    self.ext._host.parameter_changed(value, key)
                    if key == ('knob', 1):
                        self.ext._mirror(value)
                except Exception as exc:
                    result.update(status='partial', error='Snapshot feedback failed: ' + str(exc))
        return plain(result)
