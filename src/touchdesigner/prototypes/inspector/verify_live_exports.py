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
    for view in views:
        view.reload(project.folder+'/prototypes/inspector/'+view.name+'.tox');view.initializeExtensions(0)
        assert view.ext.InspectorView.Key()==('unconfigured',)*3
        assert all(not row['Destination'] for row in m.GetCatalog(view.ext.InspectorView.Key()))
        assert not view.op('base_draft').par.Destination.eval()
    assert m.Stats()['subscribers']==2
    result=dict(generic_reload=True,unconfigured_controller=True,no_saved_destinations=True,embedded_sources=True,subscribers=2)
finally:
    m.par.Controller=controller;m.Sync();m.Flush()
    for view in views:view.Connect();view.CloseEditor();view.op('window_editor').par.winclose.pulse()
    op('/inspector_below').Show()
assert controller.GetControlCatalog()==before
assert controller.State['Connected']
result['production_session_preserved']=True
Path(project.folder+'/prototypes/inspector/live_export_reload.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
