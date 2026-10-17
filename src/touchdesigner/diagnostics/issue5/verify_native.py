"""Isolated native BIND ownership checks; no physical transport."""
from pathlib import Path


def verify(td, source_dir):
    source = Path(source_dir); root = td['op']('/')
    assert root.op('base_issue5_verification') is None
    main = td['op']('/roto_clean_demo/roto_python')
    pid = main.ext.RotoPythonExt._process.pid
    h = root.create(td['baseCOMP'], 'base_issue5_verification')
    h.viewer=True; h.nodeX=3000; h.nodeY=-1900
    c = None
    try:
        ns=dict(td); path=source/'build/build_network.py'
        exec(compile(path.read_text(),str(path),'exec'),ns)
        c=ns['build'](h,source); e=c.ext.RotoPythonExt
        t=h.create(td['baseCOMP'],'base_aliases');t.viewer=True;t.nodeX=0;t.nodeY=-700
        page=t.appendCustomPage('Test')
        for name in ('Mastera','Masterb','Masterc','Unused','Aliasone','Aliastwo','Aliasthree'):
            par=page.appendFloat(name)[0];par.normMin=0;par.normMax=1;par.val=.5
        aliases=[t.par.Aliasone,t.par.Aliastwo,t.par.Aliasthree]
        for alias, name in zip(aliases,('Mastera','Masterb','Masterc')):
            alias.bindExpr='me.par.'+name; alias.mode=td['ParMode'].BIND
        specs=[dict(kind='knob',slot=i+1,id='alias'+str(i),parameter=alias) for i,alias in enumerate(aliases)]
        e.BindControls(specs,group_id='ownership-native')
        aliases[1].bindExpr='me.par.Mastera'
        try:
            e.SetValue(.8,id='alias1')
            raise AssertionError('shared master write accepted')
        except ValueError as exc:
            assert 'ownership conflict' in str(exc)
        assert t.par.Mastera.eval()==.5
        assert not e.GetControlState('alias0')['valid'] and not e.GetControlState('alias1')['valid']
        e.SetValue(.8,id='alias2');assert abs(t.par.Masterc.eval()-.8)<1e-6
        aliases[1].bindExpr='me.par.Masterb'
        e.BindControls(specs,group_id='ownership-native');e.SetValue(.7,id='alias1')
        assert abs(t.par.Masterb.eval()-.7)<1e-6
        assert aliases[0].bindExpr=='me.par.Mastera' and aliases[1].bindExpr=='me.par.Masterb'
        aliases[1].bindExpr='me.par.Unused';e.SetValue(.9,id='alias1')
        assert abs(t.par.Unused.eval()-.9)<1e-6
        sent=[];e._host.send=sent.append;proto=c.op('protocol').module
        e._host.enabled=e._host.connected=e._host.plugin=True
        for control in e._host.controls.values():
            e._receive_midi(proto.SysExCommand.CONTROL_MAPPED.message((control.index>>7,control.index&127,
                *proto.digest(control.target_id,6),0,control.key[1]-1,0)))
        sent.clear();aliases[1].bindExpr='me.par.Mastera'
        before=t.par.Mastera.eval()
        e._receive_midi((191,13,127));e._receive_midi((191,45,127))
        assert t.par.Mastera.eval()==before and sent==[]
        assert not c.errors(recurse=True)
        assert e._process is None and main.ext.RotoPythonExt._process.pid==pid
        return dict(native_build=str(td['app'].build),shared_master_write_blocked=True,
                    both_controls_suspended=True,unrelated_control_works=True,
                    explicit_reregistration_recovers=True,bind_expressions_preserved=True,
                    unclaimed_master_rebind_allowed=True,hardware_dispatch_no_feedback=True,
                    main_midi_pid_preserved=True,physical_acceptance=False)
    finally:
        if c is not None:c.Disconnect()
        h.destroy()
