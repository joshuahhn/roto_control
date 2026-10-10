"""Reload only Inspector sources; preserve production MIDI and native rectangles."""
from pathlib import Path
import json
m=op('/inspector_model');controller=m.par.Controller.eval()
before=controller.GetControlCatalog();session=m.ext.InspectorModel.adapter.Session()
views=(op('/inspector_below'),op('/inspector_popup'))
saved=[]
for v in views:
    u=v.ext.InspectorView;p=v.op('window_editor');host=u._popup_host
    saved.append(dict(style=u.style,main=v.op('window_main').isOpen,popup=p.isOpen,
                      selected=u.selected,mapping=u._mapping.open,message=u._mapping.message,
                      rect=(p.contentWidth if p.isOpen else host.width,
                            p.contentHeight if p.isOpen else host.height,p.x,p.y)))
    v.CloseEditor();p.par.winclose.pulse();v.Disconnect()
m.op('live_model').text=Path(project.folder+'/prototypes/inspector/live_model.py').read_text()
m.initializeExtensions(0)
for v,s in zip(views,saved):
    for name in ('editor_state','ui'):
        v.op(name).text=Path(project.folder+'/prototypes/inspector/'+name+'.py').read_text()
    v.initializeExtensions(0)
    u=v.ext.InspectorView;p=v.op('window_editor');width,height,x,y=s['rect']
    # A selected Mapping editor is 134px taller than its manual base.
    base=height-(134 if s['mapping'] and s['popup'] else 0)
    p.par.winw=width;p.par.winh=base;u._popup_host.par.w=width;u._popup_host.par.h=base
    u._popup_size_pending=True;u.style=s['style'];v.par.Presentation=s['style']
    if s['main']:v.Show()
    if s['selected'] is not None:v.Action('slot'+str(s['selected']))
    if s['mapping']:
        v.Action('mapping_toggle');u._mapping.message=s['message'];u._update_mapping()
    if not s['popup']:p.par.winclose.pulse()
    p.par.winoffsetx=x;p.par.winoffsety=y
assert controller.GetControlCatalog()==before
assert m.ext.InspectorModel.adapter.Session()==session and controller.State['Connected']
assert m.Stats()['subscribers']==2
assert not any(c.errors(recurse=True) for c in (m,)+views)
print('Inspector ACK status fix loaded; production catalog/session retained')
