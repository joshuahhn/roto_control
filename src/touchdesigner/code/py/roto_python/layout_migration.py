"""Explicit COMP migration plans and offline, serialized commits.

No discovery, target writes, binding replacement or hardware traffic. Owner
allocation is a separate prerequisite; every moved atomic Device has an explicit
classification with documentary evidence. Recovery files are exclusive copies.
"""
import base64
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import uuid

from protocol import digest

VERSION = 1
LEDGER = 'comp_migrations'


def encode(value):
    """Lossless JSON envelope for persisted configuration; reject opaque objects."""
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError('Recovery configuration contains a nonfinite value')
        return value
    if isinstance(value, bytes):
        return {'type': 'bytes', 'value': base64.b64encode(value).decode('ascii')}
    if isinstance(value, (list, tuple, set)):
        items = [encode(v) for v in value]
        if isinstance(value, set):
            items.sort(key=lambda v: json.dumps(v, sort_keys=True))
        return {'type': type(value).__name__, 'value': items}
    if isinstance(value, dict):
        if any(type(k) is not str for k in value):
            raise ValueError('Recovery dictionaries require string keys')
        return {'type': 'dict', 'value': {k: encode(v) for k, v in value.items()}}
    raise ValueError('Unsupported recovery value: ' + type(value).__name__)


