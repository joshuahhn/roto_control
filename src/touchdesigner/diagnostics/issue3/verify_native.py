"""Issue #3 native checks, isolated fixture only; no hardware transport."""
import copy
import json
from pathlib import Path


def verify(c, baseCOMP):
    e = c.ext.RotoPythonExt
    assert e._process is None
    target = c.parent().create(baseCOMP, 'base_identity_targets')
    target.viewer = True; target.nodeX = 0; target.nodeY = -700
    page = target.appendCustomPage('Test')
    a = page.appendFloat('Alpha')[0]; b = page.appendFloat('Beta')[0]
    for p in (a, b):
        p.normMin = 0; p.normMax = 10; p.val = 5
    e.AssignParameter('knob', 3, a)
    e.AssignParameter('knob', 3, b)
    assert e._collection.bindings['knob', 3].parameter.name == 'Beta'
    proto = c.op('protocol').module
    e._host.send = lambda message: None
    e._host.enabled = e._host.connected = e._host.plugin = e._host.learning = True
    learner = e._free_learner; learner.active = True
    assert learner.offer(a)
    assert learner.pending['parameter'].name == 'Alpha'
    def packet():
        t = learner.pending['template']
        return proto.sysex(11, 11, (t.index >> 7, t.index & 127, *proto.digest(t.target_id, 6), 0, 2, 0))
    ack = packet(); a.normMax = 20
    original = e._collection.bindings['knob', 3]
    assignments = copy.deepcopy(c.fetch('parameter_assignments'))
    assert learner.receive(ack)
    assert e._collection.bindings['knob', 3] is original
    assert c.fetch('parameter_assignments') == assignments
    a.normMax = 10
    assert learner.offer(a); ack = packet()
    watcher = c.op('base_targets/watch_knob3')
    watcher_before = (watcher.par.active.eval(), watcher.par.op.expr, watcher.par.pars.eval())
    registry = copy.deepcopy(e._layouts.data)
    library = copy.deepcopy(c.fetch('page_targets', []))
    table = c.op('base_targets/targets').text
    publish = e._publish
    calls = [0]
    def fail_once():
        calls[0] += 1
        if calls[0] == 1:
            raise RuntimeError('native late commit failure')
        return publish()
    e._publish = fail_once
    try:
        assert learner.receive(ack)
    finally:
        e._publish = publish
    assert e._collection.bindings['knob', 3] is original
    assert c.fetch('parameter_assignments') == assignments
    assert (watcher.par.active.eval(), watcher.par.op.expr, watcher.par.pars.eval()) == watcher_before
    assert c.op('base_targets/targets').text == table
    assert c.fetch('page_targets', []) == library
    assert e._layouts.data == registry
    assert not e._host.controls['knob', 3].mapped
    assert learner.offer(a); ack = packet()
    assert not learner.receive(ack); e._host.receive(ack)
    assert e._collection.bindings['knob', 3].parameter.name == 'Alpha'
    assert e.GetControlState(e._collection.bindings['knob', 3].id)['mapped']
    e._host.learning = False; learner.active = False; e.Disconnect()
    return dict(native_assign_identity=True, native_free_learn_identity=True,
                range_drift_preserved=True, late_failure_rollback=True,
                native_watcher_restored=True, table_and_library_restored=True,
                subsequent_ack_success=True, physical_acceptance=False)
