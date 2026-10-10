"""Prepared native stages; NOT executed evidence and never opens MIDI.

The Inspector sole executor supplies an explicitly marked disposable fixture,
an empty controller built from the immutable candidate, and two external COMPs
with Amount (Float, range 0..10) / Reset (Pulse). pulse_count reads a native Pulse
observer installed by that executor. Run stages across native frames.
"""
from pathlib import Path
import copy


def _fixture(controller):
    root = controller.parent(); e = controller.ext.RotoPythonExt
    if root.fetch('issue10_disposable_fixture',False,search=False) is not True:
        raise ValueError('Only an explicitly marked disposable fixture is allowed')
    if e._process is not None or e._host.connected or e._host.plugin:
        raise ValueError('Fixture must have no MIDI process or connected session')
    return root,e,e._layout_manager(),e._follow


def _select(root,comp):
    pane = ui.panes.current
    if str(pane.type).split('.')[-1] != 'NETWORKEDITOR':
        raise ValueError('Use a real Network Editor pane in the isolated project')
    pane.owner = root
    for child in root.children: child.selected = child is comp
    return pane


def prepare(controller,a,b,source_dir,pulse_count):
    root,e,m,f = _fixture(controller)
    if a.parent() != root or b.parent() != root or a is b:
        raise ValueError('Supply two external fixture COMPs under the same root')
    if controller.par.Followcomp.eval() or any(p['targets'] or p['state'].get('page_targets') for p in m.all_plugins()):
        raise ValueError('Use a fresh empty disconnected controller with Follow off')
    for name in ('text_comp_follow','layouts','RotoPythonExt','free_learn'):
        expected = Path(source_dir)/'code/py/roto_python'/(name+'.py')
        assert controller.op(name).text.replace('\r\n','\n') == expected.read_text().replace('\r\n','\n'),name
    if any(comp.par.Amount.style != 'Float' or comp.par.Reset.style != 'Pulse' for comp in (a,b)):
        raise ValueError('Fixture needs native Float Amount and Pulse Reset')
    pane = ui.panes.current
    root.store('issue10_pane_baseline',dict(id=pane.id,owner=pane.owner,
        selected=list(pane.owner.selectedChildren)))
    la = e.RegisterComp(a); lb = e.RegisterComp(b)
    e.SelectLayout(la); aid = e.AssignParameter('knob',1,a.par.Amount)['id']
    e.AssignParameter('button',1,a.par.Reset,button_type='push')
    e.SelectLayout(lb); bid = e.AssignParameter('knob',1,b.par.Amount)['id']
    track = m.track(lb)['id']; variant = e.CreatePlugin(lb,track,'Variant')
    e.SetPluginComp(lb,track,variant,b); e.SelectPlugin(lb,track,variant)
    variant_id = e.AssignParameter('knob',2,b.par.Amount)['id']
    e.SelectLayout(la)
    _select(root,a); controller.par.Followcomp = True
    f.invalidate(); f.observe(force=True); f.flush()
    result = dict(evidence_class='prepared-native-follow',executed=False,physical=False,
        layout_a=la,layout_b=lb,variant=variant,target_ids=[aid,bid,variant_id],
        values=[a.par.Amount.eval(),b.par.Amount.eval()],pulses=pulse_count(),
        registry=copy.deepcopy(e.GetLayoutRegistry()))
    root.store('issue10_follow_result',result)
    return result


def selection(controller,a,b,pulse_count):
    root,e,m,f = _fixture(controller); r = root.fetch('issue10_follow_result',None,search=False)
    if r is None: raise ValueError('Prepare on a preceding native frame')
    _select(root,b); f.observe(force=True)
    assert f.pending['layout_id'] == r['layout_b'] and f.gated
    f.flush()
    assert m.context()['key'] == (r['layout_b'],m.track()['id'],r['variant'])
    assert e.GetCompContext()['pending_layout_id'] is None
    assert not e.GetControlState(r['target_ids'][2])['mapped']
    e.GetPluginTargets(r['layout_a'])  # browse/read does not activate
    assert m.data['active'] == r['layout_b']
    _select(root,a); f.observe(force=True); f.flush()
    assert m.data['active'] == r['layout_a']
    before = e.GetLayoutRegistry()
    f.observe(force=True); f.flush(); f.observe(force=True); f.flush()
    assert e.GetLayoutRegistry() == before
    assert [a.par.Amount.eval(),b.par.Amount.eval()] == r['values']
    assert pulse_count() == r['pulses']
    for layout_id in (r['layout_a'],r['layout_b']):
        before_layout = next(l for l in r['registry']['records'] if l['id'] == layout_id)
        for old_track in before_layout['tracks']:
            for old in old_track['plugins']:
                current = m.plugin(layout_id,old_track['id'],old['id'])
                for key in ('id','group_id','device_id','targets'):
                    assert current[key] == old[key],key
                assert current['state']['page_targets'] == old['state']['page_targets']
    r.update(executed=True,evidence_class='native-offline-follow',a_b_a=True,
        variant_recall=True,target_values_unchanged=True,pulse_count_unchanged=True,
        value_write_observation='pending separate native observer gate',physical=False)
    root.store('issue10_follow_result',r)
    return copy.deepcopy(r)


def guarded(controller,a,b):
    root,e,m,f = _fixture(controller); r = root.fetch('issue10_follow_result',None,search=False)
    _select(root,b); m.locked = True
    try:
        f.observe(force=True); f.flush()
        assert m.data['active'] == r['layout_a'] and f.pending['layout_id'] == r['layout_b']
        assert not f.gated  # LOCK retains the stable original routing until unlock
        m.locked = False; m.touched.add(52); f.unlocked(); f.flush()
        assert f.gated and m.data['active'] == r['layout_a']
        m.touched.clear(); f.flush()
        assert m.data['active'] == r['layout_b']
    finally:
        m.locked = False; m.touched.clear()
    _select(root,a); f.observe(force=True); f.flush()
    r.update(native_guard_state=True,physical=False)
    root.store('issue10_follow_result',r)
    return copy.deepcopy(r)


def finish(controller):
    root,e,m,f = _fixture(controller)
    controller.par.Followcomp = False; f.observe(force=True); f.flush()
    baseline = root.fetch('issue10_pane_baseline',None,search=False)
    if baseline:
        pane = next((p for p in ui.panes if p.id == baseline['id']),None)
        if pane is not None and baseline['owner'].valid:
            pane.owner = baseline['owner']
            for child in pane.owner.children:
                child.selected = child in baseline['selected']
    return dict(physical=False,process=e._process,pending=copy.deepcopy(f.pending),
        remaining=['native synthetic RX/failure stages','native save/reload',
                   'Inspector LIVE/BROWSE','coordinated physical Follow guards/input/motor/LCD'])