def fingerprint(value):
    return hashlib.sha256(json.dumps(encode(value), sort_keys=True,
                                    separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def decode(value):
    """Read a recovery envelope for inspection/restoration planning, never apply."""
    if not isinstance(value, dict):
        return value
    kind, contents = value['type'], value['value']
    if kind == 'dict':
        return {k: decode(v) for k, v in contents.items()}
    if kind == 'bytes':
        return base64.b64decode(contents, validate=True)
    constructors = {'list': list, 'tuple': tuple, 'set': set}
    if kind not in constructors:
        raise ValueError('Unknown recovery envelope type')
    return constructors[kind](decode(v) for v in contents)


def records(snapshot):
    return {(l['id'], t['id'], p['id']): (l, t, p)
            for l in snapshot['records'] for t in l['tracks'] for p in t['plugins']}


def _new_id(migration_id, *parts):
    return uuid.uuid5(uuid.NAMESPACE_URL, json.dumps([VERSION, migration_id, *parts])).hex


def _layouts_module(manager):
    """Resolve the installed sibling DAT, never a standalone Python import."""
    try:
        owner = manager.owner
        dat = owner.op('layouts')
        if (owner != manager.ext.ownerComp or dat is None or not dat.valid
                or not dat.isDAT or dat.name != 'layouts' or dat.parent() != owner):
            raise ValueError('Missing or foreign layouts DAT')
        module = dat.module
        if (module.Layouts is not type(manager)
                or not isinstance(module.FIELDS, tuple) or not module.FIELDS
                or any(not isinstance(field, str) or not field for field in module.FIELDS)
                or len(set(module.FIELDS)) != len(module.FIELDS)
                or not isinstance(module.DEFAULTS, tuple) or len(module.DEFAULTS) != len(module.FIELDS)
                or not isinstance(module.ActivationRollbackError, type)
                or not issubclass(module.ActivationRollbackError, RuntimeError)):
            raise ValueError('Incompatible installed layouts module')
        return module
    except Exception as exc:
        raise ValueError('Readable same-controller layouts DAT is required for migration') from exc


def _library_check(plugin):
    targets = {}
    for target in plugin['state'].get('page_targets', []):
        if target['id'] in targets:
            raise ValueError('Duplicate library target ID')
        targets[target['id']] = target
    targets.update({t['id']: t for t in plugin['targets']})
    indices, hashes = set(), set()
    for target in targets.values():
        if 'action_id' in target:
            if (not isinstance(target['action_id'], str) or not target['action_id'].strip()
                    or target.get('kind') != 'button' or target.get('mode') != 'pulse'
                    or target.get('comp', '') or target.get('parameter', '')):
                raise ValueError('Invalid saved Action reference; migration will not repair it')
            # Stable references may be unavailable. Never resolve/register/recall
            # a provider during administrative relocation.
        elif not isinstance(target.get('comp'), str) or not isinstance(target.get('parameter'), str):
            raise ValueError('Callback targets need reconstruction; migration cannot convert them')
        index = target.get('index')
        identity = target.get('identity')
        if type(index) is not int or not 0 <= index < 16384 or not isinstance(identity, str) or not identity:
            raise ValueError('Migration requires saved index and wire identity')
        wire = digest(identity, 6)
        if index in indices or wire in hashes:
            raise ValueError('Library index/wire collision; migration will not re-LEARN')
        indices.add(index); hashes.add(wire)


def build_plan(manager, snapshot, migration_id, classifications, entries=None, active_variants=None):
    """Build on a detached flushed snapshot; never infer record ownership."""
    layouts = _layouts_module(manager)
    FIELDS, DEFAULTS = layouts.FIELDS, layouts.DEFAULTS
    if not isinstance(migration_id, str) or not migration_id.strip():
        raise ValueError('An explicit migration ID is required')
    request = dict(migration_id=migration_id, classifications=copy.deepcopy(classifications),
                   entries=copy.deepcopy(entries or {}), active_variants=copy.deepcopy(active_variants or {}))
    if (not isinstance(classifications, list) or not isinstance(request['entries'], dict)
            or not isinstance(request['active_variants'], dict)):
        raise ValueError('Classifications must be a list; entry/active choices must be dictionaries')
    prior = snapshot.get(LEDGER, {}).get(migration_id)
    if prior is not None:
        if prior['version'] != VERSION or prior['request'] != request:
            raise ValueError('Migration ID already used with another request/version')
        _check_completed(snapshot, prior)
        return dict(version=VERSION, request=request, completed=True, receipt=copy.deepcopy(prior))
    manager.validate(snapshot)
    source = records(snapshot)
    decisions, moves = {}, {}
    for item in classifications:
        if not isinstance(item, dict):
            raise ValueError('Invalid classification')
        key = tuple(item.get('source', ()))
        if len(key) != 3 or key not in source or key in decisions:
            raise ValueError('Unknown or duplicate classification source triple')
        decisions[key] = item
        if item.get('decision') == 'retain':
            if not isinstance(item.get('reason'), str) or not item['reason'].strip():
                raise ValueError('Retained classification needs a reason')
            continue
        if item.get('decision') != 'move':
            raise ValueError('Classification decision must be move or retain')
        layout, track, plugin = source[key]
        if layout.get('category') != 'LEGACY':
            raise ValueError('Only explicitly classified LEGACY Devices can move; CUSTOM stays independent')
        evidence = item.get('evidence')
        if (not isinstance(evidence, dict) or evidence.get('kind') not in
                ('user-confirmed-ownership', 'registration-provenance')
                or not isinstance(evidence.get('reference'), str) or not evidence['reference'].strip()):
            raise ValueError('Explicit ownership evidence is required; Focus/name/targets are insufficient')
        destination = next((l for l in snapshot['records'] if l['id'] == item.get('owner_layout_id')), None)
        owner = destination.get('owner') if destination else None
        if not owner or destination['category'] != 'COMP' or owner['id'] != item.get('owner_id'):
            raise ValueError('Destination must be an explicitly registered COMP owner')
        manager.owner_ready(destination['id'], required=True)
        link = plugin.get('focus_comp')
        if not link or link.get('state') != 'bound':
            raise ValueError('Unlinked/missing records remain in place')
        comp = manager.owner.op(link['path'])
        if (comp is not manager.owner_handles.get(owner['id']) or manager.owner_token(comp) != owner['id']
                or os.path.normpath(link['path']) != owner['path']):
            raise ValueError('Source Focus does not match the explicitly confirmed live owner')
        _library_check(plugin)
        moves[key] = destination['id']
    candidate = copy.deepcopy(snapshot)
    destinations = {l['id']: l for l in candidate['records']}
    lineage = []
    old_route = manager.context()['key']
    locations = {}
    # Original Track IDs are reused once. Retained children have first claim;
    # otherwise the first moved Device in saved order determines the reuse.
    for layout in candidate['records']:
        if layout['category'] != 'LEGACY':
            continue
        kept_tracks = []
        for track in layout['tracks']:
            groups = {}
            for plugin in track['plugins']:
                key = (layout['id'], track['id'], plugin['id'])
                groups.setdefault(moves.get(key, layout['id']), []).append(plugin)
            reuse = layout['id'] if layout['id'] in groups else next(iter(groups))
            for destination_id, plugins in groups.items():
                moved_track = copy.deepcopy(track)
                moved_track['plugins'] = plugins
                if destination_id != reuse:
                    moved_track['id'] = 'track.' + _new_id(migration_id, layout['id'], track['id'], destination_id)
                if track['active_plugin'] not in [p['id'] for p in plugins]:
                    moved_track['active_plugin'] = plugins[0]['id']
                if destination_id == layout['id']:
                    kept_tracks.append(moved_track)
                else:
                    destination = destinations[destination_id]
                    for plugin in plugins:
                        plugin['focus_comp'] = dict(plugin['focus_comp'], owner_id=destination['owner']['id'],
                                                    path=destination['owner']['path'])
                    destination['tracks'].append(moved_track)
                    lineage.append(dict(source=[layout['id'], track['id']],
                                        destination=[destination_id, moved_track['id']],
                                        reused_id=destination_id == reuse))
                for plugin in plugins:
                    locations[plugin['id']] = (destination_id, moved_track['id'], plugin['id'])
        if not kept_tracks:
            # Preserve the original Layout shell; new empty IDs have no hardware
            # assignments and never duplicate the moved variant's wire identity.
            track_id = 'track.' + _new_id(migration_id, layout['id'], 'empty-track')
            plugin_id = 'plugin.' + _new_id(migration_id, layout['id'], 'empty-device')
            plugin = dict(id=plugin_id, group_id=plugin_id, device_id='TD controls:' + plugin_id,
                          plugin_name='CUSTOM', name_mode='manual', targets=[],
                          state={f: copy.deepcopy(v) for f, v in zip(FIELDS, DEFAULTS)})
            kept_tracks = [dict(id=track_id, name='EFFECT', active_plugin=plugin_id, plugins=[plugin])]
            lineage.append(dict(source=[layout['id']], destination=[layout['id'], track_id, plugin_id],
                                reused_id=False, reason='retained empty source Layout shell'))
        layout['tracks'] = kept_tracks
        if layout['active_track'] not in [t['id'] for t in kept_tracks]:
            layout['active_track'] = kept_tracks[0]['id']
    new_route = locations.get(old_route[2], old_route)
    candidate['active'] = new_route[0]
    destinations[new_route[0]]['active_track'] = new_route[1]
    next(t for t in destinations[new_route[0]]['tracks'] if t['id'] == new_route[1])['active_plugin'] = new_route[2]
    for layout_id, entry_id in request['entries'].items():
        destination = destinations.get(layout_id)
        if not destination or destination['category'] != 'COMP' or entry_id not in [
                p['id'] for t in destination['tracks'] for p in t['plugins']]:
            raise ValueError('Entry must be an existing destination Device record ID')
        manager.owner_ready(layout_id, required=True)
        entry = next(p for t in destination['tracks'] for p in t['plugins'] if p['id'] == entry_id)
        if (entry.get('focus_comp') or {}).get('owner_id') != destination['owner']['id']:
            raise ValueError('Entry needs the destination owner-qualified Focus')
        destination['owner']['entry_plugin_id'] = entry_id
    for layout_id, plugin_id in request['active_variants'].items():
        destination = destinations.get(layout_id)
        track = next((t for t in destination['tracks'] if any(p['id'] == plugin_id for p in t['plugins'])), None) if destination else None
        if not destination or destination['category'] != 'COMP' or track is None:
            raise ValueError('Saved active variant must be an existing owned Device')
        manager.owner_ready(layout_id, required=True)
        plugin = next(p for p in track['plugins'] if p['id'] == plugin_id)
        if (plugin.get('focus_comp') or {}).get('owner_id') != destination['owner']['id']:
            raise ValueError('Saved active variant requires owner-qualified Focus')
        if layout_id == new_route[0] and (track['id'], plugin_id) != new_route[1:]:
            raise ValueError('Saved active choice would replace routing; explicitly Activate separately')
        destination['active_track'] = track['id']; track['active_plugin'] = plugin_id
    selection_changes = []
    for layout in snapshot['records']:
        old_track = next(t for t in layout['tracks'] if t['id'] == layout['active_track'])
        new_layout = destinations[layout['id']]
        new_track = next(t for t in new_layout['tracks'] if t['id'] == new_layout['active_track'])
        before = [old_track['id'], old_track['active_plugin']]
        after_choice = [new_track['id'], new_track['active_plugin']]
        if before != after_choice:
            selection_changes.append(dict(layout_id=layout['id'], before=before, after=after_choice,
                                          reason='explicit active variant' if layout['id'] in request['active_variants'] else
                                          'preserve routing Device' if layout['id'] == new_route[0] else
                                          'repair source container after partition'))
    after = records(candidate)
    manifest = []
    for key, (layout, track, plugin) in source.items():
        destination_key = next(k for k in after if k[2] == plugin['id'])
        expected = copy.deepcopy(plugin)
        if key in moves:
            expected['focus_comp'] = dict(expected['focus_comp'], owner_id=destinations[moves[key]]['owner']['id'],
                                          path=destinations[moves[key]]['owner']['path'])
        if expected != after[destination_key][2]:
            raise ValueError('Atomic Device preservation failed')
        retained_reason = ('manual CUSTOM configuration' if layout['category'] == 'CUSTOM' else
                           'already COMP-owned' if layout['category'] == 'COMP' else
                           'unlinked or missing Focus; ownership unclassified' if not plugin.get('focus_comp')
                           or plugin['focus_comp'].get('state') != 'bound' else
                           'ownership not explicitly classified; Focus is insufficient')
        manifest.append(dict(source=list(key), destination=list(destination_key),
                             decision='move' if key in moves else 'retain',
                             reason=decisions.get(key, {}).get('reason', 'explicit ownership evidence' if key in moves
                                                             else retained_reason),
                             device_fingerprint=fingerprint(expected),
                             device_wire_hash=list(digest(plugin['device_id'], 8))))
    receipt = dict(version=VERSION, request=request, source_fingerprint=fingerprint(snapshot),
                   manifest=manifest, lineage=lineage, selection_changes=selection_changes)
    if moves or request['entries'] or request['active_variants']:
        candidate.setdefault(LEDGER, {})[migration_id] = receipt
    manager.validate(candidate)
    return dict(version=VERSION, request=request, completed=False, revision=snapshot['revision'],
                source_fingerprint=fingerprint(snapshot), result=candidate,
                manifest=manifest, lineage=lineage, route=list(new_route), selection_changes=selection_changes)


def _check_completed(snapshot, receipt):
    actual = records(snapshot)
    for row in receipt['manifest']:
        key = tuple(row['destination'])
        if key not in actual:
            raise ValueError('Completed migration record was removed; do not resurrect it')
    # User edits after completion are legitimate. Re-running returns the original
    # receipt, never replays an old candidate or overwrites those edits.


def guard(manager):
    manager.owner_guard()
    e = manager.ext
    if e._host.connected or e._host.plugin or getattr(e, '_process', None) is not None:
        raise ValueError('Disconnect completely before planning/applying migration')
    if manager.quarantined or getattr(e, '_restore_pending', False):
        raise ValueError('Repair/restore the routing configuration before migration')


def plan(manager, migration_id, classifications, entries=None, active_variants=None):
    guard(manager)
    manager.ext._follow.refresh_links()
    snapshot = manager.registry_snapshot()
    guard(manager)  # fresh owner observation may have quarantined routing
    return build_plan(manager, snapshot, migration_id, classifications, entries, active_variants)


def _recovery(manager, snapshot):
    owner = manager.owner
    if not isinstance(getattr(owner, 'storage', None), dict):
        raise ValueError('Full local controller storage is required for recovery')
    pars = {}
    for p in getattr(owner, 'customPars', []):
        pars[p.name] = {k: _portable_parameter_value(getattr(p, k)) for k in
                        ('val', 'expr', 'bindExpr', 'enable', 'enableExpr', 'menuNames', 'menuLabels',
                         'menuSource', 'default', 'defaultExpr', 'defaultBindExpr', 'label', 'order',
                         'style', 'readOnly', 'normMin', 'normMax', 'min', 'max', 'clampMin', 'clampMax')
                        if hasattr(p, k)}
        for field in ('mode', 'defaultMode'):
            if hasattr(p, field):
                value = getattr(p, field)
                pars[p.name][field] = getattr(value, 'name', str(value))
        if hasattr(p, 'page'):
            pars[p.name]['page'] = p.page.name
    sources = {}
    for name in ('registration', 'base_targets/targets'):
        dat = owner.op(name)
        if dat is not None and hasattr(dat, 'text'):
            sources[name] = dat.text
    context = {k: copy.deepcopy(getattr(manager, k)) for k in
               ('selected_track', 'selected_plugin', 'first_track', 'first_plugin', 'confirmed', 'quarantined')}
    context['routing_key'] = manager.context()['key']
    context['follower'] = {k: _portable_parameter_value(getattr(manager.ext._follow, k)) for k in
                           ('baseline', 'scope', 'observed_comp', 'connection_generation', 'routing_epoch',
                            'pending', 'status', 'error', 'paused', 'gated', 'backlog')}
    context['host'] = {k: copy.deepcopy(getattr(manager.ext._host, k)) for k in
                      ('connected', 'plugin', 'learning', 'device_id', 'plugin_index', 'track_name', 'plugin_name')}
    return dict(registry=copy.deepcopy(snapshot), storage=copy.deepcopy(owner.storage),
                context=context, parameters=pars, sources=sources)


def _portable_parameter_value(value):
    if getattr(value, 'isOP', False):
        return value.path
    if isinstance(value, (list, tuple)):
        return type(value)(_portable_parameter_value(v) for v in value)
    return copy.deepcopy(value)


def apply(manager, supplied_plan, recovery_path):
    """Single synchronous TD-thread transaction. No binding install or selection."""
    ActivationRollbackError = _layouts_module(manager).ActivationRollbackError
    guard(manager)
    manager.ext._follow.refresh_links()
    current = manager.registry_snapshot()
    guard(manager)
    request = supplied_plan['request']
    expected = build_plan(manager, current, request['migration_id'], request['classifications'],
                          request['entries'], request['active_variants'])
    if expected['completed']:
        prior = expected['receipt']
        if not supplied_plan.get('completed') and supplied_plan.get('source_fingerprint') != prior['source_fingerprint']:
            raise ValueError('Completed migration does not match this source plan')
        return dict(changed=False, receipt=copy.deepcopy(prior))
    if supplied_plan != expected:
        raise ValueError('Stale or modified migration plan; rebuild and review')
    if expected['result'] == current:
        return dict(changed=False, manifest=expected['manifest'])
    recovery = _recovery(manager, current)
    encoded = encode(recovery)  # fail before committing or creating a lossy copy
    follower = manager.ext._follow
    handles = dict(follower.handles)
    owner_handles = dict(manager.owner_handles)
    parameter_modes = {p.name: p.mode for p in getattr(manager.owner, 'customPars', []) if hasattr(p, 'mode')}
    follower_state = {k: getattr(follower, k) for k in
                      ('baseline', 'scope', 'observed_comp', 'routing_epoch', 'pending', 'status', 'error')}
    intent_token = follower.sequence, follower.connection_generation
    old_index = manager.ext._host.plugin_index
    manager.mutating = True
    committed = False
    try:
        # Recheck under the same lock as commit. No asynchronous gap, no
        # CheckLayoutRevision token mistaken for a transactional guarantee.
        manager.refresh_owners(force=True)
        if (manager.data['revision'] != supplied_plan['revision']
                or fingerprint(manager.data) != supplied_plan['source_fingerprint']
                or fingerprint(manager.owner.fetch('layout_registry')) != supplied_plan['source_fingerprint']):
            raise ValueError('Layout registry changed inside migration transaction')
        path = Path(recovery_path)
        if path.suffix != '.json':
            raise ValueError('Recovery copy must use a new .json path, not a native binary')
        with path.open('x', encoding='utf-8') as stream:
            json.dump(dict(version=VERSION, migration_id=request['migration_id'],
                           source_fingerprint=supplied_plan['source_fingerprint'], recovery=encoded), stream,
                      sort_keys=True, ensure_ascii=True, indent=2)
            stream.flush(); os.fsync(stream.fileno())
        committed = True
        manager.data = copy.deepcopy(expected['result'])
        manager.save()
        manager.selected_track, manager.selected_plugin = expected['route'][1:]
        manager.first_track = (manager.layout()['tracks'].index(manager.track()) // 8) * 8
        manager.first_plugin = (manager.track()['plugins'].index(manager.plugin()) // 8) * 8
        manager.ext._host.plugin_index = manager.track()['plugins'].index(manager.plugin())
        for l in manager.data['records']:
            for t in l['tracks']:
                for p in t['plugins']:
                    link = p.get('focus_comp') or {}
                    owner_id = link.get('owner_id')
                    if owner_id:
                        comp = manager.owner_handles.get(owner_id)
                        if comp is not None and l['owner']['state'] == 'bound':
                            follower.handles[p['id']] = comp
                        else:
                            follower.handles.pop(p['id'], None)
        # Administrative relocation is not a new selection/pane/startup event.
        # Preserve the latest observed selection; update an established scope so
        # the common-base follower also avoids re-baselining on the new container.
        if follower.scope == (current['active'], manager.legacy):
            follower.scope = (expected['route'][0], manager.legacy)
        follower.routing_epoch += 1
        manager.menu()
        manager.ext._publish()
        return dict(changed=True, recovery_path=str(path.absolute()),
                    receipt=copy.deepcopy(manager.data[LEDGER][request['migration_id']]))
    except Exception as original:
        if not committed:
            raise
        try:
            revision = max(manager.data['revision'], current['revision']) + 1
            manager.data = copy.deepcopy(current); manager.data['revision'] = revision
            manager.owner.storage.clear(); manager.owner.storage.update(copy.deepcopy(recovery['storage']))
            manager.owner.store('layout_registry', copy.deepcopy(manager.data))
            for key, value in recovery['context'].items():
                if key not in ('routing_key', 'follower', 'host'):
                    setattr(manager, key, value)
            manager.ext._host.plugin_index = old_index
            manager.owner_handles = owner_handles
            follower.handles = handles
            fresh_intent = (follower.sequence, follower.connection_generation) != intent_token
            for key, value in follower_state.items():
                if key == 'routing_epoch':
                    follower.routing_epoch = max(follower.routing_epoch, value)
                elif fresh_intent and key in ('baseline', 'observed_comp', 'pending', 'status', 'error'):
                    continue  # a new selection/ingress fence is not rollback state
                else:
                    setattr(follower, key, value)
            manager.menu()
            for name, values in recovery['parameters'].items():
                if name not in ('Layout', 'Track', 'Plugin', 'Layoutname', 'Pluginname', 'Focuscomp'):
                    continue  # target/native settings were never changed
                par = getattr(manager.owner.par, name)
                for key, value in values.items():
                    if key not in ('val', 'expr', 'bindExpr', 'enable', 'menuNames', 'menuLabels'):
                        continue
                    if getattr(par, key) != value:
                        setattr(par, key, value)
                if name in parameter_modes and par.mode != parameter_modes[name]:
                    par.mode = parameter_modes[name]
            manager.ext._publish()
        except Exception as rollback:
            follower.pending = None; follower.paused = True; follower.fence()
            follower.status = 'paused'
            follower.error = str(original) + '; rollback failed: ' + str(rollback)
            raise ActivationRollbackError(follower.error) from original
        raise
    finally:
        manager.mutating = False
