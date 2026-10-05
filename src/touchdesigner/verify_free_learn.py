"""Live actual Parameter Execute callbacks for an unregistered new COMP."""
from pathlib import Path
import json


def begin(controller):
    root=controller.parent()
    for name in ('roto_free_learn_probe','base_free_learn_probe'):
        if root.op(name) is not None:
            raise ValueError('Existing free LEARN probe')
    target=root.create(baseCOMP,'base_free_learn_probe');target.viewer=True
    target.nodeX=2200;target.nodeY=-700
    page=target.appendCustomPage('Controls')
    speed=page.appendFloat('Speed')[0];speed.normMin=0;speed.normMax=10;speed.val=5
    page.appendToggle('Enabled')
    page.appendPulse('Reset')
    fixture=root.copy(controller,name='roto_free_learn_probe');fixture.viewer=True
    fixture.nodeX=2200;fixture.nodeY=-900
    fixture.Disconnect()
    return fixture.path


def start(controller):
    root=controller.parent();fixture=root.op('roto_free_learn_probe');target=root.op('base_free_learn_probe')
    e=fixture.ext.RotoPythonExt;e.Disconnect();e.Applybinding()
    proto=fixture.op('protocol').module
    e._host.send=lambda message:None
    e._host.start();e._host.receive(proto.sysex(10,12));e._host.receive(proto.sysex(11,1,(0,)))
    for key,t in e._host.controls.items():
        e._host.receive(proto.sysex(11,11,(t.index>>7,t.index&127,*proto.digest(t.target_id,6),int(key[0]=='button'),key[1]-1,0)))
    e._host.receive(proto.sysex(11,9,(1,)))
    e._free_learner.sync()
    assert fixture.op('learn_parameters').par.active.eval()
    assert target.path in fixture.op('learn_parameters').par.op.val
    assert e._free_learner.pending is None


def change_new_slider(controller):
    controller.parent().op('base_free_learn_probe').par.Speed=6


def check_offer(controller):
    root=controller.parent();fixture=root.op('roto_free_learn_probe');target=root.op('base_free_learn_probe')
    e=fixture.ext.RotoPythonExt;learner=e._free_learner
    assert learner.pending is not None,'Actual new-COMP slider callback did not offer'
    assert learner.pending['parameter']==target.par.Speed
    assert ('knob',3) not in e._collection.bindings or e._collection.bindings['knob',3].parameter!=target.par.Speed
    assert e._process is None
    old=e._host.controls['knob',8]
    t=learner.pending['template'];proto=fixture.op('protocol').module
    message=proto.sysex(11,11,(t.index>>7,t.index&127,*proto.digest(t.target_id,6),0,2,0))
    assert not learner.receive(message)
    e._host.receive(message)
    state=next(s for s in e.GetControlStates() if (s['kind'],s['slot'])==('knob',3))
    assert state['mapped'] and state['parameter']=='Speed'
    assert e._host.controls['knob',8] is old and old.mapped
    e._host.receive(proto.sysex(11,9,(0,)));learner.sync()
    assert not fixture.op('learn_parameters').par.active.eval()
    e._host.receive((191,14,64));e._host.receive((191,46,0))
    assert abs(target.par.Speed.eval()-10*8192/16383)<.001
    # API value writes must not become a new free learn offer.
    e._host.receive(proto.sysex(11,9,(1,)));learner.sync()
    e.SetValue(7,id=state['id'])
    fixture.store('free_learn_verification',dict(id=state['id'],wire_index=e._host.controls['knob',3].index,
        actual_parameter_callback=True,new_comp_discovered=True,slot_from_hardware_ack=True,
        other_mapping_preserved=True,numeric_hardware_input=True,observer_disabled_outside_learn=True))


def check_ignore_and_reload(controller):
    fixture=controller.parent().op('roto_free_learn_probe');e=fixture.ext.RotoPythonExt
    assert e._free_learner.pending is None,'API SetValue unexpectedly offered during LEARN'
    fixture.store('free_learn_verification',dict(fixture.fetch('free_learn_verification'),api_write_not_offered=True))
    e.Disconnect();fixture.par.reinitextensions.pulse()


def finish(controller):
    root=controller.parent();fixture=root.op('roto_free_learn_probe');e=fixture.ext.RotoPythonExt
    e.Applybinding()
    result=dict(fixture.fetch('free_learn_verification'))
    state=e.GetControlState(result['id'])
    assert state['parameter']=='Speed'
    assert e._host.controls['knob',3].index==result['wire_index']
    result['wire_index_and_assignment_restored']=True
    result['errors']=fixture.errors(recurse=True)
    assert not result['errors'],result['errors']
    e.Disconnect();fixture.destroy();root.op('base_free_learn_probe').destroy()
    Path(project.folder,'free_learn_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
