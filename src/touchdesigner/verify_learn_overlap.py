"""Native reproduction of the captured Lowthresh/Masksource ACK order.

Run begin, change_low, change_mask, acknowledge, reload, finish across TD frames.
Synthetic MIDI only; the main controller and its parameter values stay intact.
"""
from pathlib import Path
import json

HOLDER = 'base_learn_overlap_verification'


def fixture(controller):
    holder = controller.parent().op(HOLDER)
    comp = holder.op('controller')
    return holder, comp, comp.ext.RotoPythonExt, holder.op('target')


def packet(comp, offer, kind, slot):
    proto = comp.op('protocol').module
    target = offer['template']
    return proto.sysex(11,11,(target.index>>7,target.index&127,
        *proto.digest(target.target_id,6),kind,slot-1,0))


def begin(controller):
    assert controller.parent().op(HOLDER) is None
    holder = controller.parent().create(baseCOMP,HOLDER)
    holder.viewer = holder.display = True
    holder.nodeX,holder.nodeY = 700,-500
    comp = holder.copy(controller,name='controller')
    comp.nodeX,comp.nodeY = 0,-250
    comp.Disconnect();comp.par.Followcomp = False
    comp.op('free_learn').text = Path(project.folder,'code/py/roto_python/free_learn.py').read_text(encoding='utf-8')
    comp.par.reinitextensions.pulse();comp.Applybinding()
    e = comp.ext.RotoPythonExt
    layout = e.CreateLayout('LEARN overlap verification');e.SelectLayout(layout)
    target = holder.create(baseCOMP,'target')
    target.viewer = target.display = True
    target.nodeX,target.nodeY = 0,0
    page = target.appendCustomPage('Test')
    low = page.appendFloat('Lowthresh')[0]
    low.min = low.normMin = 0;low.max = low.normMax = 1;low.val = .2
    mask = page.appendMenu('Masksource',label='Mask Image')[0]
    mask.menuNames = ['source','control'];mask.menuLabels = ['Source (Input 1)','Control (Input 2)'];mask.val = 'source'
    e._host.send = lambda message:None
    e._host.connected = e._host.plugin = True
    e._receive_midi(comp.op('protocol').module.sysex(11,9,(1,)))
    assert e._free_learner.active and not e._follow.gated
    return 'observer initialized; native edits start next frame'


def change_low(controller):
    h,c,e,t = fixture(controller)
    t.par.Lowthresh.val = .4
    return 'native Lowthresh edit sent; next stage after callback'


def change_mask(controller):
    h,c,e,t = fixture(controller)
    assert e._free_learner.pending['parameter'] == t.par.Lowthresh
    h.store('low_ack',packet(c,e._free_learner.pending,0,2))
    t.par.Masksource.val = 'control'
    return 'native Masksource edit sent; next stage after callback'


def acknowledge(controller):
    h,c,e,t = fixture(controller)
    offer = e._free_learner.pending
    assert offer['parameter'] == t.par.Masksource and offer['template'].key[0] == 'knob'
    mask_ack = packet(c,offer,1,1)
    assert mask_ack[7:9] != h.fetch('low_ack')[7:9]
    # The physical capture reports both mappings only after LEARN exit,
    # newest Menu/Button ACK first, then the older Lowthresh/Knob ACK.
    e._receive_midi(c.op('protocol').module.sysex(11,9,(0,)))
    e._receive_midi(mask_ack);e._receive_midi(h.fetch('low_ack'))
    states = c.GetControlStates()
    assert {(s['kind'],s['slot'],s['parameter'],s['mapped']) for s in states} == {
        ('button',1,'Masksource',True),('knob',2,'Lowthresh',True)}
    assert t.par.Lowthresh.eval() == .4 and t.par.Masksource.eval() == 'control'
    e._receive_midi((191,13,64));e._receive_midi((191,45,0))
    assert abs(t.par.Lowthresh.eval()-8192/16383) < .00001
    e._receive_midi((191,20,127));assert t.par.Masksource.eval() == 'source'
    h.store('identities',[(key,target.index,target.target_id) for key,target in e._host.controls.items()])
    h.store('result',dict(native_callbacks=True,newest_ack_before_oldest=True,
        menu_kind_from_ack=True,no_commit_value_writes=True,knob_dispatch=True,menu_button_cycle=True,
        physical_acceptance=False,native_build=str(app.build)))
    return 'native overlap, Menu kind inference and dispatch passed'


def reload(controller):
    h,c,e,t = fixture(controller)
    e.Disconnect();e._layouts.capture(force=True)
    c.op('free_learn').text = Path(project.folder,'code/py/roto_python/free_learn.py').read_text(encoding='utf-8')
    c.par.reinitextensions.pulse()
    return 'extension reinitialized; check restored identities next frame'


def finish(controller):
    h,c,e,t = fixture(controller)
    c.Applybinding()
    assert [(key,target.index,target.target_id) for key,target in e._host.controls.items()] == h.fetch('identities')
    e._host.send = lambda message:None;e._host.connected = e._host.plugin = True
    for key,index,identity in h.fetch('identities'):
        p = c.op('protocol').module
        e._receive_midi(p.sysex(11,11,(index>>7,index&127,*p.digest(identity,6),int(key[0]=='button'),key[1]-1,0)))
    assert all(state['mapped'] for state in c.GetControlStates())
    result = dict(h.fetch('result'),reload_hash_recall=True,errors=c.errors(recurse=True))
    assert not result['errors'],result['errors']
    e.Disconnect();h.destroy()
    Path(project.folder,'learn_overlap_native_verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
