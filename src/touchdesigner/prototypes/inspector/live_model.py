"""Shared controller projection. Browse never changes hardware routing."""
from copy import deepcopy
from contextlib import nullcontext
from collections import OrderedDict
from itertools import count
from posixpath import normpath
import math
try:
    from InspectorModel import CatalogModel, StaleDraft, FIELDS
except ModuleNotFoundError as error:
    if error.name!='InspectorModel':raise
    from model import CatalogModel, StaleDraft, FIELDS

EMPTY=('unconfigured','unconfigured','unconfigured')
META_FIELDS=('id','mode','valid','binding_type','button_type','parameter_style','parameter_definition','definition_error','available','error')
DISPLAY_FIELDS=('value_label','mapped','connected','plugin','touched','requires_relearn')

def metadata_signature(row,info):
    if not info:return None
    return (row['Label'],row['Destination'],row['Minimum'],row['Maximum'])+tuple(info.get(n) for n in META_FIELDS)+tuple(info.get('menu_names',()))+tuple(info.get('menu_labels',()))

def project_records(states):
    rows=[dict(Label='Unassigned',Destination='',Minimum=0.,Maximum=1.,Value=0.) for _ in range(16)]
    info=[{} for _ in range(16)]
    for state in states:
        kind=state.get('kind');slot=state.get('slot')
        if kind not in ('knob','button') or type(slot) is not int or not 1<=slot<=8:continue
        i=slot-1+(8 if kind=='button' else 0)
        value=state.get('value');available=state.get('mode')!='pulse' and state.get('value_source')!='pulse' and isinstance(value,(int,float)) and math.isfinite(value)
        rows[i]=dict(Label=str(state.get('label') or 'Unavailable'),Destination=(str(state.get('comp') or '')+'.'+str(state.get('parameter') or '')) if state.get('parameter') else 'Python callback',Minimum=float(state.get('minimum',0)),Maximum=float(state.get('maximum',1)),Value=float(value) if available else 0.)
        info[i]=dict(state,available=available)
    return rows,info

