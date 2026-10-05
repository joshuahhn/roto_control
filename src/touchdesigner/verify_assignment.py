"""Live TD assignment acceptance without opening MIDI or changing user targets."""
from pathlib import Path
import json


def begin(controller):
    root=controller.parent()
    for name in ('roto_assignment_probe','base_assignment_probe'):
        if root.op(name) is not None:
            raise ValueError('Existing assignment probe: '+name)
    target=root.create(baseCOMP,'base_assignment_probe')
    target.viewer=True;target.nodeX=2200;target.nodeY=-700
    page=target.appendCustomPage('Test')
    speed=page.appendFloat('Speed')[0]
    speed.normMin=0;speed.normMax=10;speed.val=5
    page.appendToggle('Enabled')[0].val=False
    page.appendPulse('Reset')
    fixture=root.copy(controller,name='roto_assignment_probe')
    fixture.viewer=True;fixture.nodeX=2200;fixture.nodeY=-900
    fixture.ext.RotoPythonExt.Disconnect()
    return fixture.path


def exercise(controller):
    root=controller.parent();fixture=root.op('roto_assignment_probe');target=root.op('base_assignment_probe')
    e=fixture.ext.RotoPythonExt
    e.Applybinding()
    assert e._process is None
    inspector=fixture.op('inspector');module=inspector.op('inspector_data').module
    discovered=module.available_components(inspector,'knob')
    assert target in discovered
    proto=fixture.op('protocol').module
    host=e._host;host.send=lambda message:None
    host.start();host.receive(proto.sysex(10,12));host.receive(proto.sysex(11,1,(0,)))
    for key,t in host.controls.items():
        host.receive(proto.sysex(11,11,(0,t.index,*proto.digest(t.target_id,6),int(key[0]=='button'),key[1]-1,0)))
    other=host.controls['knob',8];old=host.controls['knob',2]
    sent=[];host.send=sent.append
    host.receive(proto.sysex(11,9,(1,)))
    assert module.assign(inspector,'knob',2,target.par.Speed)
    state=next(s for s in e.GetControlStates() if s['kind']=='knob' and s['slot']==2)
    assert state['comp']==target.path and not state['mapped']
    assert other is host.controls['knob',8] and other.mapped
    assert len([m for m in sent if m[0]==240 and m[5:7]==(11,10)])==1
    assert not any(m[0]==240 and m[5:7]==(11,14) for m in sent)
    # The superseded identity cannot restore a stale assignment.
    host.receive(proto.sysex(11,11,(0,old.index,*proto.digest(old.target_id,6),0,1,0)))
    assert not e.GetControlState(state['id'])['mapped']
    mapped=host.controls['knob',2]
    host.receive(proto.sysex(11,11,(0,mapped.index,*proto.digest(mapped.target_id,6),0,1,0)))
    host.receive(proto.sysex(11,9,(0,)))
    host.receive((191,13,64));host.receive((191,45,0))
    assert abs(target.par.Speed.eval()-10*8192/16383)<.001
    e.SetValue(7,id=state['id']);assert target.par.Speed.eval()==7
    pulse=e.AssignParameter('button',5,target.par.Reset)
    assert pulse['mode']=='pulse' and pulse['button_type']=='push'
    toggle=e.AssignParameter('button',6,target.par.Enabled)
    assert toggle['mode']=='toggle'
    fixture.store('assignment_verification',dict(knob_id=state['id'],pulse_id=pulse['id'],toggle_id=toggle['id'],
        discovery=True,auto_offer=True,other_mapping_preserved=True,stale_ack_rejected=True,
        numeric_input=True,software_feedback=True,no_midi_process=True))
    e.Disconnect()
    assert next(s for s in e.GetControlCatalog() if s['id']==state['id'])['comp']==target.path
    fixture.par.reinitextensions.pulse()


def finish(controller):
    root=controller.parent();fixture=root.op('roto_assignment_probe');target=root.op('base_assignment_probe')
    e=fixture.ext.RotoPythonExt;e.Applybinding()
    result=dict(fixture.fetch('assignment_verification'))
    assert e.GetControlState(result['knob_id'])['parameter']=='Speed'
    assert e.GetControlState(result['pulse_id'])['mode']=='pulse'
    assert e.GetControlState(result['toggle_id'])['mode']=='toggle'
    result['extension_reload']=True
    e.RemoveControl(result['pulse_id']);e.Applybinding()
    assert result['pulse_id'] not in [s['id'] for s in e.GetControlStates()]
    result['remove_does_not_restore']=True
    e.Disconnect()
    # A fresh exported component starts in Built-in Value, and still accepts
    # its first picker assignment while hardware LEARN is already open.
    fixture.store('parameter_assignments',[])
    fixture.store('removed_controls',[])
    e.Unbind()
    proto=fixture.op('protocol').module
    e._host.send=lambda message:None
    e._host.start();e._host.receive(proto.sysex(10,12));e._host.receive(proto.sysex(11,1,(0,)))
    e._host.receive(proto.sysex(11,9,(1,)))
    assert fixture.op('inspector/inspector_data').module.assign(fixture.op('inspector'),'knob',1,target.par.Speed)
    assert e._host.learning
    assert e.GetControlStates()[0]['parameter']=='Speed'
    assert e._host.controls['knob',1]._offered_in_learn
    result['first_assignment_in_learn']=True
    e.Disconnect()
    result['errors']=fixture.errors(recurse=True)
    assert not result['errors'],result['errors']
    fixture.destroy();target.destroy()
    Path(project.folder,'assignment_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
