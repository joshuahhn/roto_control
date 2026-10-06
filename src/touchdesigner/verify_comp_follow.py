"""Native disconnected fixture. Run stages across frames; never opens MIDI ports.

Uses the actual current Network Editor and native Parameter Execute callbacks.
Only temporary COMPs/parameters are changed. finish restores the user's pane.
"""
from pathlib import Path
import copy
import json
import tempfile

HOLDER = 'base_comp_follow_verification'


def fixture(controller):
    holder = controller.parent().op(HOLDER)
    c = holder.op('controller')
    return holder, c, c.ext.RotoPythonExt, holder.fetch('result')


def select(holder, *nodes, current=None):
    for node in holder.children:
        node.selected = False
    if current is not None:
        current.current = True
    for node in nodes:
        node.selected = True
    return dict(selected=[n.name for n in holder.selectedChildren],
                current=holder.currentChild.name if holder.currentChild else None)


def begin(controller):
    root = controller.parent()
    if root.op(HOLDER):
        raise ValueError('Existing fixture')
    holder = root.create(baseCOMP, HOLDER)
    holder.nodeX, holder.nodeY = 2400, -1500
    pane = ui.panes.current
    holder.store('pane', dict(id=pane.id, owner=pane.owner.path,
                 selected=[n.path for n in pane.owner.selectedChildren],
                 current=pane.owner.currentChild.path if pane.owner.currentChild else None))
    c = holder.copy(controller, name='controller')
    c.Disconnect(); c.Applybinding()
    for name, value, x in (('a', .25, 220), ('b', .75, 440)):
        target = holder.create(baseCOMP, name)
        target.nodeX, target.nodeY = x, 0
        page = target.appendCustomPage('Test')
        par = page.appendFloat('Speed')[0]
        par.normMin = par.min = 0; par.normMax = par.max = 1
        par.clampMin = par.clampMax = True; par.val = value
        page.appendPulse('Reset')
        watcher = target.create(parameterexecuteDAT, 'reset_observer')
        watcher.par.op = '..'; watcher.par.pars = 'Reset'
        watcher.par.builtin = False; watcher.par.custom = True; watcher.par.onpulse = True
        watcher.par.language = 'python'
        watcher.text = 'def onPulse(par):\n    par.owner.store("pulses", par.owner.fetch("pulses",0)+1)\n'
    holder.create(nullTOP, 'other_family').nodeX = 660
    e = c.ext.RotoPythonExt
    layout = e.CreateLayout('Focus verification'); e.SelectLayout(layout)
    a = e.GetTracks()[0]['id']; e.RenameTrack(layout, a, 'A')
    aid = e.AssignParameter('knob', 1, holder.op('a').par.Speed)['id']
    e.AssignParameter('button', 1, holder.op('a').par.Reset, button_type='push')
    b = e.CreateTrack(layout, 'B'); e.SelectTrack(layout, b)
    bid = e.AssignParameter('knob', 1, holder.op('b').par.Speed)['id']
    e.SelectTrack(layout, a)
    e.SetTrackComp(layout, a, holder.op('a')); e.SetTrackComp(layout, b, holder.op('b'))
    assert not c.par.Followcomp.eval()
    pane.owner = holder; select(holder, holder.op('a'), current=holder.op('a'))
    c.par.Followcomp = True
    holder.store('result', dict(layout=layout, a=a, b=b, aid=aid, bid=bid,
                 physical_acceptance=False, selection_samples=[], native_api=True))
    return 'Fixture ready; run selection next frame'


def selection(controller):
    h, c, e, r = fixture(controller); f = e._follow
    assert c.GetCompContext()['enabled'] and e.GetLayoutContext()['track_id'] == r['a']
    # A sole selected COMP wins even when currentChild disagrees.
    sample = select(h, h.op('b'), current=h.op('a'))
    r['selection_samples'].append(sample); f.observe(force=True); f.flush()
    assert e.GetLayoutContext()['track_id'] == r['b']
    assert c.par.Focuscomp.eval() == h.op('b')
    assert (h.op('a').par.Speed.eval(), h.op('b').par.Speed.eval()) == (.25, .75)
    for selected in ((), (h.op('a'), h.op('other_family')), (h.op('a'), h.op('b'))):
        sample = select(h, *selected, current=h.op('a'))
        r['selection_samples'].append(sample); f.observe(force=True); f.flush()
        assert e.GetLayoutContext()['track_id'] == r['b']
    select(h, h.op('a')); f.observe(force=True); f.flush()
    assert e.GetLayoutContext()['track_id'] == r['a']
    before = (e._host.tx, e._collection)
    f.observe(force=True); f.flush(); f.observe(force=True); f.flush()
    assert before == (e._host.tx, e._collection)
    # Explicit API guards and duplicate links do not alter saved identities.
    snapshot = copy.deepcopy(e._layouts.data)
    try: e.SetTrackComp(r['layout'], r['b'], h.op('a'))
    except ValueError: pass
    else: raise AssertionError('Duplicate accepted')
    assert snapshot == e._layouts.data
    # Real OP custom parameter change, delivered by native callback next frame.
    c.par.Focuscomp = ''
    r.update(native_selection=True, zero_mixed_multiple=True, no_idle_reinstall=True,
             unchanged_parameter_values=True, duplicate_rejected=True)
    h.store('result', r)
    return 'Selection passed; run midi next frame'