class ControllerCatalog(CatalogModel):
    """Pure cache/draft boundary; the adapter owns all authoritative data."""
    def __init__(self,adapter,schedule=None,commands_factory=None):
        super().__init__(schedule=schedule,capacity=4)
        self.adapter=adapter;self._source=OrderedDict();self._revisions={};self._info={}
        self._serial=count(1);self._session=adapter.Session();self._status=adapter.Status();self._sync_count=0
        if commands_factory is None:
            from commands import CommandService
            commands_factory=CommandService
        self._commands=commands_factory(self)

    @property
    def IsLive(self):return True
    @property
    def Status(self):return self._status
    def ActiveContext(self):return self.adapter.ActiveContext()
    def Choices(self,name,context):return self.adapter.Choices(name,context)
    def HasContext(self,context):return self.adapter.Exists(tuple(context))
    def Inspect(self,context,slot):
        context=self._context(context);slot=self._slot(slot)
        self.RefreshDefinitions(context,slot);self.Sync()
        return self.Info(context,slot)
    def RefreshDefinitions(self,context=None,slot=None):
        refresh=getattr(self.adapter,'RefreshDefinitions',None)
        if refresh:refresh(context,slot)

    def _context(self,context):
        if self._closed:raise RuntimeError('Model is closed')
        if not isinstance(context,(tuple,list)) or len(context)!=3:raise ValueError('Invalid context')
        context=tuple(context)
        if not self.adapter.Exists(context):raise ValueError('Context was removed')
        if context not in self._source:self._sync_context(context)
        self._source.move_to_end(context)
        return context

    def _sync_context(self,context):
        rows,info=project_records(self.adapter.Read(context))
        previous=self._source.get(context);old_info=self._info.get(context)
        if previous is None:
            self._source[context]=rows;self._info[context]=info
            self._revisions[context]=[next(self._serial) for _ in rows]
            while len(self._source)>self._capacity:
                key,_=self._source.popitem(last=False)
                self._info.pop(key,None);self._revisions.pop(key,None);self._cache.pop(key,None)
            return
        slots=metadata=0
        for i,row in enumerate(rows):
            changed_meta=metadata_signature(row,info[i])!=metadata_signature(previous[i],old_info[i])
            changed_display=bool(info[i] or old_info[i]) and tuple(info[i].get(n) for n in DISPLAY_FIELDS)!=tuple(old_info[i].get(n) for n in DISPLAY_FIELDS)
            if row!=previous[i] or changed_meta or changed_display:
                slots|=1<<i
                previous[i]=row
                cached=self._cache.get(context)
                if cached:cached[0][i].clear();cached[0][i].update(row)
            if changed_meta:
                metadata|=1<<i;self._revisions[context][i]=next(self._serial)
        self._info[context]=info
        if slots:self._queue(context,slots,metadata)

    def Info(self,context,slot):
        return self._info[self._context(context)][self._slot(slot)]

    def ValueText(self,context,slot):
        info=self.Info(context,slot);row=self.GetCatalog(context)[slot]
        if not info:return '—'
        if info.get('mode')=='pulse' or info.get('value_source')=='pulse':return 'Pulse'
        if not info['available']:return 'Unavailable'
        return format(row['Value'],'.4g')

    def Sync(self):
        observation=getattr(self.adapter,'Observation',nullcontext)
        with observation():self._sync_observation()

    def _sync_observation(self):
        self._sync_count+=1
        session=self.adapter.Session()
        session_changed=session!=self._session
        if session_changed:
            self._session=session;self._generation+=1
            for key in self._revisions:self._revisions[key]=[next(self._serial) for _ in range(16)]
        active=self.adapter.ActiveContext()
        contexts=set(self._source)|{c for c,_ in self._subscribers.values() if self.adapter.Exists(c)}|{active}
        # The source is a bounded projection; the controller registry is authoritative.
        for key in list(contexts):
            if self.adapter.Exists(key):self._sync_context(key)
            else:
                self._source.pop(key,None);self._info.pop(key,None);self._revisions.pop(key,None);self._cache.pop(key,None)
        status=self.adapter.Status();learn=bool(status.get('Learning'))
        if status!=self._status or learn!=self._learn or session_changed:
            self._status=status;self._learn=learn;self._learn_dirty=True;self._request_flush()
        # Routing/registry changes also need to reach pinned and following views.
        for identity,(key,_) in list(self._subscribers.items()):
            if not self.adapter.Exists(key):self._queue(key,65535,65535)

    def _reject_stale(self):raise StaleDraft('Mapping changed; reopen this control')
    def ActivationToken(self,*args):return self._commands.ActivationToken(*args)
    def ActivationCapability(self,*args):return self._commands.ActivationCapability(*args)
    def Activate(self,*args):return self._commands.Activate(*args)
    def Library(self,*args):return self._commands.Library(*args)
    def PrepareRename(self,*args,**kwargs):return self._commands.PrepareRename(*args,**kwargs)
    def Rename(self,*args):return self._commands.Rename(*args)
    def Health(self,context,slot):return self._commands.Health(context,slot)
    def Capabilities(self,context,slot):return self._commands.Capabilities(context,slot)
    def MappingSchema(self,*args):return self._commands.MappingSchema(*args)
    def ValueSchema(self,*args):return self._commands.ValueSchema(*args)
    def Assign(self,*args):return self._commands.Assign(*args)
    def TargetScope(self):return self.adapter.TargetScope()
    def TargetStart(self,*args):return self.adapter.Targets.Start(*args)
    def TargetCancel(self,identity):
        targets=getattr(self.adapter,'Targets',None)
        if targets:targets.Cancel(identity)
    def Configure(self,*args):return self._commands.Configure(*args)
    def Commit(self,*args):return self._commands.Commit(*args)
    def Ping(self,*args):return self._commands.Ping(*args)
    def CheckClear(self,*args):return self._commands.CheckClear(*args)
    def Clear(self,*args):return self._commands.Clear(*args)

    def PrepareClearDevice(self,*args):return self._commands.PrepareClearDevice(*args)
    def ClearDevice(self,*args):return self._commands.ClearDevice(*args)
    def Diagnostics(self):return self.adapter.Diagnostics()
    def ParameterDefinition(self,*args):return self._commands.ParameterDefinition(*args)
    def OpenNativeEditor(self,*args):return self._commands.OpenNativeEditor(*args)
    def DefinitionDraft(self,*args):return self._commands.DefinitionDraft(*args)
    def PreviewStyle(self,*args):return self._commands.PreviewStyle(*args)
    def ApplyDefinition(self,*args):return self._commands.ApplyDefinition(*args)
    def NativeEditorActions(self,definition,context,slot):
        return self.adapter.DefinitionModule().editor_actions(definition,self.Learn,bool(self.Info(context,slot).get('touched')))
    def Reveal(self,context,slot,token):
        context,slot,info=self._commands._target(context,slot,token)
        return self.adapter.Reveal(info)

    def Stats(self):return dict(super().Stats(),data_mode='controller',sync_calls=self._sync_count)

    def SetLearn(self,enabled):raise ValueError('Use the controller hardware to enter or exit LEARN')
    def UpdateValues(self,*args,**kwargs):raise ValueError('Live values belong to the controller')
    def Snapshot(self):raise ValueError('Use the demo model for synthetic tests')
    def Restore(self,*args):raise ValueError('Live controller data cannot be restored as a fixture')
    def ResetDemo(self):raise ValueError('Live controller data cannot be reset as a fixture')

