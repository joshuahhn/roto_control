"""Native parity fixture: disconnected controller, no production writes or MIDI."""
from pathlib import Path
import copy,json

def verify():
    m=op('/inspector_model');production=m.par.Controller.eval()
    before=production.GetControlCatalog();registry=copy.deepcopy(production.fetch('layout_registry'))
    session=m.ext.InspectorModel.adapter.Session();routing=production.GetLayoutContext()['key']
    views=[op('/inspector_below'),op('/inspector_popup')]
    styles=[v.ext.InspectorView.style for v in views]
    pane=ui.panes.current;original_owner=pane.owner
    holder=production.parent().create(baseCOMP,'base_inspector_parity_verification')
    holder.nodeX=700;holder.nodeY=-500;holder.viewer=True
    holder.appendCustomPage('Fixture').appendFloat('Amount');holder.par.Amount=.37
    effect=holder.create(baseCOMP,'effect_b');effect.appendCustomPage('Fixture').appendFloat('Power');effect.par.Power=.61
    clone=None;callback=None;result={}
    try:
        for v in views:v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        clone=holder.copy(production,name='controller');clone.Disconnect();clone.par.Followcomp=False;clone.Applybinding()
        layout=clone.CreateLayout('Parity fixture');clone.SelectLayout(layout)
        first=clone.AssignParameter('knob',1,holder.par.Amount)['id']
        second=clone.AssignParameter('knob',2,effect.par.Power)['id']
        ext=clone.ext.RotoPythonExt;manager=ext._layout_manager()
        track=clone.GetLayoutContext()['track_id'];plugin=clone.GetLayoutContext()['plugin_id']
        other=clone.CreatePlugin(layout,track,'Other Device')
        clone.SelectPlugin(layout,track,other);clone.AssignParameter('knob',1,effect.par.Power)
        other_catalog=clone.GetControlCatalog();manager.capture(force=True)
        clone.SelectPlugin(layout,track,plugin)
        m.par.Controller=clone;m.Sync();m.Flush();key=m.ActiveContext()
        v=views[0];u=v.ext.InspectorView;u.style='below'
        def select_filter(choice):
            details=dict(context=key,generation=u._menu_generation,choices={'choice':choice})
            return u.SelectFilter(dict(details=details,item='choice'))
        assert select_filter('comp:'+holder.path)
        assert u._visible_slots()==(0,) and u._rows.height==26
        assert clone.GetLayoutContext()['key']==key and clone.GetControlCatalog()[0]['id']==first
        assert select_filter('callbacks') and u._visible_slots()==() and u._rows.height==1
        assert select_filter('all') and u._visible_slots()==tuple(range(16))
        stale=dict(context=key,generation=u._menu_generation-1,choices={'choice':'callbacks'})
        assert not u.SelectFilter(dict(details=stale,item='choice'))
        original_counts=tuple(len(e.children) for e in u._editors)
        v.Action('slot0');v.Action('details_toggle')
        assert u._details_open and u._editors[0].height==402
        details=u._editors[0].op('container_details/text_details').par.text.eval()
        assert first in details and holder.path+'.Amount' in details and 'Follow  OFF' in details
        viewport=u._editors[0].op('container_details/container_readout')
        viewport.op('scroll_wheel').module.onValueChange(type('Wheel',(),dict(val=-1))(),0)
        assert viewport.panel.scrollv.val>0
        v.Action('details_toggle');v.Action('details_toggle')
        assert viewport.panel.scrollv.val==0
        snapshot=u._diagnostics
        ext._host.rx+=1;ext._host._sync();ext._publish();m.Sync();m.Flush()
        assert u._diagnostics is snapshot  # Counters are sampled only on open/Refresh.
        assert v.Action('details_refresh') and u._diagnostics is not snapshot
        manager.locked=True;m.Sync();m.Flush()
        assert m.Status['Locked'] and 'LOCK / Gate  ON / OFF' in u._editors[0].op('container_details/text_details').par.text.eval()
        manager.locked=False
        clone.par.Followcomp=True;m.Sync();m.Flush()
        assert not v.Action('details_reveal') and pane.owner==original_owner
        assert 'Turn off controller Follow' in u._error
        clone.par.Followcomp=False;m.Sync();m.Flush()
        # Reveal + restore happen in this one TD call; no global Follow tick intervenes.
        assert v.Action('details_reveal') and pane.owner==holder
        pane.owner=original_owner
        assert clone.GetLayoutContext()['key']==key
        assert v.Action('details_repair') and u._picker and not u._details_open
        v.Action('picker_cancel');v.Action('details_toggle');v.Action('mapping_toggle')
        assert not u._details_open and u._mapping.open
        v.Action('mapping_cancel');v.Action('details_toggle');v.CloseEditor()
        assert tuple(len(e.children) for e in u._editors)==original_counts
        assert not u._editors[0].op('container_details/text_details').par.text.eval()
        # Confirmation always includes the entire active registration catalog, independent of filter.
        assert select_filter('comp:'+holder.path)
        confirmation=m.PrepareClearDevice(key);assert set(confirmation['ids'])=={first,second}
        holder.par.Amount=.42;ext.onTargetValueChange(holder.par.Amount,.37);m.Sync();m.Flush()
        assert m.PrepareClearDevice(key)==confirmation
        # Exercise the actual native confirmation menu before invoking Cancel.
        assert u.RequestClearDevice()
        op.TDResources.op('popMenu').ext.PopMenuExt.CloseAll()
        request=u._clear_device_request
        label='Clear 2 registrations · '+' / '.join(dict(m.Choices(n,key))[key[i]] for i,n in enumerate(('Layout','Track','Device')))
        d=dict(request=request,generation=u._menu_generation,label=label)
        assert not u.ConfirmClearDevice(dict(details=d,item='Cancel'))
        assert set(r['id'] for r in clone.GetControlCatalog())=={first,second}
        # A definition change while confirmation is pending expires it.
        confirmation=m.PrepareClearDevice(key);clone.ConfigureControl(first,minimum=0,maximum=2)
        try:m.ClearDevice(key,confirmation);raise AssertionError('Stale config accepted')
        except ValueError:pass
        ext._host.learning=True;ext._host._sync();ext._publish();m.Sync();m.Flush()
        try:m.PrepareClearDevice(key);raise AssertionError('LEARN accepted')
        except ValueError:pass
        ext._host.learning=False;ext._host.controls[('knob',1)].touched=True;ext._host._sync();ext._publish();m.Sync();m.Flush()
        try:m.PrepareClearDevice(key);raise AssertionError('Touch accepted')
        except ValueError:pass
        ext._host.controls[('knob',1)].touched=False;ext._host._sync();ext._publish();m.Sync();m.Flush()
        try:m.PrepareClearDevice((layout,track,other));raise AssertionError('Inactive Device accepted')
        except ValueError:pass
        # Inject an interruption after first removal and verify honest partial result.
        confirmation=m.PrepareClearDevice(key);remove=ext.RemoveControl;calls=[]
        def partial(id):
            calls.append(id)
            if len(calls)>1:raise RuntimeError('Fixture removal interrupted')
            return remove(id)
        ext.RemoveControl=partial
        try:answer=m.ClearDevice(key,confirmation)
        finally:ext.RemoveControl=remove
        assert len(answer['removed'])==1 and len(answer['remaining'])==1 and answer['error']=='Fixture removal interrupted',answer
        remaining=m.PrepareClearDevice(key)
        request=v.op('parity').module.ClearRequest(remaining);u._clear_device_request=request
        d=dict(request=request,generation=u._menu_generation,label='Confirm fixture')
        assert u.ConfirmClearDevice(dict(details=d,item='Confirm fixture')),u._device_message
        assert not u.ConfirmClearDevice(dict(details=d,item='Confirm fixture'))
        m.Flush()  # Registration publication normally arrives at frame end.
        assert not clone.GetControlCatalog() and holder.par.Amount.eval()==.42 and effect.par.Power.eval()==.61
        assert 'Removed 1' in u._device_message and u._filter=='all',repr((u._device_message,u._filter))
        clone.SelectPlugin(layout,track,other)
        assert clone.GetControlCatalog()==other_catalog
        callback=holder.copy(production,name='callback_controller');callback.Disconnect();callback.par.Followcomp=False
        callback.op('registration').text="""def onRegister(controller):
    def changed(event):controller.store('fixture_events',controller.fetch('fixture_events',[])+[event])
    return controller.BindControls([dict(kind='button',slot=1,id='fixture.callback',label='Callback',mode='toggle',button_type='toggle',on_change=changed)],group_id='parity.callback.fixture')
"""
        callback.par.Setupmode='callback';assert callback.Applybinding();callback.store('fixture_events',[])
        m.par.Controller=callback;m.Sync();m.Flush();key=m.ActiveContext()
        assert select_filter('callbacks') and u._visible_slots()==(8,)
        v.Action('slot8');v.Action('details_toggle')
        assert 'Python callback' in u._editors[0].op('container_details/text_details').par.text.eval()
        assert not u._editors[0].op('container_details/reveal').par.enable.eval()
        assert not v.Action('details_reveal') and pane.owner==original_owner
        confirmation=m.PrepareClearDevice(key);assert confirmation['ids']==('fixture.callback',)
        assert m.ClearDevice(key,confirmation)==dict(removed=('fixture.callback',),remaining=(),error='')
        assert not callback.fetch('fixture_events')
        result.update(native_build=str(app.build),comp_callback_all_filters_readonly=True,stale_filter_callback_rejected=True,
                      details_fixed_section_reused=True,stable_id_target_health_display=True,diagnostics_counters_on_demand=True,
                      controller_follow_lock_state=True,reveal_existing_pane_and_follow_guard=True,repair_reuses_picker=True,
                      clear_confirmation_full_active_catalog=True,clear_cancel_and_repeat_guard=True,live_value_does_not_expire=True,
                      config_learn_touch_inactive_guards=True,partial_failure_exact_ids=True,other_device_and_target_values_preserved=True,
                      native_callback_filter_details_clear_without_dispatch=True)
    finally:
        pane.owner=original_owner
        for v,style in zip(views,styles):
            u=v.ext.InspectorView;u.style=style;u._filter='all';u._clear_device_request=None;u._device_message=''
            v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        m.par.Controller=production;m.Sync();m.Flush()
        if clone:clone.Disconnect()
        if callback:callback.Disconnect()
        holder.destroy()
    assert production.GetControlCatalog()==before and production.fetch('layout_registry')==registry
    assert production.GetLayoutContext()['key']==routing and m.ext.InspectorModel.adapter.Session()==session
    assert m.Stats()['subscribers']==2 and not m.Stats()['subscriber_errors']
    assert not any(o.errors(recurse=True) for o in [m]+views)
    result.update(production_catalog_registry_routing_session_preserved=True,subscribers=2,errors='')
    Path(project.folder+'/prototypes/inspector/parity_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

verify()
