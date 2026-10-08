"""Install only Inspector activation; do not reinitialize the MIDI controller."""
from pathlib import Path
import copy,json
p=Path(project.folder)/'prototypes/inspector'
m=op('/inspector_model');c=m.par.Controller.eval();views=[op('/inspector_below'),op('/inspector_popup')]
assert c and c.State['Connected'] and not c.State['Learning'] and not c.State['Touched']
before=c.GetControlCatalog();registry=copy.deepcopy(c.fetch('layout_registry'));pid=c.ext.RotoPythonExt._process.pid
for v in views:v.CloseEditor();v.Disconnect()
exec((p/'build_commands.py').read_text(),dict(globals()))
m.op('live_model').text=(p/'live_model.py').read_text();m.initializeExtensions(0)
exec((p/'build_activation.py').read_text(),dict(globals()))
for v in views:
    v.op('ui').text=(p/'ui.py').read_text();v.initializeExtensions(0)
m.Sync();m.Flush()
assert c.GetControlCatalog()==before and c.fetch('layout_registry')==registry and c.ext.RotoPythonExt._process.pid==pid
assert m.Stats()['subscribers']==2
assert not any(x.errors(recurse=True) for x in [c,m]+views)
print('Activation installed; controller catalog/registry/process preserved, two subscribers')
