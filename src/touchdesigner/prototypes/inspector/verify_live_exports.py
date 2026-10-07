"""Reload generic UI exports in place; production controller stays connected."""
from pathlib import Path
import json
m=op('/inspector_model');views=[op('/inspector_below'),op('/inspector_popup')]
controller=m.par.Controller.eval()
assert controller
before=controller.GetControlCatalog()
try:
    for view in views:view.Disconnect()
    m.reload(project.folder+'/prototypes/inspector/inspector_model.tox');m.initializeExtensions(0)
    assert m.par.Controller.eval() is None
    assert not m.Status['Connected']
    assert not m.ext.InspectorModel.adapter._definitions_cache
    assert m.op('base_targets').Stats()['entries']==0 and m.op('base_targets').Stats()['jobs']==0
    assert m.op('base_targets/TargetCatalog').text==Path(project.folder+'/prototypes/inspector/target_catalog.py').read_text()
    assert m.op('base_commands/InspectorCommands').text==Path(project.folder+'/prototypes/inspector/commands.py').read_text()
    assert m.op('base_commands/parity').text==Path(project.folder+'/prototypes/inspector/parity.py').read_text()
    for view in views:
        view.reload(project.folder+'/prototypes/inspector/'+view.name+'.tox');view.initializeExtensions(0)
        assert view.ext.InspectorView.Key()==('unconfigured',)*3
        assert all(not row['Destination'] for row in m.GetCatalog(view.ext.InspectorView.Key()))
        assert not view.op('base_draft').par.Destination.eval()
        assert not view.op('base_draft').par.Pickscope.eval() and not view.op('base_draft').par.Pickquery.eval()
        assert view.ext.InspectorView._picker is None
        assert view.ext.InspectorView._filter=='all' and view.ext.InspectorView._clear_device_request is None
        assert not view.ext.InspectorView._details_open and view.ext.InspectorView._diagnostics is None
        assert not view.ext.InspectorView._device_message
        assert view.op('parity').text==Path(project.folder+'/prototypes/inspector/parity.py').read_text()
        for name in ('Device','Layout','Track'):
            click=view.op('click_context_'+name)
            assert not click.par.offtoon.eval() and click.par.ontooff.eval()
            assert 'delayFrames' not in click.text and 'def onOnToOff' in click.text
            assert all(child.par.clickthrough.eval() for child in view.op('context_'+name).children if child.OPType=='textCOMP')
        assert view.op('context_menu').text==Path(project.folder+'/prototypes/inspector/context_menu.py').read_text()
        assert not view.op('context_menu').par.file.eval()
        assert view.ext.InspectorView._context_menu is None
        dropdown=view.op('container_context_menu')
        assert not dropdown.par.display.eval() and not dropdown.op('keyboard_escape').par.active.eval()
        assert not dropdown.op('base_footer/text_count').par.text.eval()
        assert all(not dropdown.op('row'+str(i)+'/text_label').par.text.eval() for i in range(8))
        assert all(not dropdown.op('row'+str(i)+'/text_check').par.display.eval() for i in range(8))
        assert not view.ext.InspectorView._mapping.open and view.ext.InspectorView._mapping.original is None
        assert view.op('base_draft').par.Mapminimum.eval()==0 and view.op('base_draft').par.Mapmaximum.eval()==1
        assert not view.op('base_draft').par.Mapmode.eval() and not view.op('base_draft').par.Mapinput.eval()
        assert view.op('editor_state').text==Path(project.folder+'/prototypes/inspector/editor_state.py').read_text()
        for editor in view.ext.InspectorView._editors:
            dropdown=editor.op('container_context_menu')
            assert not dropdown.par.display.eval() and not dropdown.op('keyboard_escape').par.active.eval()
            assert not dropdown.op('base_footer/text_count').par.text.eval()
            assert all(not dropdown.op('row'+str(i)+'/text_label').par.text.eval() for i in range(8))
            assert all(not dropdown.op('row'+str(i)+'/text_check').par.display.eval() for i in range(8))
            for host,name in ((editor,'value_menu'),(editor.op('container_mapping'),'choice_mode'),(editor.op('container_mapping'),'choice_input')):
                click=host.op('click_'+name)
                assert not click.par.offtoon.eval() and click.par.ontooff.eval() and 'delayFrames' not in click.text
            assert editor.op('field_Value').par.callbacks.eval().text==Path(project.folder+'/prototypes/inspector/value_callbacks.py').read_text()
            assert not editor.op('value_type').par.display.eval()
            assert not editor.op('value_type/text_label').par.text.eval()
            assert not editor.op('value_menu').par.display.eval() and not editor.op('value_toggle').par.display.eval()
            assert not editor.op('value_menu/text_label').par.text.eval()
            assert not editor.op('container_details/text_details').par.text.eval()
            content=editor.op('container_details/container_readout/container_info')
            assert content and all(not field.par.text.eval() for group in content.children if group.OPType=='containerCOMP' for field in group.children if field.OPType=='textCOMP' and field.name.startswith('value'))
            picker=editor.op('container_picker')
            assert not picker.op('text_status').par.text.eval()
            assert all(not picker.op('row'+str(i)+'/text_label').par.text.eval() for i in range(6))
            assert not editor.op('cancel').par.display.eval() and not editor.op('apply').par.display.eval()
        assert view.op('ui').module.popup_host(view).par.sizefromwindow.eval() and view.op('ui').module.popup_host(view).par.fixedaspect.eval()=='off'
        host=view.op('ui').module.popup_host(view)
        assert host.panelRoot==host and view.op('window_editor').par.winop.eval()==host
        assert host.height==178 and view.op('window_editor').par.winh.eval()==178
        assert view.ext.InspectorView._menu_extra==0 and view.ext.InspectorView._menu_window_extra==0
        assert view.ext.InspectorView._popup_geometry is None and view.ext.InspectorView._popup_geometry_settle is None
    assert m.Stats()['subscribers']==2
    assert m.op('base_commands').Health(m.ActiveContext(),0)['code']=='unassigned'
    result=dict(generic_reload=True,unconfigured_controller=True,no_saved_destinations=True,embedded_sources=True,
                targets_embedded_empty=True,picker_draft_empty=True,parity_embedded_empty=True,header_inline_embedded_empty=True,editor_inline_embedded_empty=True,commands_embedded_and_promoted=True,definition_cache_empty=True,mapping_draft_empty=True,editor_state_embedded=True,live_value_callbacks_embedded=True,independent_native_resize=True,subscribers=2)
finally:
    m.par.Controller=controller;m.Sync();m.Flush()
    for view in views:view.Connect();view.CloseEditor();view.op('window_editor').par.winclose.pulse()
    op('/inspector_below').Show()
assert controller.GetControlCatalog()==before
assert controller.State['Connected']
result['production_session_preserved']=True
Path(project.folder+'/prototypes/inspector/live_export_reload.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
