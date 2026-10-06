"""Native Tag discovery / scoped LEARN / Device-page verification.

Run begin, route, edit, learn, persistence, finish across TD frames.
No physical MIDI ports; main project parameters and selection stay untouched.
"""
from pathlib import Path
import json
import tempfile
import uuid

HOLDER='base_tag_device_verification'


def fixture(controller):
    h=controller.parent().op(HOLDER);c=h.op('controller')
    return h,c,c.ext.RotoPythonExt


def ack(c,e):
    p=c.op('protocol').module
    for key,t in list(e._host.controls.items()):
        e._receive_midi(p.sysex(11,11,(t.index>>7,t.index&127,*p.digest(t.target_id,6),int(key[0]=='button'),key[1]-1,0)))


def begin(controller):
    assert controller.parent().op(HOLDER) is None
    h=controller.parent().create(baseCOMP,HOLDER);h.viewer=h.display=True
    h.nodeX,h.nodeY=700,-600
    c=h.copy(controller,name='controller');c.nodeX,c.nodeY=0,-250
    c.Disconnect();c.par.Followcomp=False
    for name in ('free_learn','text_comp_follow','setup'):
        c.op(name).text=Path(project.folder,'code/py/roto_python',name+'.py').read_text(encoding='utf-8')
    c.par.reinitextensions.pulse();c.Applybinding();c.op('setup').module.configure_ui(c)
    e=c.ext.RotoPythonExt;layout=e.CreateLayout('Tag verification');e.SelectLayout(layout)
    for name,x in (('tag_a',0),('tag_b',220)):
        t=h.create(baseCOMP,name);t.viewer=t.display=True;t.nodeX,t.nodeY=x,0
        p=t.appendCustomPage('Controls').appendFloat('Power')[0]
        p.min=p.normMin=2;p.max=p.normMax=16;p.val=8
    assert len(next(p for p in c.customPages if p.name=='Device').pars)==6
    assert len(next(p for p in c.customPages if p.name=='Layout').pars)==10
    assert c.par.Plugin.page.name=='Device' and c.par.Layout.page.name=='Layout'
    assert c.par.Plugin.label=='Active Device (SEL)' and c.par.Track.label=='Active Track group (FUNC)'
    h.store('result',dict(layout=layout,track=e._layouts.track()['id'],native_build=str(app.build),physical_acceptance=False))
    return 'native fixture initialized; next stage adds actual OP tags'


def route(controller):
    h,c,e=fixture(controller);f=e._follow
    f.sampler=lambda:(('probe',h.id,h.path),(h.op('tag_a'),))
    c.par.Followcomp=True;f.observe(force=True)
    for name in ('tag_a','tag_b'):h.op(name).tags.add('roto_device')
    f.next_tag_scan=0;f.observe(force=True);f.flush()
    r=h.fetch('result');m=e._layouts
    assert m.data['active']==r['layout'] and m.track()['id']==r['track']
    assert m.plugin()['focus_comp']['path']=='../tag_a'
    r['pa']=m.plugin()['id'];r['pb']=next(p['id'] for p in m.track()['plugins'] if p.get('focus_comp',{}).get('path')=='../tag_b')
    assert f.sync_tags(force=True)==[] and len(m.track()['plugins'])==3
    e._host.send=lambda message:None;e._host.connected=e._host.plugin=True
    e._receive_midi(c.op('protocol').module.sysex(11,9,(1,)))
    assert e._free_learner.active
    r.update(actual_tag_discovery=True,tag_added_selected_comp_follow=True,layout_and_track_retained=True,separate_ui_pages=True)
    h.store('result',r)
    return 'Tag discovery, Follow and separate UI pages passed; LEARN observer initializing'


def edit(controller):
    h,c,e=fixture(controller)
    assert e._free_learner.pending is None
    assert not e._free_learner.offer(h.op('tag_b').par.Power)
    h.op('tag_a').par.Power=9
    return 'actual custom parameter edit; check offer next frame'


def learn(controller):
    h,c,e=fixture(controller);r=h.fetch('result');p=c.op('protocol').module
    offer=e._free_learner.pending
    assert offer is not None and offer['parameter']==h.op('tag_a').par.Power
    t=offer['template'];message=p.sysex(11,11,(t.index>>7,t.index&127,*p.digest(t.target_id,6),0,1,0))
    e._receive_midi(p.sysex(11,9,(0,)));e._receive_midi(message)
    a=next(s for s in c.GetControlStates() if s['slot']==2);assert a['mapped'] and a['parameter']=='Power'
    r['aid']=a['id'];r['wire']=e._host.controls['knob',2].target_id
    e.SelectComp(h.op('tag_b'))
    assert c.GetControlStates()==[] and e._layouts.plugin()['id']==r['pb']
    b=e.AssignParameter('knob',2,h.op('tag_b').par.Power);r['bid']=b['id'];ack(c,e)
    e.SelectComp(h.op('tag_a'));ack(c,e)
    assert c.GetControlState(r['aid'])['mapped'] and r['aid']!=r['bid']
    e._receive_midi((191,13,127));e._receive_midi((191,45,127))
    assert h.op('tag_a').par.Power.eval()==16 and h.op('tag_b').par.Power.eval()==8
    assert e._layouts.data['active']==r['layout'] and e._layouts.track()['id']==r['track']
    r.update(native_learn_callback=True,foreign_comp_offer_rejected=True,device_libraries_isolated=True,parameter_dispatch_isolated=True)
    h.store('result',r);return 'native own-Device LEARN, A/B/A recall and dispatch passed'


def persistence(controller):
    h,c,e=fixture(controller);e.Disconnect()
    h.op('tag_a').name='renamed_tag_a';e._follow.refresh_links();e._layouts.capture(force=True)
    path=Path(tempfile.gettempdir())/('roto-tag-verification-'+uuid.uuid4().hex+'.tox')
    c.save(str(path));h.store('temp_path',str(path));c.destroy()
    loaded=h.loadTox(str(path));loaded.name='controller'
    return 'managed tox saved/reloaded; verify next frame'


def finish(controller):
    h,c,e=fixture(controller);r=h.fetch('result');c.Applybinding()
    assert e._layouts.plugin()['id']==r['pa'] and len(e._layouts.track()['plugins'])==3
    assert e._follow.sync_tags(force=True)==[]
    assert e._layouts.plugin()['focus_comp']['path']=='../renamed_tag_a'
    assert c.GetControlState(r['aid'])['valid'] and e._host.controls['knob',2].target_id==r['wire']
    assert c.par.Plugin.page.name=='Device' and c.par.Layout.page.name=='Layout'
    c.op('setup').module.configure_ui(c)
    assert len(next(p for p in c.customPages if p.name=='Device').pars)==6
    e._host.send=lambda message:None;e._host.connected=e._host.plugin=True;ack(c,e)
    assert c.GetControlState(r['aid'])['mapped']
    assert not c.errors(recurse=True)
    r.update(rename_reload_no_duplicate=True,reload_hash_recall=True,ui_upgrade_idempotent=True,errors='')
    path=Path(h.fetch('temp_path'));e.Disconnect();h.destroy();path.unlink()
    Path(project.folder,'tag_device_native_verification.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    return r
