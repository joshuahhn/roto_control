"""Save generic compact UI components through TD; keep production MIDI open.

Temporarily detach only the Inspector's read adapter. Never alter controller
mappings or values. Exported UI has no saved target IDs, labels or destinations.
"""
from pathlib import Path
m=op('/inspector_model');views=[op('/inspector_below'),op('/inspector_popup')]
controller=m.par.Controller.eval()
saved=[dict(context=v.ext.InspectorView.Key(),follow=v.ext.InspectorView._follow_routing,filter=v.ext.InspectorView._filter) for v in views]
try:
    for v in views:
        v.CloseContextMenu();v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        # Same-frame close can leave Size From Window at its previous expanded
        # height. Generic closed editors must save their collapsed content size.
        host=v.ext.InspectorView._popup_host
        height=int(v.ext.InspectorView._editors[1].height)
        v.op('window_editor').par.winh=height;host.par.h=height
        v.ext.InspectorView._popup_size_pending=True
        v.ext.InspectorView._cancel_popup_geometry()
        for host in (v,)+v.ext.InspectorView._editors:
            dropdown=host.op('container_context_menu');dropdown.par.display=False
            dropdown.op('keyboard_escape').par.clear.pulse()
            dropdown.op('base_footer/text_count').par.text=''
            for i in range(8):
                dropdown.op('row'+str(i)+'/text_label').par.text=''
                dropdown.op('row'+str(i)+'/text_check').par.display=False
    m.par.Controller=None;m.Sync();m.Flush()
    for v in views:
        u=v.ext.InspectorView;u._filter='all';u._clear_device_request=None;u._device_message='';u._diagnostics=None
        for n,value in [('Label',''),('Destination',''),('Minimum',0),('Maximum',1),('Value',0)]:v.op('base_draft').par[n]=value
        for n,value in [('Mapminimum',0),('Mapmaximum',1),('Mapmode',''),('Mapinput',''),('Pickscope',''),('Pickquery','')]:
            if hasattr(v.op('base_draft').par,n):v.op('base_draft').par[n]=value
        v.Refresh()
        assert v.ext.InspectorView.Key()==('unconfigured',)*3
        assert all(not row['Destination'] for row in m.GetCatalog(v.ext.InspectorView.Key()))
    if m.op('base_targets'):m.op('base_targets').Reset()
    assert m.par.Controller.eval() is None
    for c in [m]+views:
        c.save(project.folder+'/prototypes/inspector/'+c.name+'.tox')
finally:
    m.par.Controller=controller;m.Sync();m.Flush()
    for v,s in zip(views,saved):
        u=v.ext.InspectorView;u._follow_routing=s['follow']
        if not s['follow'] and m.HasContext(s['context']):u.ConfigureMenus(s['context'])
        u._filter=s['filter']
        v.Refresh()
print('Generic exports saved; real controller adapter restored')
