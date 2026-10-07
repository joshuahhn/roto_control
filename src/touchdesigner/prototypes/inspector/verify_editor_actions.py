"""Live TD verification with a disconnected clone and captured protocol output."""
from pathlib import Path
import copy
import json

def verify():
    production=op('/roto_control_python/roto_python')
    model=op('/inspector_model');views=[op('/inspector_below'),op('/inspector_popup')]
    before=production.GetControlCatalog();registry=copy.deepcopy(production.fetch('layout_registry'))
    session=model.ext.InspectorModel.adapter.Session()
    holder=production.parent().create(baseCOMP,'base_inspector_action_verification')
    holder.viewer=True;holder.nodeX=700;holder.nodeY=-500
    page=holder.appendCustomPage('Fixture');page.appendFloat('Amount');page.appendPulse('Trigger')
    holder.par.Amount=.37
    clone=None
    try:
        clone=holder.copy(production,name='controller');clone.Disconnect();clone.par.Followcomp=False
        clone.Applybinding()
        layout=clone.CreateLayout('Inspector actions fixture');clone.SelectLayout(layout)
        knob=clone.AssignParameter('knob',2,holder.par.Amount)
        clone.AssignParameter('button',1,holder.par.Trigger,button_type='push')
        ext=clone.ext.RotoPythonExt;packets=[]
        ext._host.send=lambda message:packets.append(list(message))
        ext._host.connected=ext._host.plugin=True;ext._layout_manager().confirmed=True
        ext._host._sync();ext._publish()
        assert ext._process is None
        model.par.Controller=clone;model.Sync();model.Flush()
        key=model.ActiveContext();token=model.GetToken(key,1)
        assert not model.Info(key,1)['mapped']
        try:model.Ping(key,1,token)
        except ValueError:pass
        else:raise AssertionError('Ping without hardware LEARN accepted')
        assert not packets
        ext._host.learning=True;ext._host._sync();ext._publish()
        assert model.Ping(key,1,token)
        assert any(packet[5:7]==[11,10] for packet in packets),packets
        assert holder.par.Amount.eval()==.37
        assert not model.Info(key,1)['mapped']  # No synthetic hardware acknowledgement.
        ext._host.learning=False;ext._host._sync();ext._publish();model.Sync();model.Flush()
        view=views[0];ui=view.ext.InspectorView
        original_style=ui.style;ui.style='below'  # Exercise without opening a Popup.
        try:
            view.Action('slot1')
            editor=view.op('container_scroll/container_content/editor_below')
            editor.op('click_clear').module.onOffToOn(None)
            assert len(clone.GetControlCatalog())==2
            assert editor.op('clear/text_label').par.text.eval()=='?'
            editor.op('click_clear').module.onOffToOn(None)
            assert [state['kind'] for state in clone.GetControlCatalog()]==['button']
            assert holder.par.Amount.eval()==.37
            # Pulse Ping sends metadata, without pulsing the target or assigning Value.
            ext._host.learning=True;ext._host._sync();ext._publish();model.Sync();model.Flush()
            view.Action('slot8')
            popup=view.op('editor_popup');popup.op('click_ping').module.onOffToOn(None)
            assert 'awaiting hardware ACK' in ui._error
            assert holder.par.Trigger.eval()==0 and holder.par.Amount.eval()==.37
            ext._host.learning=False;ext._host._sync();ext._publish()
        finally:
            ui.style=original_style;view.CloseEditor()
        result=dict(native_build=str(app.build),ping_without_learn_rejected=True,
                    forgotten_map_metadata_offer=True,offer_not_claimed_as_ack=True,
                    clear_native_callback_requires_confirmation=True,
                    clear_one_mapping_only=True,pulse_ping_no_action=True,
                    parameter_value_preserved=True,physical_ping_acceptance=False)
    finally:
        model.par.Controller=production;model.Sync();model.Flush()
        for view in views:view.CloseEditor();view.op('window_editor').par.winclose.pulse()
        if clone:clone.Disconnect()
        holder.destroy()
    assert production.GetControlCatalog()==before
    assert production.fetch('layout_registry')==registry
    assert model.ext.InspectorModel.adapter.Session()==session
    assert not model.errors(recurse=True)
    geometry=[]
    for view in views:
        assert not view.errors(recurse=True)
        for editor in (view.op('container_scroll/container_content/editor_below'),view.op('editor_popup')):
            ping=editor.op('ping');clear=editor.op('clear');heading=editor.op('text_heading')
            # Closed/hidden panels report zero layout coordinates; inspect expressions.
            px=ping.par.x.eval();cx=clear.par.x.eval()
            assert heading.par.x.eval()+heading.par.w.eval()+6<=px
            assert px+ping.par.w.eval()+6<=cx and cx+clear.par.w.eval()<=editor.width-12
            assert ping.par.y.eval()==clear.par.y.eval()==148 and ping.par.w.eval()==clear.par.w.eval()==24 and editor.height==178
            cancel=editor.op('cancel');apply=editor.op('apply');status=editor.op('text_status')
            assert cancel.par.y.eval()==apply.par.y.eval()==status.par.y.eval()==6
            assert status.par.x.eval()+status.par.w.eval()+6<=cancel.par.x.eval()
            for upper,lower in [('ping','field_Label'),('field_Label','field_Destination'),('field_Destination','field_Minimum'),('field_Minimum','field_Value'),('field_Value','apply')]:
                assert editor.op(upper).par.y.eval()-editor.op(lower).par.y.eval()-editor.op(lower).par.h.eval()==6
            children=list(editor.children)
            for i,a in enumerate(children):
                for b in children[i+1:]:
                    assert a.nodeX+a.nodeWidth<=b.nodeX or b.nodeX+b.nodeWidth<=a.nodeX or a.nodeY+a.nodeHeight<=b.nodeY or b.nodeY+b.nodeHeight<=a.nodeY
            geometry.append(dict(editor=editor.path,width=editor.width,height=editor.height,ping_x=px,clear_x=cx))
    result.update(production_catalog_registry_session_preserved=True,errors='',geometry=geometry)
    Path(project.folder+'/prototypes/inspector/editor_actions_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

verify()
