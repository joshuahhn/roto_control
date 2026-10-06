"""Disconnected native TD acceptance. Run begin/exercise/reload/finish across frames.

Only temporary fixture parameters are touched. Never opens MIDI ports.
"""
from pathlib import Path
import copy
import json
import tempfile

HOLDER='base_multitrack_verification'


def begin(controller):
    root=controller.parent()
    if root.op(HOLDER) is not None:raise ValueError('Existing verification fixture')
    holder=root.create(baseCOMP,HOLDER);holder.viewer=True
    holder.nodeX=2400;holder.nodeY=-1200
    target=holder.create(baseCOMP,'target');target.viewer=True
    target.nodeX=220;target.nodeY=0
    page=target.appendCustomPage('Test')
    for name,value in (('Speed',.25),('Amount',.75)):
        par=page.appendFloat(name)[0];par.normMin=0;par.normMax=1;par.val=value
    fixture=holder.copy(controller,name='controller');fixture.viewer=True
    fixture.nodeX=0;fixture.nodeY=0
    fixture.Disconnect()
    return holder.path


def exercise(controller):
    holder=controller.parent().op(HOLDER);fixture=holder.op('controller');target=holder.op('target')
    e=fixture.ext.RotoPythonExt;e.Applybinding();assert e._process is None
    layout=e.CreateLayout('Verification');e.SelectLayout(layout)
    a=e.GetTracks()[0]['id'];e.RenameTrack(layout,a,'EFFECT')
    aid=e.AssignParameter('knob',1,target.par.Speed)['id']
    b=e.CreateTrack(layout,'VISUAL');e.SelectTrack(layout,b)
    bid=e.AssignParameter('knob',1,target.par.Amount)['id']
    assert e.GetControlState()['id']==bid
    target.par.Speed=.6;e.SelectTrack(layout,a)
    assert e.GetControlState()['id']==aid and e.GetControlState()['value']==.6
    assert target.par.Amount.eval()==.75
    context=e.GetLayoutContext();assert context['track_id']==a
    assert 'EFFECT / CUSTOM' in fixture.op('inspector/title').par.text.eval()
    # Confirmation cannot cross Track boundaries, including identical targets.
    inspector=fixture.op('inspector');module=inspector.op('inspector_data').module
    module.request_clear(inspector,None);e.SelectTrack(layout,b)
    assert not module.confirm_clear(inspector,True,None)
    assert e.GetControlState()['id']==bid
    # Synthetic hardware selection exercises the actual manager + host without ports.
    proto=fixture.op('protocol').module;m=e._layouts
    e._host.connected=e._host.plugin=True
    m.receive(proto.sysex(10,9,(0,0)))
    assert e.GetLayoutContext()['track_id']==a
    t=e._host.controls['knob',1]
    e._host.receive(proto.sysex(11,11,(t.index>>7,t.index&127,*proto.digest(t.target_id,6),0,0,0)))
    m.acknowledge();assert e.GetControlState()['mapped']
    e._host.receive((191,12,64));e._host.receive((191,44,0))
    assert abs(target.par.Speed.eval()-8192/16383)<.0001
    assert target.par.Amount.eval()==.75
    e.Disconnect();e.SelectTrack(layout,b)
    assert not e._host.connected and e._process is None
    state=dict(layout=layout,a=a,b=b,aid=aid,bid=bid,native_api=True,
               same_name_independent_mappings=True,current_value_recall=True,
               inspector_context=True,confirmation_scoped=True,synthetic_track_selection=True,
               synthetic_mapping_and_input=True,physical_acceptance=False)
    holder.store('result',state)
    fixture.par.Track=a  # actual Parameter Execute callback, verified next frame
    return state


def reload(controller):
    holder=controller.parent().op(HOLDER);fixture=holder.op('controller');state=holder.fetch('result')
    assert fixture.GetLayoutContext()['track_id']==state['a']
    state['native_track_menu']=True
    fixture.par.Newtrackname='THIRD';fixture.par.Newtrack.pulse()
    return 'New Track pulse queued; call save_reload next frame'


def save_reload(controller):
    holder=controller.parent().op(HOLDER);fixture=holder.op('controller');state=holder.fetch('result')
    assert len(fixture.GetTracks())==3
    assert fixture.GetTracks()[-1]['name']=='THIRD'
    state['native_new_track']=True
    fixture.SelectTrack(state['layout'],state['b'])
    fixture.Disconnect()
    path=Path(tempfile.gettempdir())/'roto_multitrack_native_fixture.tox'
    if path.exists():raise FileExistsError(path)
    holder.store('expected_registry',copy.deepcopy(fixture.fetch('layout_registry')))
    fixture.save(str(path));fixture.destroy()
    restored=holder.loadTox(str(path));restored.name='controller'
    holder.store('temp_path',str(path))
    return 'Saved and reloaded actual tox; call finish next frame'


def finish(controller):
    holder=controller.parent().op(HOLDER);fixture=holder.op('controller');state=holder.fetch('result')
    fixture.Applybinding()
    assert fixture.GetLayoutContext()['track_id']==state['b']
    assert fixture.GetControlState()['id']==state['bid']
    expected=holder.fetch('expected_registry');actual=fixture.fetch('layout_registry')
    # Runtime diagnostics in catalogs may refresh; identities/targets must not.
    for old,new in zip(expected['records'],actual['records']):
        assert old['id']==new['id'] and old['active_track']==new['active_track']
        for ot,nt in zip(old['tracks'],new['tracks']):
            assert ot['id']==nt['id'] and ot['name']==nt['name']
            for op_,np in zip(ot['plugins'],nt['plugins']):
                for key in ('id','group_id','device_id','targets'):assert op_[key]==np[key],key
    state['tox_save_reload']=True
    assert not fixture.errors(recurse=True),fixture.errors(recurse=True)
    assert fixture.ext.RotoPythonExt._process is None
    state.update(no_midi_process=True,errors='')
    fixture.Disconnect();Path(holder.fetch('temp_path')).unlink();holder.destroy()
    Path(project.folder,'multitrack_native_verification.json').write_text(json.dumps(state,indent=2)+'\n')
    return state
