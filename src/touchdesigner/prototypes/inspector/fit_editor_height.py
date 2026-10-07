"""Fit existing Popup windows to content once; retain free manual resizing."""
views=globals().get('fit_views',[op('/inspector_below'),op('/inspector_popup')])
for view in views:
    if not view:continue
    ui=view.ext.InspectorView;ui.CloseContextMenu()
    popup=view.op('window_editor');host=view.op('ui').module.popup_host(view)
    height=int(ui._editors[1].height)
    width=popup.contentWidth if popup.isOpen else host.width
    if popup.isOpen:
        x,y=popup.x,popup.y
        delta=height-popup.contentHeight
        # Opening Width can be stale after a manual resize. Synchronize it
        # before changing offsets, and never pulse Open on an existing window.
        popup.par.winw=width
        popup.par.justifyoffsetto='primarydisplay';popup.par.justifyh='left';popup.par.justifyv='bottom'
        popup.par.winoffsetx=x;popup.par.winoffsety=y-delta
    popup.par.winw=width;popup.par.winh=height
    ui._popup_size_pending=not popup.isOpen
    if not popup.isOpen:host.par.h=height
    print(view.path,'fitted editor:',int(width),height)