def ack(e, proto):
    for target in list(e._host.controls.values()):
        e._receive_midi(proto.sysex(11, 11, (target.index >> 7, target.index & 127,
            *proto.digest(target.target_id, 6), int(target.key[0] == 'button'), target.key[1]-1, 0)))


def midi(controller):
    h, c, e, r = fixture(controller); f = e._follow; m = e._layouts; p = c.op('protocol').module
    assert m.plugin()['focus_comp'] is None
    c.par.Focuscomp = h.op('a').path
    # Synchronous promoted API restores link before synthetic RX.
    e.SetTrackComp(r['layout'], r['a'], h.op('a'))
    e._host.connected = e._host.plugin = True
    ack(e, p); assert e.GetControlState()['mapped']
    e._pending = b''
    index = [t['id'] for t in m.layout()['tracks']].index(r['b'])
    e._receive_midi(p.sysex(10, 9, (index >> 7, index & 127)))
    for message in ((191, 12, 127), (191, 44, 127), (191, 20, 127), (191, 20, 0)):
        e._receive_midi(message)
    assert f.gated and e._pending == b''
    ack(e, p); assert not e.GetControlState()['mapped']
    f.flush(backlog=True); assert m.track()['id'] == r['a']
    f.flush(); assert m.track()['id'] == r['b']
    assert not e.GetControlState()['mapped']
    ack(e, p); e._receive_midi((191, 12, 64)); e._receive_midi((191, 44, 0))
    assert abs(h.op('b').par.Speed.eval() - 8192/16383) < .00001
    assert h.op('a').par.Speed.eval() == .25
    e.SelectTrack(r['layout'], r['a']); ack(e, p)
    e._receive_midi((191, 20, 127)); e._receive_midi((191, 20, 0))
    # LOCK keeps A usable; unlock fences before input while LEARN/touch guards wait.
    e._receive_midi(p.sysex(11, 13, (1,)))
    e._receive_midi(p.sysex(10, 9, (index >> 7, index & 127)))
    e._receive_midi((191, 12, 32)); e._receive_midi((191, 44, 0))
    locked_value = h.op('a').par.Speed.eval()
    e._receive_midi(p.sysex(11, 12, (1,))); e._receive_midi((191, 52, 127))
    e._receive_midi(p.sysex(11, 13, (0,)))
    for message in ((191, 12, 127), (191, 44, 127), (191, 20, 127), (191, 20, 0)):
        e._receive_midi(message)
    assert h.op('a').par.Speed.eval() == locked_value and f.gated
    f.flush(); assert m.track()['id'] == r['a']
    e._receive_midi(p.sysex(11, 12, (0,))); e._receive_midi((191, 52, 0)); f.flush()
    assert m.track()['id'] == r['b']
    # Retained manager: session cancellation, then new offline Follow.
    m.locked = True; f.request(r['layout'], r['a'], 'hardware'); token = f.token
    e.Disconnect(); assert e._layouts is m and f.pending is None and not m.locked
    e._receive_midi(p.sysex(10, 9, (0, 0)), token); assert f.pending is None
    select(h, h.op('b')); f.observe(force=True)
    select(h, h.op('a')); f.observe(force=True); f.flush()
    assert m.track()['id'] == r['a'] and e._process is None
    r.update(same_batch_backlog_fence=True, fresh_recall_required=True,
             lock_learn_touch_deferral=True, locked_input_preserved=True,
             session_generation=True, disconnected_follow=True)
    h.store('result', r)
    return 'Synthetic RX passed; run persistence next frame'


