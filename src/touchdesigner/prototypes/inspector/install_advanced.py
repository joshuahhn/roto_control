"""Upgrade only Inspector sources/UI; retain real MIDI process and mappings."""
from pathlib import Path
import json

c=op('/roto_control_python/roto_python');m=op('/inspector_model')
assert m.par.Controller.eval()==c and c.State['Connected']
assert not c.State['Learning'] and not c.State['Touched']
assert not op('/base_inspector_acceptance')
before=c.GetControlCatalog();registry=c.fetch('layout_registry')
pid=c.ext.RotoPythonExt._process.pid;session=m.ext.InspectorModel.adapter.Session()
assert len(before)==6 and all(r['mapped'] and not r['requires_relearn'] for r in before)
u=op('/inspector_below').ext.InspectorView
record=dict(project=project.name,before=before,process_pid=pid,main=(u._main.contentWidth,u._main.contentHeight),
    popup=(u._popup.contentWidth,u._popup.contentHeight),selected=u.selected,mapping_open=u._mapping.open)
path=Path(project.folder+'/prototypes/inspector/advanced_install.json')
path.write_text(json.dumps(record,indent=2)+'\n')
exec(Path(project.folder+'/prototypes/inspector/build_live.py').read_text(),dict(globals()))
assert c.State['Connected'] and c.ext.RotoPythonExt._process.pid==pid
assert c.GetControlCatalog()==before and c.fetch('layout_registry')==registry
assert m.ext.InspectorModel.adapter.Session()==session and m.Stats()['subscribers']==2
assert not any(o.errors(recurse=True) for o in [c,m,op('/inspector_below'),op('/inspector_popup')])
record.update(installed=True,controller_catalog_registry_process_session_preserved=True,subscribers=2,errors=[])
path.write_text(json.dumps(record,indent=2)+'\n')
print('Advanced sources/UI installed; real controller/process/session unchanged')
