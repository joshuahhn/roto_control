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
    assert m.op('base_commands/InspectorCommands').text==Path(project.folder+'/prototypes/inspector/commands.py').read_text()
    for view in views:
        view.reload(project.folder+'/prototypes/inspector/'+view.name+'.tox');view.initializeExtensions(0)
        assert view.ext.InspectorView.Key()==('unconfigured',)*3
        assert all(not row['Destination'] for row in m.GetCatalog(view.ext.InspectorView.Key()))
        assert not view.op('base_draft').par.Destination.eval()
        assert not view.ext.InspectorView._mapping.open and view.ext.InspectorView._mapping.original is None
        assert view.op('base_draft').par.Mapminimum.eval()==0 and view.op('base_draft').par.Mapmaximum.eval()==1
        assert not view.op('base_draft').par.Mapmode.eval() and not view.op('base_draft').par.Mapinput.eval()
        assert view.op('editor_state').text==Path(project.folder+'/prototypes/inspector/editor_state.py').read_text()
        for editor in view.ext.InspectorView._editors:
            assert editor.op('field_Value').par.callbacks.eval().text==Path(project.folder+'/prototypes/inspector/value_callbacks.py').read_text()
            assert not editor.op('cancel').par.display.eval() and not editor.op('apply').par.display.eval()
        assert view.op('editor_popup').par.sizefromwindow.eval() and view.op('editor_popup').par.fixedaspect.eval()=='off'
    assert m.Stats()['subscribers']==2
    assert m.op('base_commands').Health(m.ActiveContext(),0)['code']=='unassigned'
    result=dict(generic_reload=True,unconfigured_controller=True,no_saved_destinations=True,embedded_sources=True,
                commands_embedded_and_promoted=True,definition_cache_empty=True,mapping_draft_empty=True,editor_state_embedded=True,live_value_callbacks_embedded=True,independent_native_resize=True,subscribers=2)
finally:
    m.par.Controller=controller;m.Sync();m.Flush()
    for view in views:view.Connect();view.CloseEditor();view.op('window_editor').par.winclose.pulse()
    op('/inspector_below').Show()
assert controller.GetControlCatalog()==before
assert controller.State['Connected']
result['production_session_preserved']=True
Path(project.folder+'/prototypes/inspector/live_export_reload.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
