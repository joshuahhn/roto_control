"""Prepared native fixture; NOT executed by source tests.

Execute this file in TD during the coordinated native window. Pass an explicit
empty test parent, this worktree's source directory and a valid external Python.
No Connect, physical MIDI ports, user controller copy or canonical artifacts.
Run build_fixture; wait one frame; exercise; wait; save_reload; wait; finish.
All tox copies and evidence are retained. finish leaves the holder for inspection;
cleanup is explicit and requires captured evidence. Failure quiesces, never destroys.
"""
import copy
from functools import wraps
import hashlib
import json
from pathlib import Path
import tempfile
import uuid

HOLDER = 'base_action_preset_verification'


def _artifacts(paths):
    records = []
    for name in paths:
        path = Path(name)
        item = dict(path=str(path), exists=path.is_file())
        if item['exists']:
            try:
                item.update(size=path.stat().st_size,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            except OSError as exc:
                item['capture_error'] = str(exc)
        records.append(item)
    return records


def _quiesce(holder):
    """Best-effort fixture-local stop; preserve nodes, source and disk copies."""
    errors = []
    try:
        nodes = [holder, *holder.findChildren()]
    except Exception as exc:
        nodes = [holder]
        errors.append(f'Fixture traversal: {exc}')
    # Stop every execute DAT before pulsing any controller's Disconnect.
    for node in nodes:
        for name in ('active', 'syncfile', 'loadonstart'):
            try:
                par = getattr(node.par, name, None)
                if par is not None: par.val = False
            except Exception as exc:
                errors.append(f'{node.path}.{name}: {exc}')
    for node in nodes:
        try:
            if not node.isCOMP:
                continue
            # The source class identifier selects controller objects, not owners.
            # Direct local inventory distinguishes absence from a broken lookup.
            local = [ext for ext in node.extensions
                     if ext is not None and type(ext).__name__ == 'RotoPythonExt']
            if not local:
                continue
            extension = node.ext.RotoPythonExt  # no default swallowing AttributeError
            if not any(extension is ext for ext in local):
                raise RuntimeError('Controller extension is not attached locally')
            # Named ext searches parents; ownership requires the actual handle.
            if extension.ownerComp != node:
                raise RuntimeError('Controller extension owner does not match local COMP')
            node.Disconnect()
            host = extension._host
            host.enabled = host.connected = host.plugin = False
        except Exception as exc:
            errors.append(f'{node.path} disconnect: {exc}')
    return errors


def _checkpoint(holder):
    return dict(result=copy.deepcopy(holder.fetch('result', {})),
                paths=list(holder.fetch('temp_paths', [])))


def _capture(holder, checkpoint, stage, error=None, evidence_path=None):
    r = copy.deepcopy(checkpoint['result'])
    r.update(stage=stage, artifacts=_artifacts(checkpoint['paths']))
    r['artifact_capture_errors'] = [item['path'] for item in r['artifacts']
                                    if not item['exists'] or 'sha256' not in item
                                    or 'size' not in item]
    if r['artifact_capture_errors']:
        r['native_fixture_pass'] = False
    if error is not None:
        r.update(native_fixture_pass=False, failure=str(error),
                 failure_type=type(error).__name__)
    if holder is not None and holder.valid:
        r['holder_path'] = holder.path
        try:
            r['native_errors_before_quiesce'] = str(holder.errors(recurse=True))
        except Exception as exc:
            r['native_errors_capture_error'] = str(exc)
        r['quiesce_errors'] = _quiesce(holder)
        if r['quiesce_errors']:
            r['native_fixture_pass'] = False
    directory = Path(r['artifact_dir'])
    path = Path(evidence_path) if evidence_path else directory/(stage+'-'+uuid.uuid4().hex+'.json')
    # Do not overwrite earlier verification/recovery evidence.
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(r, indent=2)+'\n')
    if holder is not None and holder.valid:
        holder.store('last_evidence', str(path))
    return r


def capture_failure(holder, stage, error):
    """Capture errors/artifact hashes and quiesce; executor inspects before cleanup."""
    return _capture(holder, _checkpoint(holder), stage, error)


def _preserve_failure(function):
    @wraps(function)
    def guarded(holder, *args, **kwargs):
        try:
            return function(holder, *args, **kwargs)
        except Exception as exc:
            try:
                capture_failure(holder, function.__name__, exc)
            except Exception as capture_error:
                # Even evidence I/O failure must not destroy the failed fixture.
                if hasattr(exc, 'add_note'):
                    exc.add_note(f'Failure evidence capture also failed: {capture_error}')
            raise
    return guarded


