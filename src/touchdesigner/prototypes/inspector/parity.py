"""Scalar filter/confirmation helpers; importing this module performs no writes."""
from time import monotonic

def ownership_label(metadata):
    category=metadata.get('category','LEGACY')
    owner=metadata.get('owner') or {}
    if category=='COMP':
        return 'COMP: '+str(owner.get('path') or 'Unavailable')+' · '+str(owner.get('state') or 'unavailable')
    return 'CUSTOM' if category=='CUSTOM' else 'Legacy-unclassified'

def detail_groups(info,health,status,snapshot,view_labels,route_labels,selected_labels,following):
    """Readable labels first; long identities stay in the scrollable technical group."""
    state=(snapshot or {}).get('state',{})
    error=info.get('definition_error') or info.get('error') or status.get('Lasterror') or status.get('FollowError')
    mapping=[('State',health['label'],'short'),('Style / Mode',(info.get('parameter_style') or ('Action' if info.get('binding_type')=='action' else 'Callback'))+' / '+str(info.get('mode') or '—').upper(),'short')]
    if error:mapping.append(('Issue',str(error),'long'))
    elif info.get('binding_type')=='action':mapping.append(('Result',(info.get('action_result') or {}).get('status','Ready'),'short'))
    follow=str(status.get('FollowStatus','—'))
    short_follow='waiting' if follow.startswith('waiting_') else follow
    routing=[('Layout',route_labels[0],'short'),('Track · FUNC',route_labels[1],'short'),('Device · SEL',route_labels[2],'short'),
             ('Follow',('ON' if status.get('Follow') else 'OFF')+' · '+short_follow,'short'),
             ('LOCK / Gate',('ON' if status.get('Locked') else 'OFF')+' / '+('ON' if status.get('Gated') else 'OFF'),'short')]
    target=info.get('comp','')+'.'+info['parameter'] if info.get('parameter') else 'Python callback' if info.get('id') else '—'
    if info.get('binding_type')=='action':target='Action preset: '+str(info.get('action_id') or 'Unavailable')
    technical=[('Target',target,'long'),('ID',str(info.get('id') or 'Unassigned'),'long'),
               ('Viewing',ownership_label(status.get('ViewingOwner',{}))+' · '+' / '.join(view_labels)+(' · follows routing' if following else ' · browse pinned'),'long'),
               ('Selected',' / '.join(selected_labels),'long'),
               ('Owner / Follow',ownership_label(status.get('RoutingOwner',{}))+' · '+('Needs Activate · ' if status.get('Quarantined') else '')+follow.replace('_',' '),'long'),
               ('RX / TX / Rej',' / '.join(str(state.get(n,'—')) for n in ('Rx','Tx','Rejected')),'short')]
    return (('Mapping',tuple(mapping)),('Hardware routing',tuple(routing)),('Technical · Refresh snapshot',tuple(technical)))

def filter_choices(info):
    paths=tuple(dict.fromkeys(row.get('comp','') for row in info if row.get('id') and row.get('parameter')))
    return (('all','All controls'),('callbacks','Python callbacks'),('actions','Action presets'))+tuple(('comp:'+path,path) for path in paths)

def visible_slots(info,choice):
    if choice=='all':return tuple(range(16))
    if choice=='actions':return tuple(i for i,r in enumerate(info) if r.get('id') and r.get('binding_type')=='action')
    if choice=='callbacks':return tuple(i for i,r in enumerate(info) if r.get('id') and r.get('binding_type')=='callback')
    if choice.startswith('comp:'):return tuple(i for i,r in enumerate(info) if r.get('id') and r.get('parameter') and r.get('comp')==choice[5:])
    return ()

def registration_fingerprint(info):
    fields=('action_id','id','kind','slot','comp','parameter','mode','minimum','maximum','button_type','binding_type','parameter_definition','requires_relearn')
    return tuple(tuple(r.get(n) for n in fields)+(tuple(r.get('menu_names',())),tuple(r.get('menu_labels',()))) for r in info if r.get('id'))

class ClearRequest:
    def __init__(self,confirmation,clock=monotonic):
        self.confirmation=confirmation;self.clock=clock;self.expires=clock()+8;self.used=False
    def Consume(self):
        if self.used or self.clock()>self.expires:raise ValueError('Clear Device confirmation expired; request again')
        self.used=True
        return self.confirmation
