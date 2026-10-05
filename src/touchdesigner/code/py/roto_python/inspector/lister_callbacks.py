"""External Lister callbacks: confirmations, enum menus and target edits."""
def onClick(info):
    if info.get('row',0) <= 0:
        return
    if info.get('colName') in ('COMP','Parameter'):
        open_assignment(info)
        return
    id = info.get('rowData',{}).get('ID')
    if not id:
        return
    inspector = parent.RotoInspector
    module = inspector.op('inspector_data').module
    if info.get('colName') == 'Learn':
        module.offer(inspector,id)
        return
    if info.get('colName') == 'Mode' and info['rowData']['Control'].startswith('Button'):
        state=inspector.parent().GetControlState(id)
        op.TDResources.op('popMenu').Open(
            items=['Toggle','Pulse'], callback=onModeSelect,
            callbackDetails=dict(inspector=inspector,id=id,mode=state['mode']),
            checkedItems=[state['mode'].capitalize()],
            disabledItems=['Pulse'] if state.get('parameter_style')=='Toggle' else ['Toggle'] if state.get('parameter_style')=='Pulse' else [], autoClose=1)
        return
    if info.get('colName') != 'ClearLearn':
        return
    pending = inspector.fetch('pending_clear',None)
    if pending and pending['id'] == id:
        hit = inspector.fetch('clear_hit',None)
        if hit and hit[:2] == (info['row'],info['col']):
            choice=module.confirmation_choice(hit[2])
            if choice is not None:
                module.confirm_clear(inspector,choice,id)
    else:
        module.request_clear(inspector,id)


def onModeSelect(info):
    if info.get('item') not in ('Toggle','Pulse'):
        return
    details=info['details']
    inspector=details['inspector']
    if inspector is None or not inspector.valid:
        return
    inspector.op('inspector_data').module.edit(inspector,details['id'],'Mode',info['item'])


def onEditEnd(info):
    if info.get('row',0) <= 0 or info.get('colName') not in ('Min','Max','Hardware','Value'):
        return
    inspector = parent.RotoInspector
    inspector.op('inspector_data').module.edit(inspector,info['rowData']['ID'],info['colName'],info['text'])


def onInitCell(info):
    if info.get('row',0)<=0:
        return
    if info.get('colName') in ('COMP','Parameter'):
        info['attribs'].text=info.get('cellText','')+' \u25be'
    if not info.get('rowData',{}).get('ID'):
        info['attribs'].editable=0
        return
    if info.get('colName')=='ClearLearn' and '[ Yes ]' in info.get('cellText',''):
        info['attribs'].text=''
        info['attribs'].top=parent.RotoInspector.op('listerConfig/null_confirm')
    if 'Needs re-LEARN' in info.get('rowData',{}).get('Error',''):
        info['ownerComp'].SetCellOverlay(info['row'],info['col'],(.9,.55,.12,.28))
    button = info['rowData']['Control'].startswith('Button')
    if (button and info['colName'] in ('Min','Max') or not button and info['colName'] in ('Mode','Hardware')
            or info['colName']=='Value' and info['rowData']['Mode']=='pulse'):
        info['attribs'].editable=0
    if button and info['colName']=='Mode':
        info['attribs'].text=info['rowData']['Mode'].capitalize()+' \u25be'


def onDoubleClick(info):
    # Clear is handled exactly once per native release in list_events.
    if info.get('colName') not in ('ClearLearn','Learn','COMP','Parameter'):
        onClick(info)


def open_assignment(info):
    inspector = parent.RotoInspector
    module = inspector.op('inspector_data').module
    control = info['rowData']['Control'].split()
    kind, slot = control[0].lower(), int(control[1])
    if info['colName'] == 'Parameter':
        path = info['rowData'].get('COMP','')
        comp = inspector.parent().op(path)
        if comp is not None and comp.valid and comp.isCOMP:
            open_parameters(inspector,kind,slot,comp)
            return
    comps = module.available_components(inspector,kind)
    if not comps:
        inspector.store('action_status','No compatible custom parameters found')
        module.refresh(inspector,inspector.parent().GetControlCatalog())
        return
    op.TDResources.op('popMenu').Open(items=[comp.path for comp in comps], callback=onComponentSelect,
        callbackDetails=dict(inspector=inspector,kind=kind,slot=slot,comps={comp.path:comp for comp in comps}),autoClose=1)


def onComponentSelect(info):
    details = info['details']
    inspector = details['inspector']
    if inspector is None or not inspector.valid:
        return
    comp = details['comps'].get(info.get('item'))
    if comp is not None and comp.valid:
        # Defer so closing the COMP menu cannot close the parameter menu.
        run('args[0](args[1],args[2],args[3],args[4])',open_parameters,inspector,details['kind'],details['slot'],comp,delayFrames=1)


def open_parameters(inspector,kind,slot,comp):
    if not inspector.valid or not comp.valid:
        return
    parameters = inspector.op('inspector_data').module.eligible_parameters(inspector,comp,kind)
    if not parameters:
        return
    choices={parameter.label+' ('+parameter.name+')':parameter for parameter in parameters}
    op.TDResources.op('popMenu').Open(items=list(choices),callback=onParameterSelect,
        callbackDetails=dict(inspector=inspector,kind=kind,slot=slot,parameters=choices),autoClose=1)


def onParameterSelect(info):
    details = info['details']
    inspector = details['inspector']
    if inspector is None or not inspector.valid:
        return
    parameter = details['parameters'].get(info.get('item'))
    if parameter is not None:
        inspector.op('inspector_data').module.assign(inspector,details['kind'],details['slot'],parameter)
