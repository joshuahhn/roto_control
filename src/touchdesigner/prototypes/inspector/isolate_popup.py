"""Break Popup/main panel ancestry; reuse the existing native Window COMP."""
from pathlib import Path
views=globals().get('isolate_views',[op('/inspector_below'),op('/inspector_popup')])
for view in views:
    if not view:continue
    window=view.op('window_editor');ui=view.ext.InspectorView
    selected=ui.selected;was_open=window.isOpen
    host=ui._popup_host
    width,height=host.width,host.height
    x,top=window.x,window.y+window.height
    ui.CloseEditor();ui.Disconnect();window.par.winclose.pulse()
    root=view.op('base_popup') or view.create(baseCOMP,'base_popup')
    root.viewer=root.display=True;root.nodeX=0;root.nodeY=-320;root.nodeWidth=160;root.nodeHeight=130
    old=view.op('editor_popup')
    if old:
        assert root.op('editor_popup') is None,'Refuse to duplicate a Popup host'
        host=root.copy(old,name='editor_popup');old.destroy()
    else:host=root.op('editor_popup')
    host.par.display=True;host.nodeX=0;host.nodeY=0;host.nodeWidth=160;host.nodeHeight=130
    host.par.w=width;host.par.h=height
    window.par.winop.expr="parent.InspectorDemo.op('base_popup/editor_popup')"
    window.par.winw=width;window.par.winh=height
    view.op('ui').text=Path(project.folder+'/prototypes/inspector/ui.py').read_text();view.initializeExtensions(0)
    if selected is not None:view.Action('slot'+str(selected))
    if was_open:
        border=window.height-window.contentHeight
        window.par.winoffsetx=x;window.par.winoffsety=top-height-border;window.par.winopen.pulse()
    elif window.isOpen:window.par.winclose.pulse()
    print(view.path,'Popup isolated:',host.path,'existing window retained')
