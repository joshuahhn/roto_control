"""Shared controller projection. Browse never changes hardware routing."""
from collections import OrderedDict
from itertools import count
import math
try:
    from InspectorModel import CatalogModel, StaleDraft, FIELDS
except ModuleNotFoundError as error:
    if error.name!='InspectorModel':raise
    from model import CatalogModel, StaleDraft, FIELDS

EMPTY=('unconfigured','unconfigured','unconfigured')
META_FIELDS=('id','mode','valid','binding_type','button_type','parameter_style','parameter_definition','definition_error','requires_relearn','available','error')
DISPLAY_FIELDS=('value_label','mapped','connected','plugin','touched')

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
        value=state.get('value');available=isinstance(value,(int,float)) and math.isfinite(value)
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
        if not info['available']:return 'Unavailable'
        return format(row['Value'],'.4g')

    def Sync(self):
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
        session=(id(ext),getattr(follow,'connection_generation',None))
        if session!=self._definition_session:
            self._definitions_cache.clear();self._definition_session=session
            if self.Targets:self.Targets.Reset()
        return session
    def Status(self):
        c=self.controller
        if not c:return dict(Connected=False,Learning=False,Label='Choose controller')
        state=c.State
        routing=c.GetLayoutContext();follow=c.GetCompContext()
        return dict(Connected=state['Connected'],Learning=state['Learning'],Touched=state['Touched'],Bindingvalid=state['Bindingvalid'],Lasterror=state['Lasterror'],Label=routing['label'],Active=self.ActiveContext(),Locked=routing.get('locked',False),SelectedTrack=routing.get('selected_track_id'),SelectedDevice=routing.get('selected_plugin_id'),Follow=follow.get('enabled',False),FollowStatus=follow.get('status',''),FollowError=follow.get('error',''),Gated=follow.get('gated',False))
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
        return [(r['id'],r['name']) for r in records]
    def Read(self,key):
        c=self.controller
        if not c:return []
        if key==self.ActiveContext():return self._definitions(c.GetControlCatalog(),key)
        manager=c.ext.RotoPythonExt._layout_manager();record=manager.plugin(*key)
        specs=[];missing=[]
        # Resolve independently: a broken inactive target must not stop all views.
        for target in record['targets']:
            try:
                resolved,unavailable=manager.resolve(dict(record,targets=[target]))
                specs.extend(resolved);missing.extend(dict(t,error='Target unavailable') for t in unavailable)
            except (ValueError,AttributeError) as error:missing.append(dict(target,error=str(error)))
        rows=[]
        for spec in specs:
            par=spec['parameter'];value=0 if spec['mode']=='pulse' else c.op('binding').module.parameter_value(par)
            menu_names=list(par.menuNames) if par.style=='Menu' else []
            menu_labels=list(par.menuLabels) if par.style=='Menu' else []
            rows.append(dict(spec,parameter=par.name,comp=par.owner.path,value=value,valid=par.owner.valid,binding_type='parameter',parameter_style=par.style,mapped=False,connected=False,plugin=False,value_label=(menu_labels[int(value)] if 0<=int(value)<len(menu_labels) else '') if menu_labels else '',menu_names=menu_names,menu_labels=menu_labels))
        rows.extend(dict(t,comp=(c.op(t['comp']).path if c.op(t['comp']) else t['comp']),value=None,valid=False) for t in missing)
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
    def Reveal(self,info):
        c=self.controller
        if not c or not info.get('parameter'):raise ValueError('No native target to reveal')
        if c.GetCompContext().get('enabled'):raise ValueError('Turn off controller Follow before Reveal; pane selection can change routing')
        target=op(info.get('comp',''))
        if not target or not target.valid or not getattr(target.par,info['parameter'],None):raise ValueError('Target unavailable; use Target picker to repair')
        pane=ui.panes.current
        if not pane or pane.type.name!='NETWORKEDITOR':raise ValueError('Reveal requires an existing Network Editor pane')
        pane.owner=target
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
