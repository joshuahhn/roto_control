"""Save generic compact UI components through TD; keep production MIDI open.

Temporarily detach only the Inspector's read adapter. Never alter controller
mappings or values. Exported UI has no saved target IDs, labels or destinations.
"""
from pathlib import Path
m=op('/inspector_model');views=[op('/inspector_below'),op('/inspector_popup')]
controller=m.par.Controller.eval()
saved=[dict(context=v.ext.InspectorView.Key(),follow=v.ext.InspectorView._follow_routing) for v in views]
try:
    for v in views:v.CloseEditor();v.op('window_editor').par.winclose.pulse()
    m.par.Controller=None;m.Sync();m.Flush()
    for v in views:
        for n,value in [('Label',''),('Destination',''),('Minimum',0),('Maximum',1),('Value',0)]:v.op('base_draft').par[n]=value
        v.Refresh()
        assert v.ext.InspectorView.Key()==('unconfigured',)*3
        assert all(not row['Destination'] for row in m.GetCatalog(v.ext.InspectorView.Key()))
    assert m.par.Controller.eval() is None
    for c in [m]+views:
        c.save(project.folder+'/prototypes/inspector/'+c.name+'.tox')
finally:
    m.par.Controller=controller;m.Sync();m.Flush()
    for v,s in zip(views,saved):
        u=v.ext.InspectorView;u._follow_routing=s['follow']
        if not s['follow'] and m.HasContext(s['context']):u.ConfigureMenus(s['context'])
        v.Refresh()
print('Generic exports saved; real controller adapter restored')