def _controller(holder):
    if not holder.fetch('action_fixture', False):
        raise ValueError('Pass the holder returned by build_fixture')
    c = holder.op('roto_python')
    if c.ext.RotoPythonExt._process is not None:
        raise ValueError('Fixture unexpectedly owns a MIDI process; stop verification')
    return c, c.ext.RotoPythonExt


def _ack(controller):
    e = controller.ext.RotoPythonExt
    p = controller.op('protocol').module
    for key, target in list(e._host.controls.items()):
        e._receive_midi(p.sysex(11, 11, (target.index>>7, target.index&127,
                        *p.digest(target.target_id, 6), int(key[0]=='button'), key[1]-1, 0)))


def _verify_owner_entry(controller, extension, consumer, layout_id):
    """Observe RegisterComp's qualified entry; never rewrite the owner link."""
    context = controller.GetLayoutContext()
    assert context['category'] == 'COMP' and context['layout_id'] == layout_id
    owner = context['owner']
    assert owner['state'] == 'bound' and not context['quarantined']
    assert context['plugin_id'] == owner['entry_plugin_id']
    link = extension._layouts.plugin(*context['key'])['focus_comp']
    assert link['state'] == 'bound' and link['owner_id'] == owner['id']
    assert link['path'] == owner['path']
    assert extension._layouts.owner_handles[owner['id']] is consumer
    assert extension._follow.handles[owner['entry_plugin_id']] is consumer


def _configure_toggle(controller, tool, mapping_id):
    """Fixture-local fresh LEARN/offer/ACK before testing the changed RX adapter."""
    e = controller.ext.RotoPythonExt
    p = controller.op('protocol').module
    before = tool.par.Recalls.eval()
    controller.ConfigureControl(mapping_id, button_type='toggle')
    assert tool.par.Recalls.eval() == before
    # TYPE is a local adapter in the current runtime, not new wire metadata.
    # Still explicitly refresh matching ACK/reset latch for this fixture stage.
    e._receive_midi(p.sysex(11, 9, (1,)))
    assert controller.Offerparameter(mapping_id)
    _ack(controller)
    state = controller.GetControlState(mapping_id)
    assert state['mapped'] and state['button_type'] == 'toggle'
    e._receive_midi((191, 20, 127))  # LEARN must suppress action even after ACK.
    assert tool.par.Recalls.eval() == before
    e._receive_midi(p.sysex(11, 9, (0,)))
    assert tool.par.Recalls.eval() == before


def build_fixture(parent_comp, source_dir, python_path):
    source = Path(source_dir).resolve()
    python_path = Path(python_path).absolute()
    if not python_path.is_file():
        raise FileNotFoundError(python_path)
    if parent_comp is None or not parent_comp.isCOMP or parent_comp.op(HOLDER) is not None:
        raise ValueError('Pass an explicit test parent without an existing fixture')
    # Build from source rather than copying user mappings or a stale tox.
    ns = dict(globals())
    path = source/'build_network.py'
    exec(compile(path.read_text(), str(path), 'exec'), ns)
    h = parent_comp.create(baseCOMP, HOLDER)
    h.viewer = h.display = True
    h.store('action_fixture', True)
    directory = tempfile.mkdtemp(prefix='roto-actions-evidence-')
    h.store('temp_paths', [])
    h.store('result', dict(fixture_id=uuid.uuid4().hex, artifact_dir=directory,
                           physical_acceptance=False, comp_ownership_acceptance=False,
                           source=str(source)))
    try:
        c = ns['build'](h, source)
        c.Disconnect()
        c.par.Python = str(python_path)
        c.par.Followcomp = False
        e = c.ext.RotoPythonExt
        c.storage.clear(); e._layouts = None
        e.BindControls([], group_id='native.action.empty', _allow_empty=True)
        e._layout_ready = True
        c.store('layout_registry', None); e._layouts = None; e._layout_manager()
        consumer = h.create(baseCOMP, 'consumer')
        consumer.viewer = consumer.display = True
        consumer.nodeX, consumer.nodeY = 400, 0
        page = consumer.appendCustomPage('Preset')
        amount = page.appendFloat('Amount')[0]
        amount.min = amount.normMin = 0; amount.max = amount.normMax = 1
        amount.clampMin = amount.clampMax = True; amount.val = .4
        page.appendInt('Recalls')[0].val = 0
        page.appendPulse('Reset')
        dat = consumer.create(textDAT, 'presets')
        dat.par.language = 'python'
        dat.text = '''def recall(event):
    tool = me.parent()
    tool.par.Recalls += 1
    tool.par.Amount = .6
    if tool.fetch('fail', False):
        return dict(status='partial', error='fixture partial failure',
                    entries=[dict(target_key='amount', attempted=True, actual_value=tool.par.Amount.eval())])
    return dict(status='success', entries=[dict(target_key='amount', actual_value=tool.par.Amount.eval())])
'''
        c.op('registration').text = '''def onRegisterActions(controller):
    tool = controller.parent().op('consumer')
    def recall(event):
        if tool is None or not tool.valid:
            return dict(status='unavailable', error='Fixture consumer missing')
        return tool.op('presets').module.recall(event)
    controller.RegisterAction('native.clean.v1', 'Clean', recall)
'''
        assert c.Applybinding() is not False
        c.AssignParameter('knob', 1, amount, _id='native.custom.amount')
        c.AssignAction(1, 'native.clean.v1', id='native.custom.action')
        e._layouts.capture(force=True)
        b = c.RegisterComp(consumer)
        c.SelectLayout(b)
        _verify_owner_entry(c, e, consumer, b)
        c.AssignParameter('knob', 1, amount, _id='native.linked.amount')
        c.ConfigureControl('native.linked.amount', minimum=.2, maximum=.8)
        c.AssignAction(1, 'native.clean.v1', id='native.linked.action')
        e._layouts.capture(force=True)
        c.SelectLayout('custom')
        result = h.fetch('result')
        result.update(native_build=str(app.build), linked_layout=b,
                      qualified_owner_entry_verified=True,
                      baseline_count=consumer.par.Recalls.eval())
        h.store('result', result)
        h.store('definitions', {p['id']:copy.deepcopy(p['targets']) for p in e._layouts.all_plugins()})
        h.store('temp_paths', [])
        return h
    except Exception as exc:
        try:
            capture_failure(h, 'build_fixture', exc)
        except Exception as capture_error:
            if hasattr(exc, 'add_note'):
                exc.add_note(f'Failure evidence capture also failed: {capture_error}')
        raise


