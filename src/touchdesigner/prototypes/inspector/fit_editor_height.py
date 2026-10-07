"""Fit existing Popup windows to content once; retain free manual resizing."""
views=globals().get('fit_views',[op('/inspector_below'),op('/inspector_popup')])
for view in views:
    if not view:continue
    ui=view.ext.InspectorView;popup=view.op('window_editor');host=view.op('editor_popup')
    height=int(ui._editors[1].height)
    width=popup.contentWidth if popup.isOpen else host.width
    if popup.isOpen:
        delta=height-popup.contentHeight
        popup.par.justifyoffsetto='primarydisplay';popup.par.justifyh='left';popup.par.justifyv='bottom'
        popup.par.winoffsetx=popup.x;popup.par.winoffsety=popup.y-delta
    popup.par.winw=width;popup.par.winh=height
    ui._popup_size_pending=not popup.isOpen
    if popup.isOpen:popup.par.winopen.pulse()
    else:host.par.h=height
    print(view.path,'fitted editor:',int(width),height)
