"""Native assignment/typed Value fixture; no production mapping/value/MIDI edits."""
from pathlib import Path
import copy,json

def verify():
    m=op('/inspector_model');production=m.par.Controller.eval()
    before=production.GetControlCatalog();registry=copy.deepcopy(production.fetch('layout_registry'))
    session=m.ext.InspectorModel.adapter.Session()
    views=[op('/inspector_below'),op('/inspector_popup')]
    styles=[v.ext.InspectorView.style for v in views]
    holder=production.parent().create(baseCOMP,'base_inspector_target_verification');holder.viewer=True
    holder.nodeX=700;holder.nodeY=-500
    page=holder.appendCustomPage('Fixture')
    for name in ('Amount','Other','Alternate','Master','Alias','Readonly','Expression','Temporary','Replacement','Learned'):page.appendFloat(name)
    page.appendInt('Count');page.appendToggle('Enabled');page.appendPulse('Trigger')
    choice=page.appendMenu('Choice')[0];choice.menuNames=['a','b','c'];choice.menuLabels=['A','Same','Same'];choice.val='a'
    holder.par.Amount=.37;holder.par.Other=.61;holder.par.Alternate=.22;holder.par.Master=.48
    holder.par.Replacement=.41;holder.par.Learned=.58
    holder.par.Count=2;holder.par.Count.normMax=7
    holder.par.Readonly.readOnly=True;holder.par.Expression.expr='0.5'
    holder.par.Alias.bindExpr="op(%r).par.Master"%holder.path
    clone=None
    result={}
    try:
        for v in views:v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        clone=holder.copy(production,name='controller');clone.Disconnect();clone.par.Followcomp=False;clone.Applybinding()
        clone.SelectLayout(clone.CreateLayout('Target fixture'))
        ids={}
        for kind,slot,name in [('knob',1,'Amount'),('knob',2,'Count'),('knob',4,'Other'),('button',1,'Choice'),('button',2,'Enabled'),('button',3,'Trigger')]:
            ids[name]=clone.AssignParameter(kind,slot,holder.par[name])['id']
        m.par.Controller=clone;m.Sync();m.Flush();key=m.ActiveContext()
        targets=m.op('base_targets').ext.InspectorTargets
        def drain():
            for _ in range(1000):
                if not targets.jobs:return
                for identity,job in list(targets.jobs.items()):
                    if job['pending']:job['pending'].kill()
                    targets._step(identity,job['serial'])
            raise AssertionError('Discovery failed to finish')
        found=[];targets.Start('fixture',holder.path,'knob',lambda rows,*args:found.extend(rows));drain()
        by_name={row['name']:row for row in found}
        assert all(by_name[name]['reason'] for name in ('Readonly','Expression','Trigger','Enabled'))
        assert not by_name['Alias']['reason']
        assert all(not r['path'].startswith(clone.path) for r in found)
        # Picker selection/search/cancel is read-only; empty slot Assign is explicit.
        v=views[0];u=v.ext.InspectorView;u.style='below';v.Action('slot4');v.Action('target_picker');drain()
        draft=v.op('base_draft');draft.par.Pickscope=holder.path;u.SearchTargets();drain()
        baseline=clone.GetControlCatalog();vals=lambda:tuple(holder.par[n].eval() for n in ('Amount','Count','Other','Alternate','Master','Enabled','Trigger','Choice'))
        values=vals();u.PickerQuery('Alternate');assert len(u._picker['visible'])==1
        assert v.Action('picker_row0');assert clone.GetControlCatalog()==baseline and vals()==values
        assert v.Action('picker_assign');assert not u._picker
        assigned=clone.GetControlCatalog();new=next(r for r in assigned if r['slot']==5 and r['kind']=='knob')
        assert new['parameter']=='Alternate' and vals()==values
        assert editor_height(u)==178
        # Other registration identities and current values survive assignment/retarget.
        unchanged=clone.GetControlState(ids['Other'])
        v.Action('slot0');v.Action('target_picker');drain();u.PickerQuery('Amount');v.Action('picker_row0')
        v.Action('picker_cancel');assert clone.GetControlCatalog()==assigned
        v.Action('slot5');v.Action('target_picker');drain();u.PickerQuery('Alternate');v.Action('picker_row0')
        snapshot=clone.GetControlCatalog();assert not v.Action('picker_assign');assert clone.GetControlCatalog()==snapshot
        assert 'cannot be bound twice' in u._picker['message'], u._picker['message']
        v.CloseEditor()
        # Compatible BIND assignment writes its master; duplicate ownership is controller-owned.
        m.Assign(key,6,by_name['Alias']['handle'],m.GetToken(key,6));m.Flush()
        v.Action('slot6');assert u.TypedValue(.65);assert holder.par.Master.eval()==.65
        snapshot=clone.GetControlCatalog()
        try:m.Assign(key,7,by_name['Master']['handle'],m.GetToken(key,7));raise AssertionError('Duplicate bind master accepted')
        except ValueError:pass
        assert clone.GetControlCatalog()==snapshot
        # A selected stale target cannot replace an existing registration.
        handle=by_name['Temporary']['handle'];holder.par.Temporary.destroy()
        try:m.Assign(key,7,handle,m.GetToken(key,7));raise AssertionError('Deleted target accepted')
        except ValueError:pass
        handle=by_name['Choice']['handle'];choice.menuLabels=['A','B','C']
        try:m.Assign(key,7,handle,m.GetToken(key,7));raise AssertionError('Changed Menu accepted')
        except ValueError:pass
        choice.menuLabels=['A','Same','Same']
        # Numeric input type cycles without writes, native Style/range changes or re-LEARN.
        v.Action('slot0');amount_state=clone.GetControlState(ids['Amount'])
        amount_type_callback=u._editors[0].op('click_value_type').module
        amount_type_callback.onOffToOn(None)
        assert u._value_type=='int' and u._editors[0].op('field_Value').par.type.eval()=='integer'
        assert holder.par.Amount.eval()==.37 and holder.par.Amount.style=='Float'
        assert clone.GetControlState(ids['Amount'])==amount_state
        u.BeginValueEdit();assert not u.LiveValue('.5');assert holder.par.Amount.eval()==.37
        assert u.LiveValue('1');assert holder.par.Amount.eval()==1
        u.EndValueEdit();clone.SetValue(.37,ids['Amount']);m.Sync();m.Flush()
        amount_type_callback.onOffToOn(None)
        assert u._value_type=='float' and u._editors[0].op('field_Value').par.type.eval()=='float'
        assert holder.par.Amount.eval()==.37 and clone.GetControlState(ids['Amount'])['requires_relearn']==amount_state['requires_relearn']
        # Real text callbacks + integer guard, typed Toggle and Menu with duplicate labels.
        v.Action('slot1');field=u._editors[0].op('field_Value');assert field.par.type.eval()=='integer'
        assert u._value_type is None  # A different slot defaults to its native type.
        assert v.Action('value_type') and u._value_type=='float'
        assert field.par.type.eval()=='float' and holder.par.Count.style=='Int'
        u.BeginValueEdit();assert not u.LiveValue('2.5') and holder.par.Count.eval()==2
        u.EndValueEdit();assert v.Action('value_type') and u._value_type=='int'
        field.par.callbacks.eval().module.onFocus(field)
        assert not u.LiveValue('2.5') and holder.par.Count.eval()==2
        field.par.callbacks.eval().module.onTextEditEnd(field,'4','2');assert holder.par.Count.eval()==4
        field.par.callbacks.eval().module.onFocusEnd(field,{})
        v.Action('slot9');assert u._editors[0].op('value_toggle').par.display.eval()
        assert v.Action('value_toggle');assert holder.par.Enabled.eval()
        v.Action('slot8');assert u._editors[0].op('value_menu').par.display.eval()
        schema=m.ValueSchema(key,8)
        details=dict(context=key,slot=8,token=u._token,generation=u._menu_generation,signature=(schema['names'],schema['labels']),choices={'Same [2]':2})
        assert u.SelectValueMenu(dict(details=details,item='Same [2]'));assert holder.par.Choice.menuIndex==2
        assert not u.SelectValueMenu(dict(details=details,item='Same [2]')), 'Repeated callback dispatched'
        clone.SetValue(0,ids['Choice']);m.Sync();m.Flush();assert u._editors[0].op('value_menu/text_label').par.text.eval()=='A ▾', repr((u._editors[0].op('value_menu/text_label').par.text.eval(),m.GetCatalog(key)[8]['Value']))
        schema=m.ValueSchema(key,8);details=dict(context=key,slot=8,token=u._token,generation=u._menu_generation,signature=(schema['names'],schema['labels']),choices={'Same [2]':2})
        choice.menuLabels=['A','B','C']
        assert not u.SelectValueMenu(dict(details=details,item='Same [2]')), 'Changed Menu callback dispatched';assert holder.par.Choice.menuIndex==0
        v.CloseEditor();choice.menuLabels=['A','Same','Same'];m.RefreshDefinitions();m.Sync();m.Flush()
        v.Action('slot10');assert not u._editors[0].op('value_menu').par.display.eval()
        assert not u._editors[0].op('value_toggle').par.display.eval()
        assert u._editors[0].op('field_Value').par.editmode.eval()=='selectonly'
        trigger_before=holder.par.Trigger.eval();assert not u.TypedValue(1);assert holder.par.Trigger.eval()==trigger_before
        # Replacing target detaches old Value observers while preserving unrelated control.
        v.CloseEditor();targets.Start('replace',holder.path,'knob',lambda rows,*args:found.extend(rows),True);drain()
        replacement=next(r for r in reversed(found) if r['name']=='Replacement')
        m.Assign(key,4,replacement['handle'],m.GetToken(key,4));m.Flush();m.RefreshWatchers()
        holder.par.Alternate=.77;clone.ext.RotoPythonExt.onTargetValueChange(holder.par.Alternate,.22);m.Sync();m.Flush()
        assert m.GetCatalog(key)[4]['Value']==.41
        assert clone.GetControlState(ids['Other'])==unchanged
        try:clone.SetValue(.9,new['id']);raise AssertionError('Old registration still accepts input')
        except ValueError:pass
        assert holder.par.Replacement.eval()==.41
        # Popup uses the same typed/picker sections without opening extra windows.
        popup=views[1];pu=popup.ext.InspectorView;pu.style='popup'
        popup.Action('slot8');assert pu._editors[1].op('value_menu').par.display.eval()
        popup.Action('target_picker');drain()
        assert pu._picker and len(pu._picker['visible'])<=6 and pu._editors[1].height==428
        popup.Action('picker_cancel');assert pu._editors[1].height==178
        # Session/reset invalidates handles even if the target still exists.
        targets.Reset()
        try:m.Assign(key,7,by_name['Learned']['handle'],m.GetToken(key,7));raise AssertionError('Expired handle accepted')
        except ValueError:pass
        current=[];targets.Start('learn',holder.path,'knob',lambda rows,*args:current.extend(rows));drain()
        learned=next(r for r in current if r['name']=='Learned')
        ext=clone.ext.RotoPythonExt;host=ext._host;packets=[];host.send=lambda packet:packets.append(tuple(packet))
        host.connected=host.plugin=host.learning=True;host._sync();ext._publish();m.Sync();m.Flush()
        offer_calls=[];original_offer=ext.Offerparameter
        def offer(id):offer_calls.append(id);return original_offer(id)
        ext.Offerparameter=offer
        learn_values=vals();answer=m.Assign(key,7,learned['handle'],m.GetToken(key,7));m.Flush()
        assert 'awaiting hardware ACK' in answer['message'] and packets and offer_calls==[answer['id']]
        assert not clone.GetControlState(answer['id'])['mapped'] and vals()==learn_values
        host.controls[('knob',8)].touched=True;host._sync();ext._publish();m.Sync();m.Flush()
        snapshot=clone.GetControlCatalog()
        try:m.Assign(key,7,learned['handle'],m.GetToken(key,7));raise AssertionError('Touched retarget accepted')
        except ValueError:pass
        assert clone.GetControlCatalog()==snapshot
        result.update(native_build=str(app.build),empty_slot_assignment=True,search_selection_cancel_readonly=True,
                      unsupported_readonly_expression_reasons=True,compatible_bind_alias_value=True,
                      duplicate_and_bind_master_isolation=True,deleted_changed_menu_expired_handle_guards=True,
                      numeric_type_cycle_no_write_or_style_change=True,native_int_fraction_guard_in_float_mode=True,native_integer_callbacks=True,menu_toggle_widgets_live=True,duplicate_menu_labels=True,
                      changed_menu_callback_fenced=True,pulse_readonly_no_action=True,
                      old_registration_and_value_observer_fenced=True,unaffected_control_preserved=True,
                      fold_popup_reuse_six_rows=True,learn_offers_once_without_claiming_ack=True,touch_guard=True)

    finally:
        for v,style in zip(views,styles):v.ext.InspectorView.style=style;v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        m.par.Controller=production;m.Sync();m.Flush()
        if clone:clone.Disconnect()
        holder.destroy()
    assert production.GetControlCatalog()==before and production.fetch('layout_registry')==registry
    assert m.ext.InspectorModel.adapter.Session()==session
    assert m.Stats()['subscribers']==2 and not m.Stats()['subscriber_errors']
    assert not any(o.errors(recurse=True) for o in [m]+views)
    result.update(production_catalog_registry_session_preserved=True,subscribers=2,errors='')
    Path(project.folder+'/prototypes/inspector/targets_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

def editor_height(view):return view._editors[0].height

verify()