@_preserve_failure
def exercise(holder):
    c, e = _controller(holder)
    r = holder.fetch('result'); tool = holder.op('consumer'); p = c.op('protocol').module
    sent = []
    e._host.send = lambda message: sent.append(list(message))
    e._host.connected = e._host.plugin = True
    e._receive_midi(p.sysex(11, 9, (1,)))
    assert c.Offerparameter('native.custom.action')
    _ack(c)
    e._receive_midi((191, 20, 127))
    assert tool.par.Recalls.eval() == r['baseline_count']
    e._receive_midi(p.sysex(11, 9, (0,)))
    for value in (127, 127, 0, 0, 127, 0): e._receive_midi((191, 20, value))
    assert tool.par.Recalls.eval() == r['baseline_count']+2
    assert c.GetValue('native.custom.amount') == tool.par.Amount.eval() == .6
    assert c.GetControlState('native.custom.action')['action_result']['status'] == 'succeeded'
    assert any(msg[:2]==[191, 12] for msg in sent)  # true parameter feedback
    before = tool.par.Recalls.eval()
    stale = (e._follow.token[0], e._follow.token[1]-1)
    e._receive_midi((191, 20, 127), token=stale)
    assert tool.par.Recalls.eval() == before
    c.SelectLayout(r['linked_layout']); _ack(c)
    assert tool.par.Recalls.eval() == before
    assert c.GetValue('native.linked.amount') == .6
    _configure_toggle(c, tool, 'native.linked.action')
    assert tool.par.Recalls.eval() == before
    clock = [0.0]; e._host.clock = lambda: clock[0]
    for value in (127, 0, 127):
        e._receive_midi((191, 20, value)); clock[0] += .1
    assert tool.par.Recalls.eval() == before+3
    tool.store('fail', True)
    e._receive_midi((191, 20, 0))
    state = c.GetControlState('native.linked.action')
    assert not state['valid'] and state['action_result']['status']=='partial'
    assert state['action_result']['entries'][0]['actual_value'] == .6
    assert e._host.connected and e._host.plugin and e._host.enabled
    e._receive_midi((191, 12, 127)); e._receive_midi((191, 44, 127))
    assert abs(tool.par.Amount.eval()-.8)<1e-9
    tool.store('fail', False)
    c.AssignAction(1, 'native.clean.v1', id='native.linked.action')
    _ack(c)
    c.SelectLayout('custom'); _ack(c)
    assert abs(c.GetValue('native.custom.amount')-.8)<1e-9
    # Local adapter override is expected; core assignment definitions stay intact.
    assert {p['id']:p['targets'] for p in e._layouts.all_plugins()} == holder.fetch('definitions')
    e.UnregisterAction('native.clean.v1')
    assert not c.GetControlState('native.custom.action')['action_available']
    e._receive_midi((191, 20, 127))
    assert c.GetActionState('native.clean.v1')['result']['status']=='unavailable'
    c.Disconnect(); assert c.Applybinding() is not False
    assert c.GetControlState('native.custom.action')['valid']
    r.update(learn_ack_zero_recall=True, push_once=True, toggle_latched=True,
             toggle_fresh_ack_zero_recall=True,
             stale_input_fenced=True, partial_isolated=True, true_par_feedback=True,
             independent_definitions=True, real_comp_custom_fixture=True, unavailable_and_reconstruction=True,
             count_before_reload=tool.par.Recalls.eval())
    holder.store('result', r)
    return 'exercise passed; wait one frame, then save_reload'


