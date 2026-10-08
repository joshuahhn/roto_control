"""Install verified synchronous publication source; retain all bindings/Values."""
from pathlib import Path
import json

c=op('/inspector_model').par.Controller.eval()
assert c and c.State['Connected'] and not c.State['Learning'] and not c.State['Touched']
assert not op('/base_inspector_acceptance')
assert not getattr(c.ext.RotoPythonExt,'_button_adapter_probe',None)
before=c.GetControlCatalog();context=c.GetLayoutContext()['key']
assert len(before)==6 and all(r['mapped'] and not r['requires_relearn'] for r in before)
c.ext.RotoPythonExt._layouts.capture(force=True)
path=Path(project.folder+'/prototypes/inspector/control_publication_install.json')
record=dict(project=project.name,before=before,context=context)
path.write_text(json.dumps(record,indent=2)+'\n')
c.Disconnect()
c.op('RotoPythonExt').text=Path(project.folder+'/code/py/roto_python/RotoPythonExt.py').read_text()
c.initializeExtensions(0);c.Applybinding()
fields=('id','kind','slot','mode','label','minimum','maximum','button_type','binding_type','comp','parameter','value')
rows=lambda catalog:[{k:r.get(k) for k in fields} for r in catalog]
assert rows(c.GetControlCatalog())==rows(before)
assert tuple(c.GetLayoutContext()['key'])==tuple(context)
c.Connect()
print('Synchronous publication installed; original binding metadata/Values retained; waiting for matching ACKs')
