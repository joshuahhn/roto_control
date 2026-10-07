"""Inspector projection, confirmation and validated controller API edits."""
COLUMNS = ('Control', 'Mapped', 'Learn', 'ClearLearn', 'COMP', 'Parameter', 'Mode', 'Hardware', 'Min', 'Max', 'Value', 'ID', 'Error')


def confirmation_choice(u):
    if 0 <= u < 73/150:
        return True
    if 77/150 <= u <= 1:
        return False
    return None


def fingerprint(states):
    return tuple((s['id'],s['kind'],s['slot'],s['comp'],s['parameter'],s['mode'],s['minimum'],s['maximum'],s['button_type'],s['connected'],s['plugin']) for s in states)


def context(inspector):
    parent=getattr(inspector,'parent',None)
    controller=parent() if parent is not None else None
    get_context=getattr(controller,'GetLayoutContext',None)
    return get_context() if get_context is not None else dict(key=None,label='')


def refresh(inspector, states):
    current=context(inspector)
    pending = inspector.fetch('pending_clear', None)
    if pending and (pending['fingerprint'] != fingerprint(states) or pending.get('context')!=current['key']):
        inspector.store('pending_clear', None)
        pending = None
    database=inspector.op('database')
    if database is not None:
        import json
        content=json.dumps(states,ensure_ascii=True,indent=2)+'\n'
        if database.text.replace('\r\n','\n')!=content:
            database.text=content
    pages=['All COMPs']+list(dict.fromkeys(state['comp'] or 'Python callbacks' for state in states))
    inspector.store('pages',pages)
    page=inspector.fetch('selected_page','All COMPs')
    if page not in pages:
        page='All COMPs';inspector.store('selected_page',page)
    page_button=inspector.op('page_select')
    if page_button is not None:
        page_button.par.label='Page: '+page+' v'
    rows = [list(COLUMNS)]
    by_slot={(state['kind'],state['slot']):state for state in states if page=='All COMPs' or (state['comp'] or 'Python callbacks')==page}
    for kind,slot in [(kind,slot) for kind in ('knob','button') for slot in range(1,9)]:
        state=by_slot.get((kind,slot))
        if state is None:
            rows.append([kind.capitalize()+' '+str(slot),'Unassigned','','','Choose COMP \u25be','Choose parameter \u25be','','','','','','',''])
            continue
        if page!='All COMPs' and (state['comp'] or 'Python callbacks')!=page:
            continue
        destination = state['comp'] or ('Python callback' if state['binding_type']=='callback' else 'Unavailable')
        parameter = state['parameter'] or '\u2014'
        value = (format(state['value'],'.3f').rstrip('0').rstrip('.') or '0') if state['value'] is not None else 'Unavailable'
        confirm = pending and pending['id'] == state['id']
        rows.append([state['kind'].capitalize()+' '+str(state['slot']),
                     'Invalid' if not state['valid'] else 'Yes' if state['mapped'] else 'No',
                     'Re-learn' if state['mapped'] or state.get('last_mapped') or state.get('requires_relearn') else 'Learn',
                     '[ Yes ]   [ No ]' if confirm else 'Clear', destination, parameter, state['mode'],
                     (state['button_type'] or '\u2014').upper(), format(state['minimum'],'.12g'), format(state['maximum'],'.12g'), value,
                     state['id'],' | '.join(part for part in (state['error'],'Needs re-LEARN' if state.get('requires_relearn') else '') if part)])
    content = '\n'.join('\t'.join(str(cell).replace('\t',' ').replace('\n',' ') for cell in row) for row in rows)+'\n'
    table = inspector.op('targets')
    if table.text.replace('\r\n','\n') != content:
        table.text = content
    pending_id = pending['id'] if pending else False
    if pending_id != inspector.fetch('visual_pending',False):
        inspector.store('visual_pending',pending_id)
        lister = inspector.op('lister')
        if lister is not None:
            lister.par.Refresh.pulse()
    highlights = tuple(state['id'] for state in states if state.get('requires_relearn'))
    if highlights != inspector.fetch('visual_relearn', ()):
        inspector.store('visual_relearn', highlights)
        lister = inspector.op('lister')
        if lister is not None:
            lister.par.Refresh.pulse()
    count = sum(state['mapped'] for state in states)
    status = inspector.fetch('action_status','Click Mode \u25be; double-click Min / Max / Hardware / Value')
    inspector.op('title').par.text = f"ROTO Inspector | {current['label']} | {count}/{len(states)} mapped | {status}"
    if current.get('locked'):
        inspector.op('title').par.text += ' | LOCK' + (' (selected Track differs)' if current.get('selected_track_id')!=current.get('track_id') else '')
    parent = getattr(inspector, 'parent', None)
    get_focus = getattr(parent() if parent is not None else None, 'GetCompContext', None)
    if get_focus is not None:
        focus = get_focus()
        inspector.op('title').par.text += ' | Follow ' + focus['status']
    for name, label in [('clear_all','Clear All'),('clear_all_yes','Yes'),('clear_all_no','No')]:
        button = inspector.op(name)
        if button is not None:
            button.par.display = bool(pending and pending['id'] is None) if name != 'clear_all' else not bool(pending and pending['id'] is None)


