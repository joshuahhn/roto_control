"""Detached native parameter metadata; no setters, MIDI or UI side effects."""
MENU_PREVIEW=8
TEXT_LIMIT=2048

def text(value):
    if value is None:return '—'
    if isinstance(value,float):return format(value,'.9g')
    return str(value)[:TEXT_LIMIT]

def reference(value):
    if value is None:return ''
    owner=getattr(value,'owner',None)
    if owner is not None:return text(owner.path)+'.'+text(getattr(value,'name',''))
    return text(getattr(value,'path',value))

def native_rows(native):
    rows=[('Name / Page',native['label']+' · '+native['name']+'\nPage: '+native['page'],'long'),
          ('Native Style',native['style'],'short')]
    default=native['default']+' · '+native['default_mode']
    if native['default_mode']=='EXPRESSION':default+='\n'+native['default_expr']
    elif native['default_mode']=='BIND':default+='\n'+native['default_bind_expr']
    rows.append(('Default',default,'long' if '\n' in default else 'short'))
    if native['slider_range']:
        rows.append(('Slider range',' – '.join(native['slider_range']),'short'))
        rows.append(('Clamp limits','\n'.join(('Min '+native['clamp_limits'][0]+' · '+('ON' if native['clamps'][0] else 'OFF'),
                                               'Max '+native['clamp_limits'][1]+' · '+('ON' if native['clamps'][1] else 'OFF'))),'long'))
    evaluation=native['mode']+' · '+('read-only' if native['read_only'] else 'writable')+(' · disabled' if not native['enabled'] else '')
    if native['mode']=='EXPRESSION':evaluation+='\n'+native['expression']
    elif native['mode']=='BIND':
        evaluation+='\nMaster: '+(native['bind_master'] or 'unresolved')
        if native['resolved_master']!=native['bind_master']:evaluation+='\nResolved: '+native['resolved_master']
        evaluation+='\nRange: '+('inherited' if native['bind_range'] else 'local')
    elif native['mode']=='EXPORT':evaluation+='\nSource: '+(native['export_source'] or native['export_op'] or 'unresolved')
    rows.append(('Evaluation',evaluation,'long'))
    if native['menu_count'] or native['menu_source']:
        menu='\n'.join(str(i)+': '+label+' ['+name+']' for i,(name,label) in enumerate(native['menu_preview']))
        if native['menu_count']>MENU_PREVIEW:menu+='\n… '+str(native['menu_count']-MENU_PREVIEW)+' more · open Definition'
        if native['menu_source']:menu+='\nSource: '+native['menu_source']
        rows.append((native['menu_kind']+' · '+str(native['menu_count']),menu or 'No options','long'))
    return tuple(rows)

def snapshot(par):
    """Read definitions without evaluating/writing the live Value or firing Pulse."""
    if par is None or not par.valid:raise ValueError('Target unavailable; use Repair')
    master=par.bindMaster if par.mode.name=='BIND' else None
    resolved=master;seen=set()
    for _ in range(16):
        if resolved is None or not hasattr(resolved,'mode') or resolved.mode.name!='BIND':break
        key=reference(resolved)
        if key in seen:break
        seen.add(key);next_master=resolved.bindMaster
        if next_master is None:break
        resolved=next_master
    names=par.menuNames or ();labels=par.menuLabels or ()
    numeric=par.isNumber and not (par.isMenu or par.isToggle or par.isPulse)
    native=dict(name=text(par.name),label=text(par.label),page=text(par.page.name),style=text(par.style),
        default=text(par.default),default_mode=text(par.defaultMode.name),default_expr=text(par.defaultExpr),
        default_bind_expr=text(par.defaultBindExpr),mode=text(par.mode.name),read_only=bool(par.readOnly),enabled=bool(par.enable),
        expression=text(par.expr),bind_master=reference(master),resolved_master=reference(resolved),bind_range=bool(par.bindRange),
        export_op=reference(par.exportOP),export_source=reference(par.exportSource),
        slider_range=(text(par.normMin),text(par.normMax)) if numeric else (),
        clamp_limits=(text(par.min),text(par.max)) if numeric else (),clamps=(bool(par.clampMin),bool(par.clampMax)) if numeric else (),
        menu_count=len(names),menu_kind='Menu' if par.isMenu else 'States',
        menu_preview=tuple((text(name),text(labels[i] if i<len(labels) else name)) for i,name in enumerate(names[:MENU_PREVIEW])),
        menu_source=text(par.menuSource or '') if par.isMenu else '')
    target=dict(owner_id=par.owner.id,comp=text(par.owner.path),name=text(par.name),custom=bool(par.isCustom))
    return dict(target=target,native=native,rows=native_rows(native),reason='')

def unavailable(reason):return dict(target=None,native=None,rows=(('Target',reason,'long'),),reason=reason)

def editor_actions(definition,learning=False,touched=False):
    reason=definition['reason'] or ('Exit LEARN before opening native editors' if learning else
                                  'Release the control before opening native editors' if touched else '')
    custom=bool(definition.get('target') and definition['target']['custom'])
    return {kind:dict(enabled=not why,reason=why) for kind,why in
            [('values',reason),('definition',reason or ('' if custom else 'Definition editor requires a custom parameter'))]}

def read(info,resolve,learning=False,touched=False):
    if not info.get('parameter'):
        definition=unavailable('Python callback · no native parameter' if info.get('id') else 'Unassigned · choose a Target')
    else:
        try:definition=snapshot(resolve(info))
        except (ValueError,AttributeError,RuntimeError) as error:definition=unavailable(str(error) or 'Target unavailable; use Repair')
    definition['actions']=editor_actions(definition,learning,touched)
    return definition

def open_editor(info,kind,resolve,open_definition,learning=False,touched=False):
    if kind not in ('values','definition'):raise ValueError('Unknown native editor')
    definition=read(info,resolve,learning,touched);capability=definition['actions'][kind]
    if not capability['enabled']:raise ValueError(capability['reason'])
    par=resolve(info)
    if par is None or not par.valid or (par.owner.id,par.name)!=(definition['target']['owner_id'],definition['target']['name']):
        raise ValueError('Native target changed; reopen this control')
    if kind=='values':par.owner.openParameters()
    else:open_definition(par.owner)
    return definition['target']['comp']