def save_reload(holder):
    checkpoint = _checkpoint(holder)
    live_holder = holder
    try:
        c, e = _controller(holder)
        assert not c.errors(recurse=True)
        c.Disconnect(); e._follow.refresh_links(); e._layouts.capture(force=True)
        path = Path(checkpoint['result']['artifact_dir'])/('reload-'+uuid.uuid4().hex+'.tox')
        holder.store('temp_paths', holder.fetch('temp_paths')+[str(path)])
        checkpoint = _checkpoint(holder)
        parent_comp = holder.parent()
        holder.save(str(path))  # actual native serialization, never binary editing
        serialized = _capture(None, checkpoint, 'serialized_before_reload')
        assert not serialized['artifact_capture_errors'], 'Retain holder until saved copy is hashed'
        holder.destroy()  # required serialization/reload test; disk copy is retained
        live_holder = None
        loaded = parent_comp.loadTox(str(path))
        live_holder = loaded
        loaded.name = HOLDER
        return loaded
    except Exception as exc:
        try:
            _capture(live_holder, checkpoint, 'save_reload', exc)
        except Exception as capture_error:
            if hasattr(exc, 'add_note'):
                exc.add_note(f'Failure evidence capture also failed: {capture_error}')
        raise


@_preserve_failure
def finish(holder, evidence_path):
    c, e = _controller(holder); r = holder.fetch('result')
    assert c.Applybinding() is not False
    assert not e._host.connected and e._process is None
    assert holder.op('consumer').par.Recalls.eval() == r['count_before_reload']
    assert c.GetActionState('native.clean.v1')['available']
    assert {p['id']:p['targets'] for p in e._layouts.all_plugins()} == holder.fetch('definitions')
    assert not c.errors(recurse=True)
    ns = dict(globals()); source = Path(r['source']); path = source/'export_component.py'
    exec(compile(path.read_text(), str(path), 'exec'), ns)
    generic_path = Path(r['artifact_dir'])/('generic-'+uuid.uuid4().hex+'.tox')
    holder.store('temp_paths', holder.fetch('temp_paths')+[str(generic_path)])
    ns['export'](c, generic_path)
    generic = holder.loadTox(str(generic_path))
    assert generic.Applybinding() is not False
    assert generic.GetActions() == [] and generic.GetControlStates() == []
    assert not generic.ext.RotoPythonExt._host.connected and generic.ext.RotoPythonExt._process is None
    assert not generic.par.Followcomp.eval() and not generic.par.Focuscomp.eval()
    assert all(not p['targets'] and not p['state'].get('page_targets')
               for p in generic.ext.RotoPythonExt._layouts.all_plugins())
    assert not generic.errors(recurse=True)
    r.update(actual_tox_reload_zero_recall=True, generic_export_empty=True,
             errors='', native_fixture_pass=True)
    holder.store('result', r)
    # Capture success before optional executor cleanup; leave generic/holder inspectable.
    captured = _capture(holder, _checkpoint(holder), 'finish', evidence_path=evidence_path)
    assert not captured['artifact_capture_errors'], 'Retain fixture for artifact recovery'
    assert not captured['quiesce_errors'], 'Retain fixture for quiesce recovery'
    return captured


def cleanup(holder):
    """Explicit executor node cleanup after evidence; NEVER delete disk artifacts."""
    if not holder.fetch('action_fixture', False):
        raise ValueError('Only the explicit Action fixture can be cleaned up')
    evidence = Path(holder.fetch('last_evidence', ''))
    if not evidence.is_file():
        raise ValueError('Capture evidence before fixture cleanup')
    record = json.loads(evidence.read_text(encoding='utf-8'))
    if record.get('fixture_id') != holder.fetch('result', {}).get('fixture_id'):
        raise ValueError('Evidence belongs to a different fixture')
    r = _capture(holder, _checkpoint(holder), 'executor_cleanup')
    if r['quiesce_errors'] or r['artifact_capture_errors']:
        raise RuntimeError('Fixture evidence/quiesce incomplete; retain holder for recovery')
    holder.destroy()
    return r
