"""Versioned parameter-layout database and serialized host activation.

Callbacks remain supported by the legacy API, but cannot be converted without a
reconstruction factory. No target value or callable is persisted as a preset.
"""
import copy
import math
import os
import uuid
from contextlib import contextmanager
from protocol import digest, display_name, text13
from binding import parameter_value

VERSION=3
OWNER_KEY='roto_control_owner_id'
PLUGIN_FIELDS=("group_id","device_id","plugin_name","targets","state")
FIELDS=('parameter_assignments','assignment_device_id','control_overrides','removed_controls','pending_unmaps','needs_relearn','control_catalog','pending_unmap_identities','page_targets')
DEFAULTS=([],None,{},[],[],(),[],[],[])

class ActivationRollbackError(RuntimeError):
    rollback_failed = True


class Layouts:
    def __init__(self, extension):
        self.ext=extension;self.owner=extension.ownerComp
        self.mutating=False;self.locked=False;self.touched=set();self.confirmed=False
        self.delete_pending=None
        self.track_delete_pending=None
        self.first_track=0
        self.first_plugin=0
        self.selected_track=None
        self.selected_plugin=None
        self.legacy=False
        self.owner_handles={}
        self.quarantined=False
        self._owner_observation_depth=0
        data=self.owner.fetch('layout_registry',None)
        fresh=data is None
        if data is None:
            record=self.snapshot('custom','Custom')
            data=dict(version=1,active='custom',records=[record])
        data=self.migrate(data)
        if fresh:data['records'][0]['category']='CUSTOM'
        self.validate(data)
        self.data=copy.deepcopy(data)
        self.owner.store('page_targets',copy.deepcopy(self.plugin()['state'].get('page_targets',[])))
        self.save();self.attach();self.menu()

    @staticmethod
    def migrate(data):
        """Copy v1 without changing any hardware or parameter identity."""
        data=copy.deepcopy(data)
        if not isinstance(data,dict):raise ValueError('Invalid Layout database')
        if data.get('version')==1:
            records=[]
            for old in data['records']:
                track_id='track.'+old['id']
                plugin=dict({key:old[key] for key in PLUGIN_FIELDS},id='plugin.'+old['id'])
                track=dict(id=track_id,name=old['track_name'],active_plugin=plugin['id'],plugins=[plugin])
                records.append(dict(id=old['id'],name=old['name'],active_track=track_id,tracks=[track]))
            data.update(version=2,records=records)
        if data.get('version')==2:
            for layout in data['records']:
                for track in layout['tracks']:
                    link=track.pop('focus_comp',None)
                    if link is not None:track['plugins'][0]['focus_comp']=link
                    for plugin in track['plugins']:
                        plugin['name_mode']='comp' if plugin.get('focus_comp') else 'manual'
            data['version']=VERSION
        if data.get('version')==VERSION:
            data.setdefault('ownership_version',1)
            data.setdefault('revision',0)
            for layout in data['records']:
                layout.setdefault('category','LEGACY')
                for track in layout['tracks']:
                    for plugin in track['plugins']:
                        plugin.setdefault('name_mode','manual')
                        link=plugin.get('focus_comp')
                        if isinstance(link,dict) and isinstance(link.get('path'),str) and link['path']:
                            link['path']=os.path.normpath(link['path'])
                        library={t['id']:t for t in plugin['state'].get('page_targets',[])}
                        library.update({t['id']:copy.deepcopy(t) for t in plugin['targets']})
                        plugin['state']['page_targets']=list(library.values())
        return data

    @staticmethod
    def validate(data):
        if not isinstance(data,dict) or data.get('version')!=VERSION:
            raise ValueError('Unsupported Layout database version')
        records=data.get('records')
        if not isinstance(records,list) or not records:
            raise ValueError('Layout database needs at least one Layout')
        ids=set();track_ids=set();plugin_ids=set();groups=set();devices=set()
        owners=set()
        if data.get('ownership_version',1)!=1:raise ValueError('Unsupported ownership metadata version')
        if type(data.get('revision',0)) is not int or data.get('revision',0)<0:raise ValueError('Invalid registry revision')
        for layout in records:
            if not isinstance(layout,dict):raise ValueError('Invalid Layout record')
            category=layout.get('category','LEGACY')
            if category not in ('COMP','CUSTOM','LEGACY'):raise ValueError('Invalid Layout category')
            owner=layout.get('owner')
            if category=='COMP':
                if (not isinstance(owner,dict) or not isinstance(owner.get('id'),str) or not owner['id']
                        or owner['id'] in owners or owner.get('state') not in ('bound','missing','conflict','unregistered')
                        or not isinstance(owner.get('path'),str) or not owner['path'] or owner['path'].startswith('/')):
                    raise ValueError('Invalid or duplicate Layout owner')
                owners.add(owner['id'])
            elif owner is not None:raise ValueError('Only COMP Layouts have owners')
            if not isinstance(layout,dict) or not isinstance(layout.get('id'),str) or not layout['id'] or layout['id'] in ids:
                raise ValueError('Invalid or duplicate Layout ID')
            ids.add(layout['id'])
            if not isinstance(layout.get('name'),str) or not layout['name'].strip():raise ValueError('Layout name is required')
            tracks=layout.get('tracks')
            if not isinstance(tracks,list) or not 1<=len(tracks)<=16383:raise ValueError('Layout needs 1..16383 Tracks')
            if layout.get('active_track') not in [t['id'] for t in tracks]:raise ValueError('Active Track is missing')
            focus_paths={}
            for track in tracks:
                if not isinstance(track.get('id'),str) or not track['id'] or track['id'] in track_ids:raise ValueError('Invalid or duplicate Track ID')
                track_ids.add(track['id']);display_name(track['name'])
                plugins=track.get('plugins')
                if not isinstance(plugins,list) or not 1<=len(plugins)<=127:raise ValueError('Track needs 1..127 Plugins')
                if track.get('active_plugin') not in [p['id'] for p in plugins]:raise ValueError('Active Plugin is missing')
                for record in plugins:
                    if record.get('name_mode','manual') not in ('manual','comp'):raise ValueError('Invalid Plugin name policy')
                    link=record.get('focus_comp')
                    if link is not None:
                        if (not isinstance(link,dict) or link.get('state') not in ('bound','missing')
                                or not isinstance(link.get('path'),str) or not link['path'] or link['path'].startswith('/')):
                            raise ValueError('Invalid Focus COMP link')
                        qualified=category=='COMP' and link.get('owner_id')==owner['id']
                        if link.get('owner_id') is not None and not qualified:raise ValueError('Invalid Focus owner identity')
                        if qualified and link['path']!=owner['path']:raise ValueError('Owner Focus path differs from owner locator')
                        if link['state']=='bound':
                            # Qualified same-owner variants are atomic independent configs.
                            # Unqualified Focus remains unique; it cannot infer ownership.
                            if link['path'] in focus_paths and not (qualified and focus_paths[link['path']]):
                                raise ValueError('Duplicate Focus COMP link in Layout')
                            focus_paths[link['path']]=qualified
                    if not isinstance(record.get('id'),str) or not record['id'] or record['id'] in plugin_ids:raise ValueError('Invalid or duplicate Plugin ID')
                    plugin_ids.add(record['id'])
                    for field,seen in (('group_id',groups),('device_id',devices)):
                        if not isinstance(record.get(field),str) or not record[field] or record[field] in seen:raise ValueError('Invalid or duplicate Plugin '+field)
                        seen.add(record[field])
                    display_name(record['plugin_name'])
                    if not isinstance(record.get('targets'),list) or not isinstance(record.get('state'),dict):raise ValueError('Invalid Plugin target/state records')
                    slots=set();target_ids=set()
                    for target in record['targets']:
                        key=(target['kind'],target['slot'])
                        if key[0] not in ('knob','button') or type(key[1]) is not int or not 1<=key[1]<=8 or key in slots or target['id'] in target_ids:raise ValueError('Invalid or duplicate Plugin target slot/ID')
                        slots.add(key);target_ids.add(target['id'])
            if category=='COMP' and owner.get('entry_plugin_id') not in [p['id'] for t in tracks for p in t['plugins']]:
                raise ValueError('Owner Device is missing')
        if data.get('active') not in ids:raise ValueError('Active Layout is missing')

    def save(self):
        self.validate(self.data)
        stored=self.owner.fetch('layout_registry',None)
        left=copy.deepcopy(stored);right=copy.deepcopy(self.data)
        if isinstance(left,dict):left.pop('revision',None)
        right.pop('revision',None)
        if left!=right:
            self.data['revision']=(stored or {}).get('revision',0)+1
            self.owner.store('layout_registry',copy.deepcopy(self.data))
        elif stored is not None:self.data['revision']=stored.get('revision',0)

    def registry_snapshot(self):
        """Detached source for planning. Flush definitions without writing target values."""
        self.refresh_owners(force=True);self.capture(force=True)
        return copy.deepcopy(self.data)

    def check_revision(self, revision):
        """Preflight for a future serialized migration transaction, not a commit API."""
        current=self.registry_snapshot()['revision']
        if type(revision) is not int or revision!=current:raise ValueError('Layout registry revision changed; rebuild plan')
        return current

    def owner_candidates(self, extra=()):
        """Identity inventory, including untagged COMPs; names never identify owners."""
        follower=getattr(self.ext,'_follow',None)
        candidates=list(extra)+list(self.owner_handles.values())
        if follower is not None:candidates.extend(follower.owner_candidates())
        for layout in self.data['records']:
            if layout.get('owner'):candidates.append(self.owner.op(layout['owner']['path']))
        return list({c.path:c for c in candidates if c is not None and getattr(c,'valid',False)
                     and getattr(c,'isCOMP',False)}.values())

    @staticmethod
    def owner_token(comp):
        """A COMP's local storage token; OP.fetch defaults to parent inheritance."""
        fetch=getattr(comp,'fetch',None)
        return fetch(OWNER_KEY,None,search=False) if callable(fetch) else None

    @contextmanager
    def owner_observation(self):
        """One inventory for a synchronous read/Tick batch, never a timed cache."""
        if not self._owner_observation_depth:self.refresh_owners()
        self._owner_observation_depth+=1
        try:yield
        finally:self._owner_observation_depth-=1

    def refresh_owners(self, extra=(), force=False):
        if self._owner_observation_depth and not (extra or force):return
        if not any(r.get('owner') for r in self.data['records']):return
        inventory={}
        for comp in self.owner_candidates(extra):
            token=self.owner_token(comp)
            if isinstance(token,str) and token:inventory.setdefault(token,[]).append(comp)
        changed=False
        follower=getattr(self.ext,'_follow',None)
        for layout in self.data['records']:
            owner=layout.get('owner')
            if not owner:continue
            matches=inventory.get(owner['id'],[])
            state=owner['state']
            if state=='unregistered':continue
            # A clone conflict is latched, even after one copy disappears.
            new_state='conflict' if len(matches)>1 or state=='conflict' else 'bound' if matches else 'missing'
            if new_state!=state:
                owner['state']=new_state;changed=True
                if layout['id']==self.data['active'] and not self.legacy:
                    if new_state!='bound':self.quarantined=True
                    self.confirmed=False
                    for target in self.ext._host.controls.values():target.mapped=False
                    if follower:
                        follower.routing_epoch+=1;follower.pending=None;follower.clear_controls()
                        self.ext._discard_context_output()
            if new_state!='bound':
                self.owner_handles.pop(owner['id'],None)
                continue
            comp=matches[0];self.owner_handles[owner['id']]=comp
            path=os.path.relpath(comp.path,self.owner.path)
            if path!=owner['path']:
                if follower:follower._rebase_targets(None,owner['path'],path)
                owner['path']=path;changed=True
            # Owner entry is a Focus link too, but Focus is not ownership.
            for plugin in (p for t in layout['tracks'] for p in t['plugins']):
                if plugin['id']!=owner['entry_plugin_id'] and (plugin.get('focus_comp') or {}).get('owner_id')!=owner['id']:continue
                link=dict(path=path,state='bound',owner_id=owner['id'])
                if plugin.get('focus_comp')!=link:plugin['focus_comp']=link;changed=True
                if follower:follower.handles[plugin['id']]=comp
        if changed:self.save()

    def owner_ready(self, layout_id=None, required=False):
        if self.legacy and layout_id is None:return True  # separate callback registration routing
        # Mutations/writes always revalidate inventory. Nested getters borrow the
        # current synchronous observation but still check their live handle/token.
        if required or not self._owner_observation_depth:self.refresh_owners(force=required)
        owner=self.layout(layout_id).get('owner')
        if owner and owner['state']=='bound':
            comp=self.owner_handles.get(owner['id'])
            if (comp is None or not getattr(comp,'valid',False) or self.owner_token(comp)!=owner['id']
                    or os.path.relpath(comp.path,self.owner.path)!=owner['path']):
                self.refresh_owners(force=True)
        ready=owner is None or owner['state']=='bound'
        if required and not ready:raise ValueError('Layout owner '+owner['state']+'; explicitly repair ownership before Activate')
        return ready

    def register_comp(self, comp, new_identity=False):
        """Enroll without selecting. Clone re-keying is explicit and transactional."""
        follower=getattr(self.ext,'_follow',None)
        if follower is None or not follower.eligible(comp):raise ValueError('Choose a valid external COMP')
        if not callable(getattr(comp,'fetch',None)) or not callable(getattr(comp,'store',None)):
            raise ValueError('COMP must support persistent storage')
        self.owner_guard();self.refresh_owners((comp,))
        old_token=self.owner_token(comp)
        if old_token is not None and (not isinstance(old_token,str) or not old_token):
            raise ValueError('Invalid durable owner token; explicit repair is required')
        existing=next((r for r in self.data['records'] if old_token and r.get('owner',{}).get('id')==old_token),None)
        if existing and not new_identity:
            state=existing['owner']['state']
            if state=='unregistered':raise ValueError('Owner unregistered; use RelinkLayoutOwner to resume')
            if state!='bound':raise ValueError('Owner '+state+'; use explicit relink or clone identity')
            return existing['id']
        if new_identity and existing and existing['owner']['state']!='conflict':
            raise ValueError('Cannot re-key an existing owner; clone conflict must be resolved explicitly')
        token='owner.'+uuid.uuid4().hex if new_identity or not old_token else old_token
        matches=[c for c in self.owner_candidates((comp,)) if self.owner_token(c)==token]
        if len(matches)>1:raise ValueError('Duplicate owner token; explicitly register clone with new_identity=True')
        self.capture(force=True)
        previous=copy.deepcopy(self.data);handles=dict(self.owner_handles);focus=dict(follower.handles)
        name=getattr(comp,'name',comp.path.rsplit('/',1)[-1])
        track=self.empty_track('EFFECT');plugin=track['plugins'][0]
        plugin.update(plugin_name=''.join(c if 32<=ord(c)<=126 else '?' for c in name)[:12] or 'COMP',
                      name_mode='comp',comp_name=name,
                      focus_comp=dict(path=os.path.relpath(comp.path,self.owner.path),state='bound',owner_id=token))
        layout=dict(id=uuid.uuid4().hex,name=name,category='COMP',active_track=track['id'],tracks=[track],
                    owner=dict(id=token,path=plugin['focus_comp']['path'],state='bound',entry_plugin_id=plugin['id']))
        try:
            comp.store(OWNER_KEY,token);self.owner_handles[token]=comp;follower.handles[plugin['id']]=comp
            self.data['records'].append(layout);self.save();self.menu()
        except Exception as original:
            self._owner_rollback(previous,handles,focus,[(comp,old_token)],{},original)
            raise
        return layout['id']

    def _owner_rollback(self, previous, handles, focus, tokens, stores, original):
        follower=self.ext._follow
        try:
            for comp,token in tokens:comp.store(OWNER_KEY,token)
            self.data=previous;self.owner_handles=handles;follower.handles=focus
            for key,value in stores.items():self.owner.store(key,value)
            self.save();self.menu()
        except Exception as rollback:
            follower.pending=None;follower.paused=True;follower.fence()
            follower.error=str(original)+'; rollback failed: '+str(rollback);follower.status='paused'
            raise ActivationRollbackError(follower.error) from original

    def relink_owner(self, layout_id, comp):
        """Explicit recovery keeps all mapping/wire IDs and rebinds saved destinations."""
        layout=self.layout(layout_id);owner=layout.get('owner');follower=getattr(self.ext,'_follow',None)
        if owner is None:raise ValueError('Layout has no owner')
        self.owner_guard()
        if layout_id==self.data['active']:raise ValueError('Activate another Layout before relinking this owner')
        if follower is None or not follower.eligible(comp):raise ValueError('Choose a valid external COMP')
        if not callable(getattr(comp,'store',None)) or not callable(getattr(comp,'fetch',None)):
            raise ValueError('COMP must support persistent storage')
        self.refresh_owners((comp,))
        token=self.owner_token(comp)
        if token and token!=owner['id']:raise ValueError('COMP already has another durable identity')
        if any(c is not comp and self.owner_token(c)==owner['id']
               for c in self.owner_candidates((comp,))):raise ValueError('Owner identity still exists on another COMP')
        handles=dict(self.owner_handles);focus=dict(follower.handles)
        # Capture the routing configuration before rebasing its external references.
        self.capture(force=True);previous=copy.deepcopy(self.data)
        stores={key:copy.deepcopy(self.owner.fetch(key,[])) for key in ('parameter_assignments','page_targets','control_catalog')}
        try:
            comp.store(OWNER_KEY,owner['id'])
            path=os.path.relpath(comp.path,self.owner.path)
            follower._rebase_targets(None,owner['path'],path,layout_id=layout_id)
            owner.update(path=path,state='bound');self.owner_handles[owner['id']]=comp
            self.refresh_owners((comp,));self.save();self.menu();follower.invalidate()
        except Exception as original:
            self._owner_rollback(previous,handles,focus,[(comp,token)],stores,original)
            raise
        return layout_id

    def unregister_owner(self, layout_id):
        layout=self.layout(layout_id);owner=layout.get('owner')
        if owner is None:raise ValueError('Layout has no owner')
        self.owner_guard();self.capture(force=True)
        if layout_id==self.data['active']:raise ValueError('Activate another Layout before unregistering this owner')
        previous=copy.deepcopy(self.data);handles=dict(self.owner_handles);focus=dict(self.ext._follow.handles)
        try:
            owner['state']='unregistered';self.owner_handles.pop(owner['id'],None)
            self.save();self.menu()
        except Exception as original:
            self._owner_rollback(previous,handles,focus,[],{},original)
            raise
        return layout_id

    def plugin_targets(self, layout_id=None, track_id=None, plugin_id=None):
        """Read live values for an inactive library; never trust saved catalog values."""
        layout=self.layout(layout_id);track=self.track(layout['id'],track_id)
        plugin=self.plugin(layout['id'],track['id'],plugin_id)
        ready=self.owner_ready(layout['id'])
        library={t['id']:copy.deepcopy(t) for t in plugin['state'].get('page_targets',[])}
        targets=plugin['targets']
        if (layout['id'],track['id'],plugin['id'])==self.context().get('key'):
            library.update({t['id']:copy.deepcopy(t) for t in self.owner.fetch('page_targets',[])})
            targets=self.snapshot(layout['id'],layout['name'])['targets']
        library.update({t['id']:copy.deepcopy(t) for t in targets})
        result=[]
        for target in library.values():
            target.update(value=None,valid=False,value_source='unavailable')
            try:
                comp=self.owner.op(target['comp']) if ready else None
                par=getattr(comp.par,target['parameter'],None) if comp is not None and getattr(comp,'valid',False) else None
                if par is not None:
                    value=None if target['mode']=='pulse' else parameter_value(par)
                    if value is not None and not math.isfinite(value):raise ValueError('Target value is not finite')
                    target.update(value=value,valid=True,value_source='pulse' if target['mode']=='pulse' else 'live')
            except (ValueError,AttributeError,RuntimeError,TypeError):pass
            result.append(target)
        return result

    def layout(self,id=None):
        id=self.data['active'] if id is None else id
        for record in self.data['records']:
            if record['id']==id:return record
        raise ValueError('Unknown Layout ID: '+str(id))

    def track(self,layout_id=None,track_id=None):
        layout=self.layout(layout_id)
        track_id=layout['active_track'] if track_id is None else track_id
        for track in layout['tracks']:
            if track['id']==track_id:return track
        raise ValueError('Unknown Track ID: '+str(track_id))

    def plugin(self,layout_id=None,track_id=None,plugin_id=None):
        track=self.track(layout_id,track_id)
        plugin_id=track['active_plugin'] if plugin_id is None else plugin_id
        for plugin in track['plugins']:
            if plugin['id']==plugin_id:return plugin
        raise ValueError('Unknown Plugin ID: '+str(plugin_id))

    def record(self,id=None,track_id=None,plugin_id=None):
        """Flat activation projection; nested registry remains the authority."""
        layout=self.layout(id);track=self.track(id,track_id)
        return dict(self.plugin(id,track_id,plugin_id),id=layout['id'],name=layout['name'],track_name=track['name'])

    def context(self):
        if self.legacy:return dict(legacy=True,label='Python registration',key=None)
        layout=self.layout();track=self.track();plugin=self.plugin()
        return dict(legacy=False,category=layout.get('category','LEGACY'),owner=copy.deepcopy(layout.get('owner')),
                    revision=self.data['revision'],quarantined=self.quarantined,
                    layout_id=layout['id'],track_id=track['id'],plugin_id=plugin['id'],
                    selected_track_id=self.selected_track or track['id'],locked=self.locked,
                    selected_plugin_id=self.selected_plugin or plugin['id'],first_plugin=self.first_plugin,
                    plugin_count=len(track['plugins']),
                    key=(layout['id'],track['id'],plugin['id']),
                    label=layout.get('category','LEGACY')+' / '+layout['name']+' / '+track['name']+' / '+plugin['plugin_name'])

    def snapshot(self,id,name):
        ext=self.ext;targets=[]
        old=self.record(id) if hasattr(self,"data") and any(r["id"]==id for r in self.data["records"]) else None
        bindings=ext._collection.bindings.items() if ext._collection is not None else [(('knob',1),ext._binding)]
        for key,binding in bindings:
            if binding is None:
                # Built-in Value remains a real target, never a saved numeric preset.
                parameter=ext._value_parameter()
                target=dict(kind='knob',slot=1,id='Value',label='Value',minimum=0,maximum=1,mode='value',button_type=None,index=0)
            else:
                parameter=binding.parameter
                if parameter is None: raise ValueError('Callback Layouts need a reconstruction factory; existing callback API is unchanged')
                target=dict(kind=key[0],slot=key[1],id=binding.id,label=binding.label,minimum=binding.minimum,maximum=binding.maximum,
                            mode=ext._collection.modes[key] if ext._collection is not None else 'value',
                            button_type=ext._collection.button_types[key] if ext._collection is not None else None,
                            index=ext._collection.indices[key] if ext._collection is not None else 0)
            target['identity']=ext._host.controls[key].target_id if ext._collection is not None else ext._host.target_id
            target['menu_names']=list(binding.menu_names) if binding is not None else []
            target['menu_labels']=list(binding.menu_labels) if binding is not None else []
            if not getattr(parameter.owner,'valid',True):
                previous=next((t for t in old['targets'] if t['id']==target['id']),None) if old else None
                if previous is None:
                    previous=next((t for t in self.owner.fetch('parameter_assignments',[]) if t['id']==target['id']),None)
                if previous is None:raise ValueError('Unavailable target needs a saved Layout record')
                target.update(comp=previous['comp'],parameter=previous['parameter'])
                targets.append(target);continue
            target.update(comp=os.path.relpath(parameter.owner.path,self.owner.path),parameter=parameter.name)
            targets.append(target)
        old=self.record(id) if hasattr(self,'data') and any(r['id']==id for r in self.data['records']) else None
        # Preserve unavailable registrations until an explicit Clear removes them.
        removed=set(self.owner.fetch('removed_controls',[]))
        if old:
            present={t['id'] for t in targets}
            slots={(t['kind'],t['slot']) for t in targets}
            targets.extend(copy.deepcopy(t) for t in old['targets'] if t['id'] not in present and t['id'] not in removed and (t['kind'],t['slot']) not in slots)
        group=self.owner.par.Groupid.eval() if ext._collection is not None else 'legacy:'+ext._host.device_id
        return dict(id=id,name=name,group_id=group,device_id=ext._host.device_id,
                    track_name=ext._host.track_name,plugin_name=ext._host.plugin_name,targets=targets,
                    state={field:copy.deepcopy(self.owner.fetch(field,default)) for field,default in zip(FIELDS,DEFAULTS)})

    def capture(self,force=False):
        if self.legacy or self.mutating or self.ext._restore_pending or not getattr(self.ext,"_layout_ready",True) or not (force or getattr(self.ext,"_layout_dirty",False)):return
        old=self.record()
        record=self.snapshot(old['id'],old['name'])
        removed=set(self.owner.fetch('removed_controls',[]))
        library={t['id']:t for t in self.owner.fetch('page_targets',[]) if t['id'] not in removed}
        library.update({t['id']:copy.deepcopy(t) for t in record['targets']})
        self.owner.store('page_targets',list(library.values()))
        record['state']['page_targets']=copy.deepcopy(list(library.values()))
        self.plugin().update({key:record[key] for key in PLUGIN_FIELDS})
        self.track()['name']=record['track_name']
        self.save()
        self.ext._layout_dirty=False

    def menu(self):
        for name,records,active in (('Layout',self.data['records'],self.data['active']),('Track',self.layout()['tracks'],self.layout()['active_track'])):
            par=getattr(self.owner.par,name,None)
            if par is not None:
                par.menuNames=[r['id'] for r in records]
                par.menuLabels=[r.get('category','LEGACY')+' / '+r['name'] for r in records] if name=='Layout' else [r['name'] for r in records]
                par.val=active
        par=getattr(self.owner.par,'Plugin',None)
        if par is not None:
            par.menuNames=[p['id'] for p in self.track()['plugins']]
            par.menuLabels=[p.get('comp_name',p['plugin_name']) if p.get('name_mode')=='comp' else p['plugin_name'] for p in self.track()['plugins']]
            par.val=self.plugin()['id']
        name=getattr(self.owner.par,'Pluginname',None)
        if name is not None:name.enable=not self.legacy and self.plugin().get('name_mode')!='comp'
        for name,value in (('Layoutname',self.layout()['name']),('Newtrackname','TRACK')):
            par=getattr(self.owner.par,name,None)
            if par is not None and name=='Layoutname':par.val=value
        follower = getattr(self.ext, '_follow', None)
        if follower is not None:follower.sync_ui()

    def attach(self):
        host=self.ext._host
        host.devices_callback=None if self.legacy else self.announce
        host.tracks_callback=None if self.legacy else self.announce_tracks
        host.plugin_index=self.track()['plugins'].index(self.plugin())
        if hasattr(host,'pending_unmaps') and not self.legacy:host.pending_unmaps=set()

    def track_detail(self,index):
        track=self.layout()['tracks'][index]
        return (index>>7,index&127,*text13(track['name']),0,0)

    def announce_tracks(self,select=True):
        host=self.ext._host;tracks=self.layout()['tracks']
        self.first_track=min(self.first_track,((len(tracks)-1)//8)*8)
        host._command(10,4,(len(tracks)>>7,len(tracks)&127))
        host._command(10,5,(self.first_track>>7,self.first_track&127))
        for index in range(self.first_track,min(self.first_track+8,len(tracks))):
            host._command(10,7,self.track_detail(index))
        host._command(10,8)
        if select:
            selected=self.selected_track or self.track()['id']
            index=next(i for i,t in enumerate(tracks) if t['id']==selected)
            host._command(12,4,self.track_detail(index))

    def announce(self,select=True):
        host=self.ext._host;plugins=self.track()['plugins']
        self.first_plugin=min(self.first_plugin,((len(plugins)-1)//8)*8)
        host._command(11,2,(len(plugins),));host._command(11,3,(self.first_plugin,))
        for index in range(self.first_plugin,min(self.first_plugin+8,len(plugins))):
            record=plugins[index]
            host._command(11,5,(index,*digest(record['device_id'],8),1,*text13(record['plugin_name']),0,0))
        host._command(11,6)
        if select:host._command(11,8,(plugins.index(self.plugin()),0,0))

    def guard(self,hardware=False):
        host=self.ext._host
        if self.mutating or self.ext._dispatching or host.learning or host.touched or self.touched:
            raise ValueError('Exit LEARN and release controls before switching Layout')
        if self.locked and not hardware:raise ValueError('Unlock hardware before switching Layout')
        if not self.legacy:self.snapshot(self.record()['id'],self.record()['name'])  # callback preflight

    def owner_guard(self):
        self.guard()
        follower=getattr(self.ext,'_follow',None);host=self.ext._host
        if self.legacy:raise ValueError('Owner Layouts require Parameter mapping')
        if follower and (follower.paused or follower.gated or follower.pending or follower.backlog):
            raise ValueError('Wait for routing recovery before changing Layout ownership')
        if getattr(self.ext,'_process',None) is not None and not (host.connected and host.plugin):
            raise ValueError('Wait for MIDI connection before changing Layout ownership')

    def resolve(self,record,quarantine=False):
        if not self.owner_ready(record.get('id')):
            if quarantine:return [],copy.deepcopy(record['targets'])
            self.owner_ready(record.get('id'),required=True)
        specs=[];unavailable=[]
        for target in record['targets']:
            comp=self.owner.op(target['comp']);par=getattr(comp.par,target['parameter'],None) if comp is not None else None
            if par is None or not getattr(comp,'valid',True):
                unavailable.append(target);continue
            if target['mode']=='pulse':
                value=0
            else:
                value=parameter_value(par)
            spec=dict({k:v for k,v in target.items() if k not in ('comp','parameter','identity','menu_names','menu_labels')},parameter=par,value=value)
            if getattr(par,'style','')=='Menu' and (list(par.menuNames)!=target.get('menu_names',[]) or list(par.menuLabels)!=target.get('menu_labels',[])):
                spec['minimum']=0;spec['maximum']=len(par.menuNames)-1
            specs.append(spec)
        self.owner.op('controls').module.Controls(specs,allow_empty=True)
        return specs,unavailable

    def install(self,record,hardware=False,quarantine=False):
        specs,unavailable=self.resolve(record,quarantine)  # preflight before mutation
        ext=self.ext;host=ext._host;session=(host.connected,host.plugin,host.learning)
        self.mutating=True
        try:
            inspector=self.owner.op('inspector')
            if inspector is not None:
                inspector.store('pending_clear',None)
                inspector.store('action_status','Selected '+self.context()['label'])
            self.delete_pending=self.track_delete_pending=None
            ext._delete_request=None
            # Keep only a partially transmitted JSON line so the MIDI child's
            # input stream remains valid; discard queued old-context feedback.
            pending=ext._pending
            ext._pending=(pending.split(b'\n',1)[0]+b'\n') if pending and not pending.startswith(b'{"midi":') else b''
            host.connected=host.plugin=False
            learner=getattr(ext,'_free_learner',None)
            if learner:
                learner.pending=learner.last_parameter=None;learner.ignored={};learner.baseline={}
                self.owner.op('learn_parameters').par.active=False
            for field,default in zip(FIELDS,DEFAULTS):self.owner.store(field,copy.deepcopy(record['state'].get(field,default)))
            # Materialized records replace table/hook sources for this Layout.
            self.owner.store('parameter_assignments',copy.deepcopy(record['targets']))
            table=self.owner.op('base_targets/targets');header=[c.val for c in table.row(0)]
            table.clear();table.appendRow(header)
            self.owner.par.Setupmode='collection';self.owner.par.Groupid=record['group_id']
            self.owner.store('assignment_device_id',dict(group_id=record['group_id'],device_id=record['device_id']))
            ext._restoring=False
            ext.BindControls(specs,group_id=record['group_id'],_allow_empty=True)
            for key,binding in ext._collection.bindings.items():
                saved=next(t for t in record['targets'] if t['id']==binding.id)
                semantics_match=(list(binding.menu_names)==saved.get('menu_names',[]) and list(binding.menu_labels)==saved.get('menu_labels',[]))
                if semantics_match and saved.get('identity'):
                    ext._host.controls[key].target_id=saved['identity']
                elif not semantics_match:
                    pending=set(self.owner.fetch('needs_relearn',()));pending.add(binding.id)
                    self.owner.store('needs_relearn',tuple(pending))
            ext._host.device_id=record['device_id'];ext._host.track_name=record['track_name'];ext._host.plugin_name=record['plugin_name']
            self.owner.par.Trackname=record['track_name'];self.owner.par.Pluginname=record['plugin_name']
            ext._host.connected,ext._host.plugin,ext._host.learning=session
            self.confirmed=False;self.attach();self.menu()
            catalog=copy.deepcopy(record['state'].get('control_catalog',[]))
            for missing in unavailable:
                item=next((item for item in catalog if item['id']==missing['id']),None)
                if item is None:
                    item=dict(missing,comp=self.owner.path+'/'+missing['comp'],binding_type='parameter',parameter_style='',value=None,normalized=0,valid=False,mapped=False,connected=session[0],plugin=session[1],touched=False,requires_relearn=True)
                    catalog.append(item)
                item.update(valid=False,mapped=False,error='Target unavailable',last_mapped=False)
            self.owner.store('control_catalog',catalog)
            if ext._host.connected and ext._host.plugin:
                self.announce_tracks(select=not hardware)
                self.announce()
            ext._host.last_event=self.context()['label']+': awaiting per-control recall' if session[0] else self.context()['label']+': disconnected'
            ext._last_error=''
            ext._layout_ready=True
            self.quarantined=quarantine
        finally:
            self.mutating=False

    def select(self,id,hardware=False):
        layout=self.layout(id)
        return self._select(id,layout['active_track'],hardware)

    def select_track(self,layout_id,track_id,hardware=False):
        self.track(layout_id,track_id)
        self._select(layout_id,track_id,hardware)
        return track_id

    def select_plugin(self,layout_id,track_id,plugin_id,hardware=False):
        self.plugin(layout_id,track_id,plugin_id)
        if self.locked and hardware and (layout_id!=self.data['active'] or track_id!=self.track()['id']):
            raise ValueError('Locked Device selection stays within the routing Track')
        self._select(layout_id,track_id,hardware,plugin_id)
        return plugin_id

    def _select(self,layout_id,track_id,hardware=False,plugin_id=None):
        follower = getattr(self.ext, '_follow', None)
        self.owner_ready(layout_id,required=True)
        plugin_id=self.plugin(layout_id,track_id,plugin_id)['id']
        if (layout_id,track_id,plugin_id)==self.context().get('key') and not self.legacy and not self.quarantined:
            if follower is not None and not follower.committing:
                follower.before_manual(layout_id,track_id,plugin_id);follower.after_manual()
            if not self.locked:self.selected_track=track_id
            return layout_id
        self.guard(hardware)
        destination=self.record(layout_id,track_id,plugin_id);self.resolve(destination);self.capture(force=True)
        if follower is not None:follower.before_manual(layout_id,track_id,plugin_id)
        previous=copy.deepcopy(self.data);old_selected=self.selected_track;old_page=self.first_track
        old_quarantine=self.quarantined
        old_plugin=self.selected_plugin;old_plugin_page=self.first_plugin
        session=(self.ext._host.connected,self.ext._host.plugin,self.ext._host.learning)
        self.legacy=False;self.owner.store('layout_registry_suspended',False)
        self.data['active']=layout_id;self.layout()['active_track']=track_id
        self.track()['active_plugin']=plugin_id
        self.selected_track=old_selected if self.locked and hardware else track_id
        self.selected_plugin=plugin_id
        self.first_track=(self.layout()['tracks'].index(self.track())//8)*8
        self.first_plugin=(self.track()['plugins'].index(self.plugin())//8)*8
        try:self.install(destination,hardware)
        except Exception as original:
            self.data=previous;self.selected_track=old_selected;self.first_track=old_page
            self.selected_plugin=old_plugin;self.first_plugin=old_plugin_page
            self.ext._host.connected,self.ext._host.plugin,self.ext._host.learning=session
            try:self.install(self.record(),quarantine=old_quarantine)
            except Exception as rollback:
                if isinstance(rollback,OSError):raise
                if follower is not None:
                    follower.pending=None;follower.paused=True;follower.fence()
                    follower.error=str(original)+'; rollback failed: '+str(rollback)
                    follower.status='paused'
                raise ActivationRollbackError(str(original)+'; rollback failed: '+str(rollback)) from original
            raise
        self.save()
        if follower is not None:follower.after_manual()
        self.ext._publish();return layout_id

    def restore(self):
        self.legacy=False;self.owner.store('layout_registry_suspended',False)
        self.selected_track=self.track()['id']
        self.selected_plugin=self.plugin()['id']
        self.first_track=(self.layout()['tracks'].index(self.track())//8)*8
        self.first_plugin=(self.track()['plugins'].index(self.plugin())//8)*8
        self.install(self.record(),quarantine=not self.owner_ready());self.ext._restore_pending=False;self.ext._publish()

    @staticmethod
    def empty_plugin(name):
        name=display_name(name)
        plugin_id='plugin.'+uuid.uuid4().hex
        return dict(id=plugin_id,group_id=plugin_id,device_id='TD controls:'+plugin_id,
                    plugin_name=name,name_mode='manual',targets=[],state={f:copy.deepcopy(v) for f,v in zip(FIELDS,DEFAULTS)})

    @staticmethod
    def empty_track(name):
        name=display_name(name);plugin=Layouts.empty_plugin('CUSTOM')
        return dict(id='track.'+uuid.uuid4().hex,name=name,active_plugin=plugin['id'],plugins=[plugin])

    def create_plugin(self,layout_id,track_id,name):
        track=self.track(layout_id,track_id);plugin=self.empty_plugin(name)
        if len(track['plugins'])>=127:raise ValueError('Plugin count exceeds protocol capacity')
        self.guard();self.capture(force=True)
        track['plugins'].append(plugin);self.save();self.menu()
        if (layout_id,track_id)==(self.data['active'],self.track()['id']) and self.ext._host.connected:
            self.announce(select=False)
        return plugin['id']

    def rename_plugin(self,layout_id,track_id,plugin_id,name):
        name=display_name(name);plugin=self.plugin(layout_id,track_id,plugin_id)
        if self.ext._host.learning:raise ValueError('Exit LEARN before renaming Device')
        if (layout_id,track_id,plugin_id)==self.context().get('key'):
            self.ext.SetLayoutNames(self.track()['name'],name)
        plugin.update(plugin_name=name,name_mode='manual')
        self.save();self.menu()
        if (layout_id,track_id)==(self.data['active'],self.track()['id']) and self.ext._host.connected:
            self.announce(select=False)
        self.ext._publish();return plugin_id

    def remove_plugin(self,layout_id,track_id,plugin_id):
        if self.layout(layout_id).get('owner',{}).get('entry_plugin_id')==plugin_id:
            raise ValueError('Owner Device cannot be deleted; unregister preserves its recovery entry')
        track=self.track(layout_id,track_id);plugin=self.plugin(layout_id,track_id,plugin_id)
        if len(track['plugins'])==1:raise ValueError('Cannot delete the last Device')
        self.guard()
        if track['active_plugin']==plugin_id:
            successor=next(p['id'] for p in track['plugins'] if p['id']!=plugin_id)
            if (layout_id,track_id)==(self.data['active'],self.track()['id']):
                self.select_plugin(layout_id,track_id,successor)
            else:track['active_plugin']=successor
        track['plugins'].remove(plugin)
        if (layout_id,track_id)==(self.data['active'],self.track()['id']):
            self.ext._host.plugin_index=track['plugins'].index(self.plugin())
        self.save();self.menu()
        if (layout_id,track_id)==(self.data['active'],self.track()['id']) and self.ext._host.connected:self.announce()
        return True

    def create(self,name):
        if not isinstance(name,str) or not name.strip():raise ValueError('Layout name is required')
        self.guard();self.capture(force=True);id=uuid.uuid4().hex;track=self.empty_track('EFFECT')
        self.data['records'].append(dict(id=id,name=name.strip(),category='CUSTOM',active_track=track['id'],tracks=[track]))
        self.save();self.menu();return id

    def create_track(self,layout_id,name):
        layout=self.layout(layout_id);track=self.empty_track(name)
        if len(layout['tracks'])>=16383:raise ValueError('Track count exceeds protocol capacity')
        self.guard();self.capture(force=True)
        layout['tracks'].append(track);self.save();self.menu()
        if layout_id==self.data['active'] and self.ext._host.connected:self.announce_tracks(select=False)
        return track['id']

    def rename(self,id,name):
        if not isinstance(name,str) or not name.strip():raise ValueError('Layout name is required')
        self.layout(id)['name']=name.strip();self.save();self.menu();self.ext._publish();return id

    def rename_track(self,layout_id,track_id,name):
        name=display_name(name);track=self.track(layout_id,track_id)
        if self.ext._host.learning:raise ValueError('Exit LEARN before renaming Track')
        if layout_id==self.data['active'] and track_id==self.track()['id']:
            self.ext.SetLayoutNames(name,self.plugin()['plugin_name'])
        else:
            track['name']=name;self.save();self.menu()
            if layout_id==self.data['active'] and self.ext._host.connected:self.announce_tracks(select=False)
        return track_id

    def remove(self,id):
        if self.layout(id).get('owner'):raise ValueError('Use UnregisterLayoutOwner; owner Layouts retain recovery records')
        if len(self.data['records'])==1:raise ValueError('Cannot delete the last Layout')
        self.guard()
        if id==self.data['active']:self.select(next(r['id'] for r in self.data['records'] if r['id']!=id))
        self.data['records']=[r for r in self.data['records'] if r['id']!=id]
        self.save();self.menu();return True

    def remove_track(self,layout_id,track_id):
        layout=self.layout(layout_id);track=self.track(layout_id,track_id)
        if layout.get('owner',{}).get('entry_plugin_id') in [p['id'] for p in track['plugins']]:
            raise ValueError('Owner Track cannot be deleted; unregister preserves its recovery entry')
        if len(layout['tracks'])==1:raise ValueError('Cannot delete the last Track')
        self.guard()
        if layout['active_track']==track_id:
            successor=next(t['id'] for t in layout['tracks'] if t['id']!=track_id)
            if layout_id==self.data['active']:self.select_track(layout_id,successor)
            else:layout['active_track']=successor
        layout['tracks'].remove(track)
        self.save();self.menu()
        if layout_id==self.data['active'] and self.ext._host.connected:self.announce_tracks()
        return True

    def all_plugins(self):
        return (p for layout in self.data['records'] for track in layout['tracks'] for p in track['plugins'])

    def page_changed(self):
        """Normal Plugin arrows announce a new page, but not an absolute index.

        Keep all parameter definitions; current slots are rebuilt solely from
        CONTROL MAPPED hashes. An empty page must never route the previous page.
        """
        self.capture(force=True)
        ext=self.ext;host=ext._host
        if ext._collection is None:return
        self.mutating=True
        try:
            for watcher in self.owner.ops('base_targets/watch_*'):watcher.par.active=False
            learner=getattr(ext,'_free_learner',None)
            if learner:
                learner.pending=None;learner.last_parameter=None
            for mapping in (ext._collection.ids,ext._collection.bindings,ext._collection.modes,
                            ext._collection.button_types,ext._collection.paths,ext._collection.errors,ext._collection.indices):
                mapping.clear()
            host.controls.clear();host._parts.clear();host._sync()
            # Complete a partially transmitted JSON line, discard queued old feedback.
            pending=ext._pending
            ext._pending=(pending.split(b'\n',1)[0]+b'\n') if pending and not pending.startswith(b'{"midi":') else b''
            self.confirmed=False;self.touched.clear()
            self.plugin()['targets']=[]
            self.owner.store('parameter_assignments',[]);self.owner.store('control_catalog',[])
            ext._enable_manual_controls(False)
            inspector=self.owner.op('inspector')
            if inspector is not None:
                inspector.store('pending_clear',None)
                inspector.store('action_status','Control page changed; awaiting mapping reports')
            ext._output_values=None;ext._layout_dirty=True
            host.last_event='Control page changed; awaiting mapping reports'
        finally:self.mutating=False
        self.capture(force=True);ext._publish()

    def recall_page_target(self,data):
        """Resolve a saved Plugin parameter independently of its last physical slot."""
        kind='button' if data[8] else 'knob';slot=data[9]+1
        index=(data[0]<<7)|data[1];ext=self.ext
        target=ext._host.controls.get((kind,slot))
        if target is not None and target.index==index and digest(target.target_id,6)==data[2:8]:return
        removed=set(self.owner.fetch('removed_controls',[]))
        saved=next((t for t in self.owner.fetch('page_targets',[]) if t['id'] not in removed
                    and t['kind']==kind and t['index']==index and digest(t['identity'],6)==data[2:8]),None)
        if saved is None:return
        record=dict(saved,slot=slot)
        specs,missing=self.resolve({'targets':[record]})
        if missing:
            ext._last_error='Control page target unavailable: '+record['parameter'];return
        spec=specs[0];parameter=spec['parameter']
        if (list(getattr(parameter,'menuNames',None) or [])!=record.get('menu_names',[]) or
                list(getattr(parameter,'menuLabels',None) or [])!=record.get('menu_labels',[])):
            ext._last_error='Control page Menu choices changed; re-LEARN required';return
        ext.AssignParameter(kind,slot,parameter,_id=record['id'],_wire_index=index,
                            _hardware_mapped=True,_saved_spec=spec)
        ext._host.controls[kind,slot].target_id=record['identity']
        ext._layout_dirty=True
        self.capture(force=True)

    def receive(self,message,control_only=False):
        message=tuple(message)
        follower=getattr(self.ext,'_follow',None)
        control_only=control_only or bool(follower and follower.gated)
        if len(message)==3 and message[0]==191 and 52<=message[1]<=59 and 0<=message[2]<128:
            if message[2]:self.touched.add(message[1])
            else:self.touched.discard(message[1])
        if len(message)<8 or message[:5]!=(240,0,34,3,2) or message[-1]!=247 or any(type(x)is not int or not 0<=x<128 for x in message[1:-1]):return False
        group,command,data=message[5],message[6],message[7:-1]
        if self.legacy:
            if group==11 and command==13 and len(data)==1 and data[0] in (0,1):self.locked=bool(data[0]);return True
            if group==12 or (group==10 and command==2) or (group==11 and command==1):self.locked=False;self.touched.clear()
            return False
        if control_only and ((group==11 and command in (11,14)) or (group==10 and command in (20,21))):
            return False
        if group==11 and command==1 and self.ext._host.connected and not control_only:
            self.page_changed()
        if group==10 and command in (20,21) and not data and self.ext._host.plugin:
            self.page_changed();return True
        if group==11 and command==11 and len(data)==11 and data[8] in (0,1) and 0<=data[9]<8 and data[10]==0:
            try:self.recall_page_target(data)
            except ValueError as exc:self.ext._last_error=str(exc)
            pending={tuple(key) for key in self.owner.fetch('pending_unmaps',[])}
            for removed in self.owner.fetch('pending_unmap_identities',[]):
                key=(removed['kind'],removed['slot'])
                if key not in pending or key in self.ext._host.controls:continue
                if data[:2]==(removed['index']>>7,removed['index']&127) and data[2:8]==digest(removed['identity'],6) and data[8:]==(int(removed['kind']=='button'),removed['slot']-1,0):
                    ambiguous=any(t.get('identity')==removed['identity'] and t['index']==removed['index'] for r in self.all_plugins() if r['id']!=self.plugin()['id'] for t in r['state'].get('page_targets',r['targets']))
                    if ambiguous:
                        self.ext._last_error='Cannot attribute removed-target acknowledgement uniquely to this Layout'
                        return True
                    self.confirmed=True
                    self.ext._host._command(11,14,(int(removed['kind']=='button'),removed['slot']-1))
                    self.ext._host.last_event='Removed target hardware unmap reconciled'
                    return True
        if group==11 and command==13 and len(data)==1 and data[0] in (0,1):
            was_locked=self.locked;self.locked=bool(data[0])
            if follower is not None:
                if was_locked and not self.locked:follower.unlocked()
                return True
            if was_locked and not self.locked and self.selected_track and self.selected_track!=self.track()['id']:
                try:self.select_track(self.data['active'],self.selected_track,hardware=True)
                except ValueError as exc:self.ext._last_error=str(exc)
            return True
        if group==10 and command in (6,9):
            if len(data)!=2:return True
            index=(data[0]<<7)|data[1];tracks=self.layout()['tracks']
            if index>=len(tracks):return True
            if command==6:
                if index%8:return True
                self.first_track=index;self.announce_tracks(select=False)
            elif follower is not None:
                self.selected_track=tracks[index]['id']
                follower.request(self.data['active'],tracks[index]['id'],'hardware')
            elif self.locked:
                # Mirror Ableton: browsing selection can change while the locked
                # Plugin keeps its original Track and mappings. No forced select.
                self.selected_track=tracks[index]['id'];self.ext._publish()
            else:
                try:self.select_track(self.data['active'],tracks[index]['id'],hardware=True)
                except ValueError as exc:
                    self.ext._last_error=str(exc);self.announce_tracks();self.ext._publish()
            return True
        if group==11 and command==7:
            plugins=self.track()['plugins']
            if len(data)==1 and data[0]<8 and self.first_plugin+data[0]<len(plugins):
                plugin_id=plugins[self.first_plugin+data[0]]['id']
                if follower is not None:
                    self.selected_plugin=plugin_id
                    follower.request(self.data['active'],self.track()['id'],'hardware_plugin',plugin_id=plugin_id)
                else:
                    try:self.select_plugin(self.data['active'],self.track()['id'],plugin_id,hardware=True)
                    except ValueError as exc:self.ext._last_error=str(exc)
            return True
        if group==11 and command==4:
            if len(data)==1 and data[0]%8==0 and data[0]<len(self.track()['plugins']):
                self.first_plugin=data[0];self.announce(select=False)
            return True
        if (group==10 and command==2) or (group==11 and command==1):
            self.confirmed=False;self.locked=False;self.touched.clear();self.selected_track=self.track()['id']
            self.selected_plugin=self.plugin()['id']
        return False

    def acknowledge(self):
        if self.legacy:return
        if not self.confirmed and self.ext._host.mapped:
            self.confirmed=True
            # Selection has current-layout parameter evidence. Scoped offline removals can now be sent.
            # Offline deletions reconcile only on their exact removed-target report.
            # A ready slot is not evidence for other slots on this control page.
            self.ext._host.last_event=self.context()['label']+': controls recalled'
