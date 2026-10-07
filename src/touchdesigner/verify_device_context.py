"""Native same-Track Device fixture; synthetic RX only, no MIDI ports opened.

Run begin, follow, controls, after_controls, persistence, reopened and finish
across frames. Temporary native COMPs live at (2400,-1900); targets at 220/440.
"""
from pathlib import Path
import copy
import json
import tempfile

HOLDER='base_device_verification'


def load_source(source,filename):
    namespace=dict(globals());path=source/filename
    exec(compile(path.read_text(),str(path),'exec'),namespace)
    return namespace


def fixture(controller):
    h=controller.parent().op(HOLDER);c=h.op('controller')
    return h,c,c.ext.RotoPythonExt,h.fetch('result')


def select(h,node):
    for child in h.children:child.selected=False
    node.selected=True;node.current=True


def ack(e,proto):
    for target in list(e._host.controls.values()):
        e._receive_midi(proto.sysex(11,11,(target.index>>7,target.index&127,
            *proto.digest(target.target_id,6),int(target.key[0]=='button'),target.key[1]-1,0)))


def begin(controller):
    source=Path(project.folder);parent=controller.parent()
    assert parent.op(HOLDER) is None
    h=parent.create(baseCOMP,HOLDER);h.viewer=True;h.nodeX,h.nodeY=2400,-1900
    pane=ui.panes.current
    h.store('pane',dict(id=pane.id,owner=pane.owner.path,
        selected=[n.path for n in pane.owner.selectedChildren],current=pane.owner.currentChild.path if pane.owner.currentChild else None))
    c=h.copy(controller,name='controller');c.Disconnect();c.par.Followcomp=False
    load_source(source,'upgrade_layouts.py')['upgrade'](c,source);c.Applybinding()
    for name,value,x in (('a',.25,220),('b',.75,440)):
        target=h.create(baseCOMP,name);target.viewer=True;target.nodeX,target.nodeY=x,0
        page=target.appendCustomPage('Test');par=page.appendFloat('Speed')[0]
        par.min=par.normMin=0;par.max=par.normMax=1;par.clampMin=par.clampMax=True;par.val=value
        page.appendPulse('Reset')
        watcher=target.create(parameterexecuteDAT,'reset_observer');watcher.viewer=True
        watcher.nodeX,watcher.nodeY=0,0;watcher.par.language='python'
        watcher.par.op='..';watcher.par.pars='Reset';watcher.par.builtin=False;watcher.par.custom=True;watcher.par.onpulse=True
        watcher.text='def onPulse(par):\n    par.owner.store("pulses",par.owner.fetch("pulses",0)+1)\n'
    e=c.ext.RotoPythonExt;layout=e.CreateLayout('Device verification');e.SelectLayout(layout)
    track=e.GetTracks()[0]['id'];e.RenameTrack(layout,track,'FX')
    pa=e.GetPlugins()[0]['id'];e.RenamePlugin(layout,track,pa,'A')
    aid=e.AssignParameter('knob',1,h.op('a').par.Speed)['id']
    e.AssignParameter('button',1,h.op('a').par.Reset,button_type='push')
    pb=e.CreatePlugin(layout,track,'B');e.SelectPlugin(layout,track,pb)
    bid=e.AssignParameter('knob',1,h.op('b').par.Speed)['id']
    e.SelectPlugin(layout,track,pa)
    e.SetPluginComp(layout,track,pa,h.op('a'));e.SetPluginComp(layout,track,pb,h.op('b'))
    pane.owner=h;select(h,h.op('a'));c.par.Followcomp=True
    h.store('result',dict(layout=layout,track=track,pa=pa,pb=pb,aid=aid,bid=bid,
        physical_acceptance=False,native_build=str(app.build),original_values=[.25,.75]))
    assert len(c.GetPlugins())==2 and c.par.Plugin.eval()==pa
    return 'begin: upgraded isolated fixture; main controller untouched'


