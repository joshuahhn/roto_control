"""Install the verified optional UI projection change; reconnect existing MIDI.

Only two embedded DAT sources change. Force-capture the current registry before
extension reinitialization; preserve every binding identity, parameter and Value.
"""
from pathlib import Path
import copy,json
c=op('/inspector_model').par.Controller.eval()
assert c and c.State['Connected'] and not c.State['Learning'] and not c.State['Touched']
assert not op('/base_inspector_acceptance')
before=c.GetControlCatalog();context=c.GetLayoutContext()['key']
ext=c.ext.RotoPythonExt;ext._layouts.capture(force=True)
record=dict(before=before,context=context,project=project.name)
Path(project.folder+'/prototypes/inspector/projection_install.json').write_text(json.dumps(record,indent=2))
c.Disconnect()
c.op('inspector/inspector_data').text=Path(project.folder+'/code/py/roto_python/inspector/inspector_data.py').read_text()
c.op('RotoPythonExt').text=Path(project.folder+'/code/py/roto_python/RotoPythonExt.py').read_text()
c.initializeExtensions(0);c.Applybinding()
fields=('id','kind','slot','mode','label','minimum','maximum','button_type','binding_type','comp','parameter','value')
projected=lambda rows:[{k:r.get(k) for k in fields} for r in rows]
assert projected(c.GetControlCatalog())==projected(before)
assert tuple(c.GetLayoutContext()['key'])==tuple(context)
c.Connect()
print('Projection change installed; original binding metadata/Values retained; MIDI handshake pending')
