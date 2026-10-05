def onOffToOn(panelValue):
    inspector = parent.RotoInspector
    module = inspector.op('inspector_data').module
    name = panelValue.owner.name
    if name == 'page_select':
        op.TDResources.op('popMenu').Open(items=inspector.fetch('pages',[]),callback=onPageSelect,callbackDetails=inspector,checkedItems=[inspector.fetch('selected_page','All COMPs')])
    elif name == 'clear_all':
        module.request_clear(inspector,None)
    elif name in ('clear_all_yes','clear_all_no'):
        module.confirm_clear(inspector,name=='clear_all_yes',None)
    return


def onPageSelect(info):
    inspector=info['details']
    if info.get('item') and inspector is not None and inspector.valid:
        inspector.op('inspector_data').module.select_page(inspector,info['item'])
