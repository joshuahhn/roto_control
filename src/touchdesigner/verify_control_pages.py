"""Disconnected native regression for two pages sharing Knob 1."""
from pathlib import Path
import copy
import json
import tempfile


def begin(controller):
    root=controller.parent()
    if root.op('base_control_pages_test') is not None:raise ValueError('Existing page test fixture')
    h=root.create(baseCOMP,'base_control_pages_test');h.viewer=True;h.nodeX=2400;h.nodeY=-1200
    t=h.create(baseCOMP,'target');t.viewer=True;t.nodeX=220;t.nodeY=0
    page=t.appendCustomPage('Test')
    page.appendFloat('First')[0].val=.2;page.appendFloat('Second')[0].val=.8
    c=h.copy(controller,name='controller');c.viewer=True;c.nodeX=0;c.nodeY=0;c.Disconnect()
    return h.path


def exercise(controller):
    h=controller.parent().op('base_control_pages_test');c=h.op('controller');t=h.op('target');e=c.ext.RotoPythonExt
    e.Applybinding();layout=c.CreateLayout('Page regression');c.SelectLayout(layout)
    m=e._layouts;proto=c.op('protocol').module
    def rx(packet):
        if not m.receive(packet):e._host.receive(packet)
        m.acknowledge();e._publish()
    def ack(target):
        return proto.sysex(11,11,(target['index']>>7,target['index']&127,*proto.digest(target['identity'],6),0,0,0))
    e._host.connected=e._host.plugin=True
    c.AssignParameter('knob',1,t.par.First,_wire_index=128,_hardware_mapped=True)
    first=copy.deepcopy(m.record()['targets'][0]);rx(ack(first))
    rx(proto.sysex(10,21));assert not c.GetControlStates()
    c.AssignParameter('knob',1,t.par.Second,_wire_index=129,_hardware_mapped=True)
    second=copy.deepcopy(m.record()['targets'][0]);rx(ack(second))
    for target,parameter,arrow in ((first,'First',20),(second,'Second',21),(first,'First',20)):
        rx(proto.sysex(10,arrow));rx(ack(target))
        assert c.GetControlState()['parameter']==parameter and c.GetControlState()['mapped']
    assert len(c.fetch('page_targets'))==2
    before=t.par.Second.eval();e._host.receive((191,12,64));e._host.receive((191,44,0))
    assert abs(t.par.First.eval()-8192/16383)<.0001 and t.par.Second.eval()==before
    rx(proto.sysex(10,21));assert not c.GetControlStates()
    e._host.receive((191,12,127));e._host.receive((191,44,127));assert t.par.Second.eval()==before
    e.Disconnect()
    h.store('first',first);h.store('second',second);h.store('layout',layout)
    path=Path(tempfile.gettempdir())/'roto_control_pages_fixture.tox'
    if path.exists():raise FileExistsError(path)
    c.save(str(path));c.destroy();c=h.loadTox(str(path));c.name='controller';h.store('temp_path',str(path))
    return 'A/B/A and empty-page input passed; actual tox reloaded for next stage'


def finish(controller):
    h=controller.parent().op('base_control_pages_test');c=h.op('controller');c.Applybinding()
    e=c.ext.RotoPythonExt;m=e._layouts;proto=c.op('protocol').module
    assert len(c.fetch('page_targets'))==2
    e._host.connected=e._host.plugin=True
    target=h.fetch('first');packet=proto.sysex(11,11,(target['index']>>7,target['index']&127,*proto.digest(target['identity'],6),0,0,0))
    if not m.receive(packet):e._host.receive(packet)
    m.acknowledge();e._publish()
    assert c.GetControlState()['parameter']=='First' and c.GetControlState()['mapped']
    assert not c.errors(recurse=True),c.errors(recurse=True)
    assert e._process is None
    result=dict(native_page_recall=True,native_empty_page_input_blocked=True,independent_target_writes=True,
                tox_reload_retains_offpage_targets=True,errors='',physical_acceptance=False)
    e.Disconnect();Path(h.fetch('temp_path')).unlink();h.destroy()
    Path(project.folder,'control_pages_native_verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