def request_clear(inspector, id):
    states = inspector.parent().GetControlCatalog()
    if id is not None and id not in [s['id'] for s in states]:
        raise ValueError('Unknown target ID: '+str(id))
    inspector.store('pending_clear',dict(id=id,fingerprint=fingerprint(states),context=context(inspector)['key']))
    inspector.store('action_status','Delete all bindings in current Plugin?' if id is None else 'Delete target '+id+'?')
    refresh(inspector,states)


def confirm_clear(inspector, yes, id):
    pending = inspector.fetch('pending_clear',None)
    states = inspector.parent().GetControlCatalog()
    if not pending or pending['id'] != id or pending['fingerprint'] != fingerprint(states) or pending.get('context')!=context(inspector)['key']:
        inspector.store('pending_clear',None)
        inspector.store('action_status','Confirmation expired; click Clear again')
        refresh(inspector,states)
        return False
    inspector.store('pending_clear',None)
    if not yes:
        inspector.store('action_status','Clear cancelled')
    else:
        try:
            if id is None:
                inspector.parent().RemoveAllControls()
            else:
                inspector.parent().RemoveControl(id)
            inspector.store('action_status','Removed: '+('all registered targets' if id is None else id))
        except Exception as exc:
            inspector.store('action_status','Cannot clear: '+str(exc))
    refresh(inspector,inspector.parent().GetControlCatalog())
    return bool(yes)


def edit(inspector, id, column, text):
    try:
        controller = inspector.parent()
        if column == 'Value':
            controller.SetValue(float(text),id=id)
        else:
            field = {'Min':'minimum','Max':'maximum','Mode':'mode','Hardware':'button_type'}[column]
            value = float(text) if column in ('Min','Max') else text.strip().lower()
            state=controller.ConfigureControl(id,**{field:value})
        inspector.store('action_status','Updated '+id+': '+column+(' \u2014 Needs re-LEARN' if column!='Value' and state['requires_relearn'] else ''))
    except Exception as exc:
        inspector.store('action_status','Cannot edit: '+str(exc))
    refresh(inspector,inspector.parent().GetControlCatalog())
    inspector.op('lister').par.Refresh.pulse()


def select_page(inspector, page):
    if page not in inspector.fetch('pages', []):
        raise ValueError('Unknown COMP page')
    inspector.store('selected_page',page)
    inspector.store('pending_clear',None)
    refresh(inspector,inspector.parent().GetControlCatalog())
    inspector.op('lister').par.Refresh.pulse()


def offer(inspector, id):
    """Send the row's registered metadata; hardware LEARN chooses the slot."""
    controller=inspector.parent()
    try:
        state=controller.GetControlState(id)
        slot=state['kind'].capitalize()+' '+str(state['slot'])
        if not state['connected'] or not state['plugin']:
            raise ValueError('Connect to PLUGIN first')
        if not state['valid']:
            raise ValueError(state['error'] or 'Target is invalid')
        if not controller.State['Learning']:
            raise ValueError('Open hardware LEARN, select '+slot+', then click Learn')
        if not controller.Offerparameter(id):
            raise ValueError('Offer rejected; check LEARN and target state')
        inspector.store('action_status','Offered '+slot+': '+state['label']+'; waiting for hardware acknowledgement')
        result=True
    except Exception as exc:
        inspector.store('action_status','Cannot learn: '+str(exc))
        result=False
    refresh(inspector,controller.GetControlCatalog())
    return result


def eligible_parameters(inspector, comp, kind):
    """Discover writable custom parameters on demand; no per-frame scanning."""
    if comp is None or not comp.valid or not comp.isCOMP or getattr(comp, 'OPType', '') == 'annotateCOMP':
        return []
    styles = ('Float','Int','Menu') if kind == 'knob' else ('Toggle','Pulse','Menu')
    controls = inspector.parent().op('controls').module.Controls
    result = []
    for parameter in comp.customPars:
        if parameter.style not in styles:
            continue
        mode = 'value' if kind == 'knob' else 'cycle' if parameter.style == 'Menu' else 'pulse' if parameter.style == 'Pulse' else 'toggle'
        try:
            controls([dict(kind=kind,slot=1,id='picker.check',parameter=parameter,mode=mode)])
        except (ValueError, TypeError, AttributeError):
            continue
        result.append(parameter)
    return result


def available_components(inspector, kind):
    controller = inspector.parent()
    root = controller.parent()
    stack = [root]
    result = []
    while stack:
        comp = stack.pop()
        if comp == controller or not comp.valid or not comp.isCOMP or getattr(comp, 'OPType', '') == 'annotateCOMP':
            continue
        if eligible_parameters(inspector, comp, kind):
            result.append(comp)
        stack.extend(child for child in comp.children if child.isCOMP)
    return sorted(result,key=lambda comp:comp.path.lower())


def assign(inspector, kind, slot, parameter):
    controller = inspector.parent()
    try:
        state = controller.AssignParameter(kind,slot,parameter)
        inspector.store('selected_page','All COMPs')
        inspector.store('pending_clear',None)
        if controller.State['Learning'] and state['connected'] and state['plugin']:
            return offer(inspector,state['id'])
        inspector.store('action_status','Assigned '+kind.capitalize()+' '+str(slot)+': '+state['label']+
                        '; open hardware LEARN, select this control, then click Learn')
        result = True
    except Exception as exc:
        inspector.store('action_status','Cannot assign: '+str(exc))
        result = False
    refresh(inspector,controller.GetControlCatalog())
    inspector.op('lister').par.Refresh.pulse()
    return result
