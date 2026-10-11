"""Isolated #4 native state-transition checks; no physical MIDI connection."""
from pathlib import Path
import json


def verify(td, source_dir):
    source = Path(source_dir)
    root = td['op']('/')
    name = 'base_issue4_verification'
    assert root.op(name) is None
    main = td['op']('/roto_clean_demo/roto_python')
    pid = main.ext.RotoPythonExt._process.pid
    h = root.create(td['baseCOMP'], name)
    h.viewer = True; h.nodeX = 3000; h.nodeY = -1700
    c = None
    try:
        ns = dict(td); path = source/'scripts/build_network.py'
        exec(compile(path.read_text(), str(path), 'exec'), ns)
        c = ns['build'](h, source)
        e = c.ext.RotoPythonExt
        target = h.create(td['baseCOMP'], 'base_targets_test')
        target.viewer = True; target.nodeX = 0; target.nodeY = -700
        par = target.appendCustomPage('Test').appendFloat('Value')[0]
        par.normMin = 0; par.normMax = 1; par.val = .25
        layout = e.CreateLayout('Transition test'); e.SelectLayout(layout)
        track = e.GetTracks()[0]['id']; pa = e.GetPlugins()[0]['id']
        e.AssignParameter('knob', 1, par)
        pb = e.CreatePlugin(layout, track, 'Second')
        other = e.CreateTrack(layout, 'Other')
        f = e._follow; m = e._layouts; proto = c.op('protocol').module
        def ready():
            e._host.send = lambda message: None
            e._host.enabled = e._host.connected = e._host.plugin = True
        def ack():
            for ctrl in e._host.controls.values():
                e._receive_midi(proto.sysex(11,11,(ctrl.index>>7,ctrl.index&127,
                    *proto.digest(ctrl.target_id,6),int(ctrl.key[0]=='button'),ctrl.key[1]-1,0)))
        ready(); ack()
        for first, second in ((12,44),(44,12)):
            before = par.eval()
            e._receive_midi((191,first,64))
            e._receive_midi(proto.sysex(11,9,(1,)))
            e._receive_midi(proto.sysex(11,9,(0,)))
            e._receive_midi((191,second,0))
            assert par.eval() == before
        for split in (False, True):
            e.SelectPlugin(layout,track,pa);ready();ack()
            e._receive_midi(proto.sysex(11,13,(1,)))
            e._receive_midi(proto.sysex(10,9,(0,1)))
            e._receive_midi(proto.sysex(11,7,(1,)))
            if split:
                f.flush()
                assert m.track()['id']==track and m.plugin()['id']==pb and m.selected_track==other
            e._receive_midi(proto.sysex(11,13,(0,)))
            f.flush()
            assert m.track()['id']==other and m.selected_track==other
            assert f.pending is None
        assert not c.errors(recurse=True)
        assert e._process is None
        assert main.ext.RotoPythonExt._process.pid == pid
        return dict(native_build=str(td['app'].build),
                    partial_pairs_discarded=True,both_half_directions=True,
                    same_batch_unlock=True,split_batch_unlock=True,
                    locked_device_selection_retained=True,
                    main_midi_pid_preserved=True,physical_acceptance=False)
    finally:
        if c is not None: c.Disconnect()
        h.destroy()