def follow(controller):
    h,c,e,r=fixture(controller);f=e._follow
    select(h,h.op('b'));f.observe(force=True);f.flush()
    assert e.GetLayoutContext()['key']==(r['layout'],r['track'],r['pb'])
    assert c.par.Focuscomp.eval()==h.op('b') and c.par.Plugin.eval()==r['pb']
    select(h,h.op('a'));f.observe(force=True);f.flush()
    assert e.GetLayoutContext()['plugin_id']==r['pa']
    assert [h.op(n).par.Speed.eval() for n in ('a','b')]==r['original_values']
    assert h.op('a').fetch('pulses',0)==0
    assert c.par.Pluginname.eval()=='a' and not c.par.Pluginname.enable
    c.par.Followcomp=False
    r.update(native_same_track_follow=True,selection_no_parameter_or_pulse_writes=True,
        device_custom_parameter_callback=True,linked_comp_naming=True)
    h.store('result',r);return 'follow passed'


def controls(controller):
    h,c,e,r=fixture(controller);f=e._follow;m=e._layouts;p=c.op('protocol').module
    e._host.connected=e._host.plugin=True;ack(e,p)
    e._receive_midi((191,12,127));e._receive_midi((191,44,127))
    assert h.op('a').par.Speed.eval()==1
    e._receive_midi(p.sysex(11,7,(1,)))
    for packet in ((191,12,0),(191,44,0),(191,20,127)):e._receive_midi(packet)
    ack(e,p);f.flush(backlog=True)
    assert m.plugin()['id']==r['pa'] and f.gated
    assert [h.op(n).par.Speed.eval() for n in ('a','b')]==[1,.75]
    f.flush();assert m.plugin()['id']==r['pb'] and m.track()['id']==r['track']
    assert not e.GetControlState()['mapped']
    e._receive_midi((191,44,0));assert h.op('b').par.Speed.eval()==.75
    ack(e,p);e._receive_midi((191,44,0));assert h.op('b').par.Speed.eval()==.75
    e._receive_midi((191,12,0));assert h.op('b').par.Speed.eval()==0
    e.SelectPlugin(r['layout'],r['track'],r['pa']);ack(e,p)
    e._receive_midi((191,20,127))
    r.update(same_batch_backlog_old_input_fenced=True,fresh_recall_required=True,
        real_parameter_dispatch=True,pulse_expected=1)
    h.store('result',r);return 'controls passed; native Pulse checked next frame'


def after_controls(controller):
    h,c,e,r=fixture(controller);f=e._follow;m=e._layouts;p=c.op('protocol').module
    assert h.op('a').fetch('pulses',0)==1
    e._receive_midi(p.sysex(11,13,(1,)));e._receive_midi(p.sysex(11,7,(1,)));f.flush()
    assert m.locked and m.plugin()['id']==r['pb'];ack(e,p)
    e._receive_midi((191,12,127));e._receive_midi((191,44,127))
    assert [h.op(n).par.Speed.eval() for n in ('a','b')]==[1,1]
    e._receive_midi(p.sysex(11,13,(0,)));f.flush()
    ids=[r['pa'],r['pb']]
    for i in range(2,9):ids.append(e.CreatePlugin(r['layout'],r['track'],'DEV'+str(i)))
    e._pending=b'';e._receive_midi(p.sysex(11,4,(8,)))
    packets=[json.loads(line)['midi'] for line in e._pending.splitlines()]
    assert list(p.sysex(11,2,(9,))) in packets and list(p.sysex(11,3,(8,))) in packets
    assert m.plugin()['id']==r['pb'] and f.pending is None
    e._receive_midi(p.sysex(11,7,(0,)));f.flush()
    assert m.plugin()['id']==ids[8] and e.GetControlStates()==[]
    e.SelectPlugin(r['layout'],r['track'],r['pa'])
    for plugin in ids[2:]:e.RemovePlugin(r['layout'],r['track'],plugin)
    e.Disconnect()
    m.capture(force=True)
    before=copy.deepcopy(m.data)
    load_source(Path(project.folder),'upgrade_layouts.py')['upgrade'](c,Path(project.folder));c.Applybinding()
    assert c.ext.RotoPythonExt._layouts.data==before
    r.update(real_pulse_once=True,locked_explicit_device_selection=True,ninth_device_bank_and_selection=True,
        repeated_upgrade_idempotent=True)
    h.store('result',r);return 'guard / bank / repeated upgrade passed'