class TDControllerAdapter:
    def __init__(self,owner):self.owner=owner;self._definitions_cache=OrderedDict();self._definition_session=None
    @property
    def controller(self):return self.owner.par.Controller.eval()
    @property
    def Targets(self):
        component=self.owner.op('base_targets')
        return component.ext.InspectorTargets if component else None
    def TargetScope(self):
        c=self.controller
        if not c:raise ValueError('Choose a controller')
        focus=c.par.Focuscomp.eval() if hasattr(c.par,'Focuscomp') else None
        return focus.path if focus else c.parent().path
    def Assign(self,key,slot,handle):
        if key!=self.ActiveContext():raise ValueError('Browse only: activate this Device first')
        c=self.controller
        if not c:raise ValueError('Choose a controller')
        kind='knob' if slot<8 else 'button'
        parameter=self.Targets.Resolve(handle,kind)
        state=c.AssignParameter(kind,slot%8+1,parameter)
        message='Assigned · open HW LEARN, then Ping'
        if c.State['Learning'] and state['connected'] and state['plugin']:
            try:
                offered=c.Offerparameter(state['id'])
                message='Assigned · awaiting hardware ACK' if offered else 'Assigned · Ping was rejected'
            except Exception as error:message='Assigned · Ping failed: '+str(error)
        return dict(id=state['id'],message=message)
    def ActiveContext(self):
        c=self.controller
        return tuple(c.GetLayoutContext().get('key') or EMPTY) if c else EMPTY
    def Session(self):
        c=self.controller
        if not c:
            self._definitions_cache.clear();self._definition_session=None
            if self.Targets:self.Targets.Reset()
            return None
        ext=c.ext.RotoPythonExt;follow=getattr(ext,'_follow',None)
        routing=c.GetLayoutContext()
        session=(id(ext),getattr(follow,'connection_generation',None),getattr(follow,'routing_epoch',None),routing.get('quarantined'),repr(routing.get('owner')))
        if session!=self._definition_session:
            self._definitions_cache.clear();self._definition_session=session
            if self.Targets:self.Targets.Reset()
        return session
    def Observation(self):
        c=self.controller
        return c.ext.RotoPythonExt._layout_manager().owner_observation() if c else nullcontext()

    def ActivationReason(self):
        c=self.controller
        if not c:return 'Choose a controller'
        e=c.ext.RotoPythonExt;m=e._layout_manager();h=e._host;f=getattr(e,'_follow',None)
        if m.legacy:return 'Device activation requires Parameter mapping'
        if h.learning:return 'Exit LEARN before activating Device'
        if h.touched or m.touched:return 'Release all controls before activating Device'
        if m.locked:return 'Unlock hardware before activating Device'
        if m.mutating or e._dispatching:return 'Wait for controller activation to finish'
        if f and f.paused:return 'Repair paused controller selection before activating Device'
        if f and (f.gated or f.backlog or f.pending):return 'Wait for pending controller selection to finish'
        if e._process is not None and not (h.connected and h.plugin):return 'Connect to PLUGIN before activating Device'
        return ''

    def Activate(self,key):
        reason=self.ActivationReason()
        if reason:raise ValueError(reason)
        c=self.controller
        if not self.Exists(key):raise ValueError('Context was removed')
        metadata=next((r for r in c.GetLayouts() if r['id']==key[0]),{})
        if metadata.get('category')=='COMP' and (metadata.get('owner') or {}).get('state')!='bound':raise ValueError('Layout owner unavailable')
        result=c.SelectPlugin(*key)
        routing=c.GetLayoutContext()
        if tuple(routing.get('key') or ())!=tuple(key) or routing.get('quarantined'):raise ValueError('Controller did not recover requested routing')
        return result

    def Status(self):
        c=self.controller
        if not c:return dict(Connected=False,Learning=False,Label='Choose controller')
        state=c.State
        routing=c.GetLayoutContext();follow=c.GetCompContext()
        return dict(Connected=state['Connected'],Learning=state['Learning'],Touched=state['Touched'],Bindingvalid=state['Bindingvalid'],Lasterror=state['Lasterror'],Label=routing['label'],Active=self.ActiveContext(),Locked=routing.get('locked',False),SelectedTrack=routing.get('selected_track_id'),SelectedDevice=routing.get('selected_plugin_id'),Follow=follow.get('enabled',False),FollowStatus=follow.get('status',''),FollowError=follow.get('error',''),Gated=follow.get('gated',False),ActivationReason=self.ActivationReason(),Legacy=routing.get('legacy',False),Quarantined=routing.get('quarantined',False),RoutingEpoch=getattr(c.ext.RotoPythonExt._follow,'routing_epoch',None),ContextOwners={r['id']:dict(category=r.get('category','LEGACY'),owner=deepcopy(r.get('owner'))) for r in c.GetLayouts()} if not routing.get('legacy') else {})
    def Exists(self,key):
        c=self.controller
        if not c:return key==EMPTY
        manager=c.ext.RotoPythonExt._layout_manager()
        if manager.legacy:return key==EMPTY
        try:manager.plugin(*key);return True
        except ValueError:return False
    def Choices(self,name,key):
        c=self.controller
        if not c:return [('unconfigured','Choose controller')]
        if c.GetLayoutContext().get('legacy'):return [('unconfigured','Python registration' if name=='Device' else '—')]
        records=c.GetLayouts() if name=='Layout' else c.GetTracks(key[0]) if name=='Track' else c.GetPlugins(key[0],key[1])
        if name=='Layout':
            return [(r['id'],('COMP' if r.get('category')=='COMP' else 'CUSTOM' if r.get('category')=='CUSTOM' else 'Legacy')+' · '+r['name']) for r in records]
        return [(r['id'],r['name']) for r in records]
    def Registry(self):return self.controller.GetLayoutRegistry()

    def Rename(self,key,name,intent,fingerprint,validate):
        # All reads, preflight and mutation execute synchronously in this TD call.
        c=self.controller;snapshot=c.GetLayoutRegistry()
        if fingerprint(snapshot,key)!=intent['fingerprint']:raise ValueError('Rename definition changed; reopen draft')
        status=self.Status()
        validate(status)
        reason=self.ActivationReason()
        if reason:raise ValueError(reason)
        if status.get('Quarantined'):raise ValueError('Recover the Layout before Rename')
        layout=next(r for r in snapshot['records'] if r['id']==key[0])
        if layout.get('category')=='COMP' and (layout.get('owner') or {}).get('state')!='bound':raise ValueError('Layout owner unavailable')
        track=next(t for t in layout['tracks'] if t['id']==key[1]);device=next(p for p in track['plugins'] if p['id']==key[2])
        kind=intent['kind']
        if kind not in ('Layout','Track','Device'):raise ValueError('Invalid Rename scope')
        if kind=='Device' and device.get('focus_comp') and device.get('name_mode')!='manual' and not intent['manual']:
            raise ValueError('Linked Device naming requires explicit manual naming opt-out')
        c.CheckLayoutRevision(snapshot['revision'])
        if kind=='Layout':return c.RenameLayout(key[0],name)
        if kind=='Track':return c.RenameTrack(key[0],key[1],name)
        return c.RenamePlugin(*key,name)

    def Library(self,key):
        c=self.controller;rows=deepcopy(c.GetPluginTargets(*key))
        active=key==self.ActiveContext()
        for row in rows:
            locator=row.get('comp','')
            row['comp']=normpath(c.path+'/'+locator) if locator and not locator.startswith('/') else locator
            target=c.op(locator) if locator else None
            par=getattr(target.par,row.get('parameter',''),None) if target and target.valid else None
            row['parameter_style']=par.style if par is not None else ''
            row.update(library_key=tuple(key)+(row['id'],),mapped=False,connected=False,plugin=False,projection='library' if active else 'last-saved preview')
            if row.get('mode')=='pulse':row['value']=None
        return rows

    def Read(self,key):
        c=self.controller
        if not c:return []
        manager=c.ext.RotoPythonExt._layout_manager()
        if key==self.ActiveContext() and not c.GetLayoutContext().get('quarantined'):
            # Current bindings are complete snapshots; catalog can include history.
            rows=c.GetControlStates()
        else:
            record=manager.plugin(*key);library={r['id']:r for r in self.Library(key)}
            rows=[]
            for target in record['targets']:
                row=dict(library.get(target['id'],target),binding_type='parameter',mapped=False,connected=False,plugin=False,projection='last-saved preview')
                if key==self.ActiveContext() and manager.quarantined:row.update(value=None,valid=False,error='Activate the repaired Layout first')
                rows.append(row)
        return self._definitions(rows,key)

    def RefreshDefinitions(self,context=None,slot=None):
        if context is None:self._definitions_cache.clear();return
        cached=self._definitions_cache.get(tuple(context))
        if cached is not None:
            if slot is None:cached.clear()
            else:
                kind='knob' if slot<8 else 'button';number=slot%8+1
                for id,(signature,_) in list(cached.items()):
                    if signature[:2]==(kind,number):cached.pop(id,None)
    def _definitions(self,records,key):
        c=self.controller
        cache=self._definitions_cache.setdefault(tuple(key),{})
        self._definitions_cache.move_to_end(tuple(key))
        while len(self._definitions_cache)>4:self._definitions_cache.popitem(last=False)
        present=set()
        for info in records:
            if not info.get('parameter'):continue
            id=info['id'];present.add(id)
            signature=tuple(info.get(n) for n in ('kind','slot','comp','parameter','parameter_style','minimum','maximum','valid','error'))+tuple(info.get('menu_names',()))+tuple(info.get('menu_labels',()))
            previous=cache.get(id)
            if previous and previous[0]==signature:
                info.update(previous[1]);continue
            definition={}
            target=op(info.get('comp',''))
            par=getattr(target.par,info['parameter'],None) if target and target.valid else None
            if par is None:
                definition['definition_error']='Target unavailable'
                cache[id]=(signature,definition);info.update(definition);continue
            try:
                chain=c.op('binding').module.parameter_chain(par)
                definition['parameter_definition']=tuple((p.owner.id,p.owner.path,p.name,p.style,p.mode.name,p.readOnly,p.min,p.max,p.clampMin,p.clampMax,tuple(p.menuNames or ()),tuple(p.menuLabels or ())) for p in chain)
                if par.style=='Menu' and (tuple(par.menuNames or ())!=tuple(info.get('menu_names',())) or tuple(par.menuLabels or ())!=tuple(info.get('menu_labels',()))):
                    raise ValueError('Menu options changed; assign again and re-LEARN')
                if par.style in ('Float','Int') and any((p.clampMin and info['minimum']<p.min) or (p.clampMax and info['maximum']>p.max) for p in chain):
                    raise ValueError('Binding range exceeds target or bind master clamp limits')
            except (ValueError,AttributeError) as error:definition['definition_error']=str(error)
            cache[id]=(signature,definition);info.update(definition)
        for id in set(cache)-present:cache.pop(id,None)
        return records
    def Write(self,key,info,value):
        c=self.controller
        if key!=self.ActiveContext():raise ValueError('Browse only: activate this Device on the controller before editing')
        if c.State['Learning']:raise ValueError('Exit LEARN before editing Value')
        current=c.GetControlState(info['id'])
        if current['touched']:raise ValueError('Release the control before editing')
        c.SetValue(value,info['id'])
    def Ping(self,key,info):
        if key!=self.ActiveContext():raise ValueError('Browse only: activate this Device first')
        return self.controller.Offerparameter(info['id'])
    def Clear(self,key,info):
        if key!=self.ActiveContext():raise ValueError('Browse only: activate this Device first')
        return self.controller.RemoveControl(info['id'])
    def ClearDevice(self,key):
        if key!=self.ActiveContext():raise ValueError('Browse only: activate this Device first')
        return self.controller.RemoveAllControls()
    def Diagnostics(self):
        c=self.controller
        return dict(state=dict(c.State),routing=dict(c.GetLayoutContext()),follow=dict(c.GetCompContext())) if c else dict(state={},routing={},follow={})
    def DefinitionModule(self):return self.owner.op('base_commands/parameter_definition').module
    def StyleModule(self):return self.owner.op('base_commands/style_migration').module
    def EditModule(self):return self.owner.op('base_commands/definition_edit').module
    def _definition_guard(self,key,info):
        c=self.controller
        if key!=self.ActiveContext():raise ValueError('Browse only: activate this Device first')
        if c.GetLayoutContext().get('quarantined'):raise ValueError('Activate the repaired Layout first')
        if c.State['Learning']:raise ValueError('Exit LEARN before editing native definition')
        if c.State['Touched'] or c.GetControlState(info['id'])['touched']:raise ValueError('Release controls before editing native definition')
    def DefinitionDraft(self,key,info):
        self._definition_guard(key,info)
        draft=self.EditModule().begin(info,self._native_parameter,self._definition_ranges(info))
        if draft['style'] in ('Float','Int'):
            draft['style_snapshot']=self.StyleModule().begin(self._native_parameter(info))
            draft['style_library']=self._style_signature(info)
        return draft
    def ApplyDefinition(self,key,info,draft,patch):
        self._definition_guard(key,info)
        if patch.get('style',draft['style'])!=draft['style']:
            return self._apply_style(key,info,draft,patch)
        patch={k:v for k,v in patch.items() if k not in ('style','style_value')}
        def reconcile():
            # ConfigureControl preserves stable registration ID/index and replaces
            # only changed wire semantics. It explicitly unmaps the old hardware.
            c=self.controller
            try:c.ConfigureControl(info['id'])
            finally:
                current=c.GetControlState(info['id'])
                if not current['mapped']:
                    c.store('needs_relearn',tuple(set(c.fetch('needs_relearn',()))|{info['id']}))
                    c.ext.RotoPythonExt._publish()
            c.ext.RotoPythonExt._layout_manager().capture(force=True)
        return self.EditModule().apply(info,draft,patch,self._native_parameter,self._definition_ranges(info),
            reconcile=reconcile if draft['style']=='Menu' else None)
    def _style_signature(self,info):
        c=self.controller;manager=c.ext.RotoPythonExt._layout_manager();rows=[];count=0
        names=('id','kind','slot','mode','button_type','index','identity','label','minimum','maximum')
        def add(scope,record,relative=True):
            nonlocal count
            count+=1
            if count>16384:raise ValueError('Style library exceeds bounded scan limit')
            if self.StyleModule().matches(record,info['comp'],info['parameter'],c.path):
                rows.append((scope,tuple(record.get(n) for n in names)))
        if not manager.legacy:
            for layout in manager.data['records']:
                for track in layout['tracks']:
                    for plugin in track['plugins']:
                        scope=(layout['id'],track['id'],plugin['id'])
                        for record in plugin['targets']:add(scope,record)
                        for key in ('page_targets','parameter_assignments'):
                            for record in plugin['state'].get(key,[]):add(scope+(key,),record)
            for record in c.fetch('page_targets',[]):add(('active-pages',),record)
        # Include authoritative wire index/hash; Value/ACK traffic is excluded.
        ext=c.ext.RotoPythonExt
        if ext._collection:
            for key,binding in ext._collection.bindings.items():
                if binding.parameter is None:continue
                target=ext._host.controls[key]
                add(('active',),dict(c.GetControlState(binding.id),index=target.index,identity=target.target_id))
        return tuple(sorted(rows,key=repr))

    def _style_foreign_guard(self,info):
        # Standard hosts can be named arbitrarily; identify their source DAT.
        controllers={dat.parent().path:dat.parent() for dat in root.findChildren(name='RotoPythonExt',type=textDAT)}.values()
        if len(controllers)>128:raise ValueError('Too many controller owners to audit Style inline')
        module=self.StyleModule();count=0
        for foreign in controllers:
            if foreign==self.controller:continue
            records=list(foreign.fetch('control_catalog',[]))
            registry=foreign.fetch('layout_registry',{}) or {}
            for layout in registry.get('records',[]):
                for track in layout.get('tracks',[]):
                    for plugin in track.get('plugins',[]):
                        records.extend(plugin.get('targets',[]));records.extend(plugin.get('state',{}).get('page_targets',[]))
            for record in records:
                count+=1
                if count>16384:raise ValueError('Other-controller Style audit exceeds bounded scan limit')
                if module.matches(record,info['comp'],info['parameter'],foreign.path):
                    raise ValueError('Another controller also registers this target; use TD Definition / coordinated repair')

    def PreviewStyle(self,key,info,draft,patch):
        self._definition_guard(key,info)
        c=self.controller;ext=c.ext.RotoPythonExt;manager=ext._layout_manager()
        if ext._collection is None or manager.legacy:raise ValueError('Style migration requires a managed parameter collection')
        if self._style_signature(info)!=draft['style_library']:raise ValueError('Saved Style registrations changed; reopen draft')
        self._style_foreign_guard(info)
        candidate=self.StyleModule().plan(self._native_parameter(info),draft['style_snapshot'],patch,self._definition_ranges(info))
        self._style_binding_guard(info,candidate)
        parameter=self.StyleModule().ParameterPreview(self._native_parameter(info),candidate)
        def identity(record):
            controls=c.op('controls').module.Controls([dict(record,parameter=parameter)])
            return next(controls.specs())['identity']
        # Validate every related candidate before replacement or hardware clear.
        self.StyleModule().rewrite_library(manager.data,c.fetch('page_targets',[]),
            info['comp'],info['parameter'],c.path,identity,candidate['style'])
        return candidate

    def _style_binding_guard(self,info,candidate):
        collection=self.controller.ext.RotoPythonExt._collection
        binding=collection.bindings[collection.key(info['id'])]
        if not binding.valid or binding.integer!=(binding.parameter.style=='Int'):
            raise ValueError('Mapping numeric Style is stale; repair / re-LEARN before migration')
        if binding.value!=candidate['value']:
            raise ValueError('Value update is pending; retry Style preview after it settles')

    def _apply_style(self,key,info,draft,patch):
        self.PreviewStyle(key,info,draft,patch)
        c=self.controller;ext=c.ext.RotoPythonExt;manager=ext._layout_manager()
        # Capture preflight must succeed before native replacement or hardware clear.
        manager.snapshot(manager.record()['id'],manager.record()['name'])
        data=deepcopy(manager.data)
        fields=('page_targets','parameter_assignments','control_overrides','needs_relearn')
        stored={n:deepcopy(c.fetch(n,{} if n=='control_overrides' else [])) for n in fields}
        key=ext._collection.key(info['id']);target=ext._host.controls[key];old_identity=target.target_id
        watcher=c.op('base_targets/watch_'+key[0]+str(key[1]));watching=watcher.par.active.eval()
        par=self._native_parameter(info)
        def mark_pending():
            c.store('needs_relearn',tuple(set(c.fetch('needs_relearn',()))|{info['id']}))
            ext._publish()
        def reconcile():
            c.ConfigureControl(info['id'])
            def identity(record):
                candidate=c.op('controls').module.Controls([dict(record,parameter=par)])
                return next(candidate.specs())['identity']
            registry,pages,ids=self.StyleModule().rewrite_library(manager.data,c.fetch('page_targets',[]),
                info['comp'],info['parameter'],c.path,identity,par.style)
            manager.data=registry;manager.save();c.store('page_targets',pages)
            c.store('needs_relearn',tuple(set(c.fetch('needs_relearn',()))|set(ids)))
            mark_pending();ext._layout_dirty=True;manager.capture(force=True)
        def compensate():
            c.ConfigureControl(info['id'])
            ext._host.controls[key].target_id=old_identity
            manager.data=deepcopy(data);manager.save()
            for name,value in stored.items():c.store(name,deepcopy(value))
            mark_pending();ext._layout_dirty=True;manager.capture(force=True)
        watcher.par.active=False
        try:return self.StyleModule().apply(par,draft['style_snapshot'],patch,self._definition_ranges(info),reconcile,compensate)
        finally:watcher.par.active=watching

    def _definition_ranges(self,info):
        c=self.controller;active=self.ActiveContext();ranges={};count=0
        def add(context,record,relative=False):
            nonlocal count
            count+=1
            if count>4096:raise ValueError('Mapping library exceeds inline bounds scan limit; use TD Definition')
            if not record.get('parameter'):return
            comp=record.get('comp','')
            if not isinstance(comp,str):return
            if relative and not comp.startswith('/'):comp=normpath(c.path+'/'+comp)
            if comp==info['comp'] and record.get('parameter')==info['parameter']:
                try:ranges[(tuple(context),record['id'])]=(float(record['minimum']),float(record['maximum']))
                except (KeyError,TypeError,ValueError):raise ValueError('Saved mapping limits unavailable; repair mapping before editing bounds')
        manager=c.ext.RotoPythonExt._layout_manager()
        if not manager.legacy:
            removed=set(c.fetch('removed_controls',[]))
            for layout in manager.data['records']:
                for track in layout['tracks']:
                    for plugin in track['plugins']:
                        context=(layout['id'],track['id'],plugin['id'])
                        for record in plugin['targets']:
                            if context!=active or record.get('id') not in removed:add(context,record,True)
            for record in c.fetch('page_targets',[]):
                if record.get('id') not in removed:add(active,record,True)
        # Active catalog overwrites saved/page snapshots for the same stable ID.
        for record in c.GetControlCatalog():add(active,record)
        return tuple((context,id,low,high) for (context,id),(low,high) in sorted(ranges.items()))
    def _native_parameter(self,info):
        target=op(info.get('comp',''))
        if not target or not target.valid:return None
        return getattr(target.par,info.get('parameter',''),None)
    def ParameterDefinition(self,info,learning=False,touched=False):
        return self.DefinitionModule().read(info,self._native_parameter,learning,touched)
    def OpenNativeEditor(self,info,kind,learning=False,touched=False):
        return self.DefinitionModule().open_editor(info,kind,self._native_parameter,ui.openCOMPEditor,learning,touched)
    def Reveal(self,info):
        c=self.controller
        if not c or not info.get('parameter'):raise ValueError('No native target to reveal')
        target=op(info.get('comp',''))
        if not target or not target.valid or not getattr(target.par,info['parameter'],None):raise ValueError('Target unavailable; use Target picker to repair')
        pane=ui.panes.current
        if not pane or not pane.open or pane.type.name!='NETWORKEDITOR':
            pane=next((p for p in ui.panes if p.open and p.type.name=='NETWORKEDITOR'),None)
        if not pane:raise ValueError('Reveal requires an existing Network Editor pane')
        destination=target.parent()
        # Follow samples selected children. Navigate with no selection so a saved
        # child selection cannot silently route to another linked Device.
        if c.GetCompContext().get('enabled'):
            for child in tuple(destination.selectedChildren):child.selected=False
        pane.owner=destination
        # home() schedules native viewport changes beyond this call.
        # Direct coordinates keep repeated Reveal at a readable fixed scale.
        pane.zoom=1.0
        pane.x=target.nodeX+target.nodeWidth/2
        pane.y=target.nodeY+target.nodeHeight/2
        return target.path
    def Configure(self,key,info,values):
        if key!=self.ActiveContext():raise ValueError('Browse only: activate this Device first')
        return self.controller.ConfigureControl(info['id'],**values)