def persistence(controller):
    h, c, e, r = fixture(controller); f = e._follow
    assert h.op('a').fetch('pulses', 0) == 1
    assert h.op('b').fetch('pulses', 0) == 0
    r['native_pulse_exactly_once_and_fenced'] = True
    h.op('a').name = 'renamed_a'
    f.paused = True
    # Managed component save prepares references synchronously, without Tick.
    c.op('lifecycle_callbacks').module.onProjectPreSave()
    assert e._layouts.plugin(r['layout'], r['a'])['focus_comp']['path'] == '../renamed_a'
    f.paused = False
    before = copy.deepcopy(e._layouts.data)
    ns = dict(globals()); exec(Path(project.folder, 'upgrade_layouts.py').read_text(), ns)
    ns['upgrade'](c, project.folder); e = c.ext.RotoPythonExt; e.Applybinding()
    assert c.par.Followcomp.eval()
    assert e._layouts.plugin(r['layout'], r['a'])['focus_comp'] == before['records'][-1]['tracks'][0]['plugins'][0]['focus_comp']
    select(h, h.op('b')); e._follow.invalidate(); e.Tick()
    assert e.GetLayoutContext()['track_id'] == r['a']  # baseline only
    path = Path(tempfile.gettempdir(), 'roto_comp_follow_native_fixture.tox')
    if path.exists(): raise FileExistsError(path)
    e._follow.refresh_links(); c.save(str(path)); c.destroy()
    c = h.loadTox(str(path)); c.name = 'controller'; h.store('temp_path', str(path))
    r.update(presave_refresh_paused_follower=True, repeated_upgrade_preserves_links=True)
    h.store('result', r)
    return 'Managed tox saved/reloaded; run finish next frame'


def project_presave(controller, destination):
    """After begin settles, test actual pre-save without a Tick or manual hook."""
    h, c, e, r = fixture(controller)
    target = h.op('a'); target.name = 'project_renamed_a'
    # Refresh the active target snapshot, leaving Focus metadata for pre-save.
    e._layouts.capture(force=True)
    assert e._layouts.plugin()['focus_comp']['path'] == '../a'
    e._follow.paused = True
    was_playing = root.time.play
    root.time.play = False
    try:
        project.save(str(destination))
        assert c.fetch('layout_registry')['records'][-1]['tracks'][0]['plugins'][0]['focus_comp']['path'] == '../project_renamed_a'
    finally:
        root.time.play = was_playing
    return dict(project=project.name, folder=project.folder,
                actual_project_presave_callback=True, paused_timeline_immediate_rename_save=True)


def project_reopened(controller):
    """Run after project.load of the project_presave artifact."""
    h, c, e, r = fixture(controller)
    e.Applybinding(); e.Tick()
    assert c.par.Followcomp.eval() and e.GetLayoutContext()['track_id'] == r['a']
    assert e._follow.pending is None and e._process is None
    assert c.par.Focuscomp.eval() == h.op('project_renamed_a')
    assert e.GetControlState()['id'] == r['aid'] and e.GetControlState()['valid']
    r.update(actual_project_presave_callback=True, paused_timeline_immediate_rename_save=True,
             project_reopen_links_and_baseline=True)
    source = Path('/Users/huihongnin/project/roto_control/src/touchdesigner')
    evidence = json.loads((source/'comp_follow_native_verification.json').read_text())
    evidence.update({k:v for k,v in r.items() if k.startswith(('actual_', 'paused_', 'project_'))})
    (source/'comp_follow_native_verification.json').write_text(json.dumps(evidence,indent=2)+'\n')
    saved = h.fetch('pane'); pane = next(p for p in ui.panes if p.id == saved['id'])
    pane.owner = op(saved['owner'])
    for node in pane.owner.children: node.selected = node.path in saved['selected']
    if saved['current']: op(saved['current']).current = True
    e.Disconnect(); h.destroy(); root.time.play = True
    return dict(project_reopen_links_and_baseline=True, valid_target=True, disconnected=True)


def finish(controller):
    h, c, e, r = fixture(controller); e.Applybinding(); e.Tick()
    assert c.par.Followcomp.eval() and e.GetLayoutContext()['track_id'] == r['a']
    assert e.GetControlState()['id'] == r['aid'] and e._process is None
    assert e._follow.pending is None and c.par.Focuscomp.eval() == h.op('renamed_a')
    assert not c.errors(recurse=True), c.errors(recurse=True)
    r.update(tox_reload_baseline_only=True, no_midi_process=True, errors='')
    saved = h.fetch('pane'); pane = next(p for p in ui.panes if p.id == saved['id'])
    pane.owner = op(saved['owner'])
    for node in pane.owner.children: node.selected = node.path in saved['selected']
    current = op(saved['current']) if saved['current'] else None
    if current: current.current = True
    e.Disconnect(); Path(h.fetch('temp_path')).unlink(); h.destroy()
    Path(project.folder, 'comp_follow_native_verification.json').write_text(json.dumps(r, indent=2)+'\n')
    return r
