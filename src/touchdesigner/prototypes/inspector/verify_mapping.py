"""Native configuration/accordion fixtures; no production config or MIDI writes."""
from pathlib import Path
import copy,json

def verify():
    model=op('/inspector_model');production=model.par.Controller.eval()
    before=production.GetControlCatalog();registry=copy.deepcopy(production.fetch('layout_registry'))
    session=model.ext.InspectorModel.adapter.Session();views=[op('/inspector_below'),op('/inspector_popup')]
    holder=production.parent().create(baseCOMP,'base_inspector_mapping_verification');holder.viewer=True
    holder.nodeX=700;holder.nodeY=-500
    page=holder.appendCustomPage('Fixture')
    page.appendFloat('Amount');holder.par.Amount=.37
    page.appendInt('Count');holder.par.Count=0
    page.appendToggle('Enabled');page.appendPulse('Trigger')
    menu=page.appendMenu('Choice')[0];menu.menuNames=['a','b','c'];menu.menuLabels=['A','B','C'];menu.val='b'
    clone=None;callback=None;styles=[v.ext.InspectorView.style for v in views]
    values=lambda:tuple(holder.par[n].eval() for n in ('Amount','Count','Enabled','Trigger','Choice'))
    initial=values()
    try:
        for v in views:v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        clone=holder.copy(production,name='controller');clone.Disconnect();clone.par.Followcomp=False;clone.Applybinding()
        clone.SelectLayout(clone.CreateLayout('Mapping fixture'))
        ids={}
        for kind,slot,name in [('knob',2,'Amount'),('knob',3,'Count'),('button',1,'Choice'),('button',2,'Enabled'),('button',3,'Trigger')]:
            ids[name]=clone.AssignParameter(kind,slot,holder.par[name])['id']
        clone.store('needs_relearn',())
        ext=clone.ext.RotoPythonExt;host=ext._host;packets=[];host.send=lambda packet:packets.append(tuple(packet))
        host.connected=host.plugin=True
        for target in host.controls.values():target.mapped=True
        host._sync();ext._publish();assert ext._process is None
        model.par.Controller=clone;model.Sync();model.Flush();key=model.ActiveContext()
        v=views[0];u=v.ext.InspectorView;u.style='below'
        v.Action('slot1');v.Action('mapping_toggle')
        editor=u._editors[0];mapping=editor.op('container_mapping')
        assert editor.height==312 and mapping.par.display.eval()
        assert mapping.op('field_minimum').par.editmode.eval()=='editable'
        draft=v.op('base_draft');snapshot=clone.GetControlState(ids['Amount'])
        draft.par.Mapmaximum=.2
        assert not v.Action('mapping_apply')
        assert clone.GetControlState(ids['Amount'])==snapshot
        assert values()==initial and not packets
        draft.par.Mapminimum=-1;draft.par.Mapmaximum=2
        assert v.Action('mapping_apply')
        state=clone.GetControlState(ids['Amount'])
        assert state['minimum']==-1 and state['maximum']==2 and state['requires_relearn'] and not state['mapped']
        assert model.Health(key,1)['code']=='relearn'
        assert values()==initial and len(packets)==1  # One unmap; no Value/Pulse dispatch.
        assert v.op('base_draft').par.Value.eval()==.37
        # A matching ACK changes health, not the configured target/token.
        token=model.GetToken(key,1)
        u._error='Ping sent · awaiting hardware ACK'
        host.controls[('knob',2)].mapped=True;host._sync();ext._publish();model.Sync();model.Flush()
        assert model.GetToken(key,1)==token and not u._mapping.IsStale(model,key,1)
        assert not clone.GetControlState(ids['Amount'])['requires_relearn']
        assert not u._error and model.Health(key,1)['code']=='mapped'
        for e in u._editors:
            assert e.op('container_mapping/text_status').par.text.eval()=='Mapping saved · hardware acknowledged'
            assert e.op('field_Value').par.editmode.eval()=='editablecontinuous'
            assert e.op('container_mapping/mapping_apply').par.enable.eval()
        assert values()==initial and len(packets)==1
        v.Action('mapping_cancel');assert editor.height==178 and not u._mapping.open
        # Native Menu/Toggle/Pulse retain fixed compatible Mode and Range.
        for slot,mode in [(8,'cycle'),(9,'toggle'),(10,'pulse')]:
            v.Action('slot'+str(slot));v.Action('mapping_toggle')
            schema=model.MappingSchema(key,slot)
            assert schema['modes']==(mode,) and not schema['range_editable']
            assert mapping.op('field_minimum').par.editmode.eval()=='selectonly'
            assert not mapping.op('choice_mode').par.enable.eval()
            if slot==9:
                old=clone.GetControlState(ids['Enabled']);n=len(packets)
                draft.par.Mapinput='push';assert v.Action('mapping_apply')
                new=clone.GetControlState(ids['Enabled'])
                assert new['mapped'] and not new['requires_relearn'] and new['button_type']=='push'
                assert old['id']==new['id'] and len(packets)==n and values()==initial
        v.Action('slot2');v.Action('mapping_toggle');draft.par.Mapminimum=-.5
        assert not v.Action('mapping_apply');assert 'integers' in u._mapping.message
        # Draft stale after native metadata change; no write to replacement state.
        v.Action('slot1');v.Action('mapping_toggle');token=u._mapping.token
        clone.ConfigureControl(ids['Amount'],maximum=3);model.Sync();model.Flush()
        assert model.GetToken(key,1)!=token
        snapshot=clone.GetControlState(ids['Amount']);assert not v.Action('mapping_apply')
        assert clone.GetControlState(ids['Amount'])==snapshot
        # Touch and HW LEARN update capability even with an already open draft.
        v.Action('mapping_toggle');v.Action('mapping_toggle')
        for name in ('touched','learning'):
            target=host.controls[('knob',2)] if name=='touched' else host
            setattr(target,name,True);host._sync();ext._publish();model.Sync();model.Flush()
            assert not model.Capabilities(key,1)['mapping']['enabled']
            assert not mapping.op('mapping_apply').par.enable.eval()
            setattr(target,name,False);host._sync();ext._publish();model.Sync();model.Flush()
        # Callback registration uses the supported legacy registration factory.
        callback=holder.copy(production,name='callback_controller');callback.Disconnect();callback.par.Followcomp=False
        callback.op('registration').text="""def onRegister(controller):
    def changed(event):controller.store('fixture_events',controller.fetch('fixture_events',[])+[event])
    return controller.BindControls([dict(kind='button',slot=1,id='fixture.callback',label='Callback',mode='toggle',button_type='toggle',on_change=changed)],group_id='mapping.callback.fixture')
"""
        callback.par.Setupmode='callback';assert callback.Applybinding()
        callback.store('fixture_events',[]);ce=callback.ext.RotoPythonExt;ch=ce._host;cp=[];ch.send=lambda p:cp.append(tuple(p))
        ch.connected=ch.plugin=True;ch.controls[('button',1)].mapped=True;ch._sync();ce._publish()
        model.par.Controller=callback;model.Sync();model.Flush();ck=model.ActiveContext()
        assert model.HasContext(ck) and model.MappingSchema(ck,8)['modes']==('toggle','pulse')
        model.Configure(ck,8,dict(mode='pulse'),model.GetToken(ck,8));model.Flush()
        assert callback.GetControlState('fixture.callback')['requires_relearn']
        assert not callback.fetch('fixture_events') and len(cp)==1 and values()==initial
        result=dict(native_build=str(app.build),invalid_range_preserves_mapping=True,
                    one_configure_one_unmap_no_value_write=True,input_only_keeps_ack=True,
                    native_menu_toggle_pulse_fixed_schema=True,integer_guard=True,
                    stale_touch_learn_guards=True,callback_factory_mode_change_no_dispatch=True,
                    mapping_cancel_local_only=True,fixture_native_values_preserved=True,
                    ack_refreshes_both_editor_statuses_without_staling_value=True)
    finally:
        for v,style in zip(views,styles):v.ext.InspectorView.style=style;v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        model.par.Controller=production;model.Sync();model.Flush()
        if clone:clone.Disconnect()
        if callback:callback.Disconnect()
        holder.destroy()
    assert production.GetControlCatalog()==before and production.fetch('layout_registry')==registry
    assert model.ext.InspectorModel.adapter.Session()==session
    assert model.Stats()['subscribers']==2 and not model.Stats()['subscriber_errors']
    assert not any(c.errors(recurse=True) for c in [model]+views)
    result.update(production_catalog_registry_session_preserved=True,subscribers=2,errors='')
    Path(project.folder+'/prototypes/inspector/mapping_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

verify()