def persistence(controller):
    h,c,e,r=fixture(controller);e.Disconnect()
    h.op('a').name='renamed_a'
    e._follow.refresh_links();c.par.Followcomp=True
    select(h,h.op('renamed_a'));e._follow.observe(force=True);e._follow.flush()
    assert e.GetLayoutContext()['plugin_id']==r['pa']
    assert c.par.Pluginname.eval()=='renamed_a'
    path=Path(tempfile.gettempdir())/'roto-device-native-verification.tox'
    if path.exists():path.unlink()
    c.save(str(path));h.store('temp_path',str(path));c.destroy()
    loaded=h.loadTox(str(path));loaded.name='controller'
    r.update(rename_before_save=True);h.store('result',r)
    return 'managed tox saved/reloaded; verify next frame'


def reopened(controller):
    h,c,e,r=fixture(controller);e.Applybinding();e.Tick()
    assert e.GetLayoutContext()['plugin_id']==r['pa']
    assert len(e.GetPlugins())==2 and c.par.Focuscomp.eval()==h.op('renamed_a')
    assert c.GetControlState()['id']==r['aid'] and c.GetControlState()['valid']
    assert c.par.Followcomp.eval() and e._follow.pending is None and e._process is None
    assert c.par.Pluginname.eval()=='renamed_a'
    assert h.op('a') is None and h.op('renamed_a').fetch('pulses',0)==1
    assert not c.errors(recurse=True),c.errors(recurse=True)
    r.update(tox_reload_ids_links_library=True,baseline_only_reload=True,no_process=True,errors='')
    h.store('result',r);return 'reopened passed'


def project_presave(controller):
    """Actual project save callback with timeline stopped and no manual refresh."""
    h,c,e,r=fixture(controller);controller.Disconnect();c.Disconnect()
    c.par.Followcomp=True
    root.time.play=False
    h.op('a').name='project_renamed_a'
    path=Path(project.folder,'roto_device_presave_verification.toe')
    assert not path.exists()
    h.store('temp_project',str(path))
    r.update(project_presave_test=True);h.store('result',r)
    project.save(str(path))
    plugin=c.fetch('layout_registry')['records'][-1]['tracks'][0]['plugins'][0]
    assert plugin['focus_comp']['path']=='../project_renamed_a'
    assert plugin['plugin_name']=='project_rena'
    assert all(t['comp']=='../project_renamed_a' for t in plugin['targets'])
    assert c.par.Pluginname.eval()=='project_rena'
    return str(path)


def project_reopened(controller):
    """Caller pauses time again after reload; TD may restart its global clock."""
    h,c,e,r=fixture(controller);c.Applybinding();e.Tick()
    assert not root.time.play
    assert c.par.Followcomp.eval() and c.GetLayoutContext()['plugin_id']==r['pa']
    assert c.par.Focuscomp.eval()==h.op('project_renamed_a')
    assert c.GetControlState()['id']==r['aid'] and c.GetControlState()['valid']
    assert c.par.Pluginname.eval()=='project_rena'
    assert e._follow.pending is None and e._process is None
    assert not c.errors(recurse=True),c.errors(recurse=True)
    r.update(actual_stopped_timeline_project_presave=True,project_reopen_valid_target_and_name=True)
    evidence_path=Path(project.folder,'device_context_native_verification.json')
    evidence=json.loads(evidence_path.read_text());evidence.update({k:v for k,v in r.items() if k.startswith(('actual_','project_'))})
    evidence_path.write_text(json.dumps(evidence,indent=2)+'\n')
    saved=h.fetch('pane');pane=next(p for p in ui.panes if p.id==saved['id'])
    temp=Path(h.fetch('temp_project'));c.Disconnect();h.destroy()
    pane.owner=op(saved['owner'])
    for node in pane.owner.children:node.selected=node.path in saved['selected']
    if saved['current']:op(saved['current']).current=True
    root.time.play=True;temp.unlink()
    return dict(actual_stopped_timeline_project_presave=True,project_reopen_valid_target_and_name=True)


def finish(controller):
    h,c,e,r=fixture(controller);saved=h.fetch('pane');pane=next(p for p in ui.panes if p.id==saved['id'])
    pane.owner=op(saved['owner'])
    for node in pane.owner.children:node.selected=node.path in saved['selected']
    if saved['current']:op(saved['current']).current=True
    e.Disconnect();Path(h.fetch('temp_path')).unlink();h.destroy()
    Path(project.folder,'device_context_native_verification.json').write_text(json.dumps(r,indent=2)+'\n')
    return r