class InspectorModel(ControllerCatalog):
    def __init__(self,ownerComp):
        self.ownerComp=ownerComp;self._queued_run=None;self._sync_run=None
        factory=ownerComp.op('base_commands/InspectorCommands').module.CommandService
        super().__init__(TDControllerAdapter(ownerComp),schedule=self._schedule_flush,commands_factory=factory)
        self._sync_context(self.ActiveContext());self.Sync()
    def _schedule_flush(self):self._queued_run=run('args[0].Dispatch()',self,endFrame=True)
    def Dispatch(self):self._queued_run=None;return super().Flush()
    def Flush(self):
        if self._queued_run:self._queued_run.kill();self._queued_run=None
        return super().Flush()
    def RequestSync(self):
        if not self._sync_run:self._sync_run=run('args[0].SyncController()',self,endFrame=True)
    def SyncController(self):self._sync_run=None;self.Sync()
    def ControllerData(self):
        c=self.adapter.controller
        return c.op('inspector/targets') if c else None
    def ControllerMetadata(self):
        c=self.adapter.controller
        return c.op('inspector/context_state') if c else None
    def WatchOwners(self):
        c=self.adapter.controller
        if not c:return []
        owners=[c,c.op('base_state'),c.op('inspector/title')]
        for key in {context for context,_ in self._subscribers.values()}:
            if not self.HasContext(key):continue
            for info in self._info.get(key,[]):
                target=op(info.get('comp','')) if info else None
                if target and target not in owners:owners.append(target)
                for definition in info.get('parameter_definition',()):
                    master=op(definition[1])
                    if master and master not in owners:owners.append(master)
        return [o for o in owners if o]
    def WatchPars(self):
        names={'Learning','Connected','Plugin','Touched','Bindingvalid','Lasterror','Targetid','text','Followcomp','Layout','Track','Plugin','Focuscomp'}
        for key in {context for context,_ in self._subscribers.values()}:
            for info in self._info.get(key,[]):
                if info.get('parameter'):names.add(info['parameter'])
                names.update(d[2] for d in info.get('parameter_definition',()))
        return ' '.join(sorted(names))
    def Subscribe(self,*args):
        result=super().Subscribe(*args);self.RefreshWatchers();return result
    def Unsubscribe(self,*args):super().Unsubscribe(*args);self.RefreshWatchers()
    def RefreshWatchers(self):
        watcher=self.ownerComp.op('controller_parameters')
        metadata=self.ownerComp.op('controller_registry')
        if metadata:metadata.par.active=bool(self.adapter.controller)
        catalog=self.ownerComp.op('controller_catalog')
        if catalog:catalog.par.active=bool(self.adapter.controller)
        if watcher:
            watcher.par.active=bool(self.adapter.controller)
            # Refresh expressions only when selected target owners/pars change.
            owners=self.WatchOwners();names=self.WatchPars()
            signature=(tuple((o.id,o.path) for o in owners),names)
            if signature!=getattr(self,'_watch_signature',None):
                self._watch_signature=signature
                watcher.par.active=False;watcher.par.op.expr=''
                watcher.par.op=' '.join(o.path for o in owners);watcher.par.pars=names;watcher.par.active=bool(self.adapter.controller)
    def Sync(self):
        super().Sync()
        if hasattr(self,'ownerComp'):self.RefreshWatchers()
    def onDestroyTD(self):
        for pending in (self._queued_run,self._sync_run):
            if pending:pending.kill()
        if self.adapter.Targets:self.adapter.Targets.Reset()
        self.Shutdown()
