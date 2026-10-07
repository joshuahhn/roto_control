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
    def __init__(self,adapter,schedule=None):
        super().__init__(schedule=schedule,capacity=4)
        self.adapter=adapter;self._source=OrderedDict();self._revisions={};self._info={}
        self._serial=count(1);self._session=adapter.Session();self._status=adapter.Status();self._sync_count=0

    @property
    def IsLive(self):return True
    @property
    def Status(self):return self._status
    def ActiveContext(self):return self.adapter.ActiveContext()
    def Choices(self,name,context):return self.adapter.Choices(name,context)
    def HasContext(self,context):return self.adapter.Exists(tuple(context))

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
            signature=lambda r,s:tuple(r[n] for n in FIELDS if n!='Value')+tuple(s.get(n) for n in ('id','mode','valid','parameter_style','requires_relearn','available','error'))+tuple(s.get('menu_names',()))+tuple(s.get('menu_labels',()))
            changed_meta=signature(row,info[i])!=signature(previous[i],old_info[i])
            changed_display=tuple(info[i].get(n) for n in ('value_label','mapped','connected','plugin'))!=tuple(old_info[i].get(n) for n in ('value_label','mapped','connected','plugin'))
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

    def Commit(self,context,slot,record,token):
        self.Sync();context=self._context(context);slot=self._slot(slot)
        if token!=self.GetToken(context,slot):raise StaleDraft('Mapping changed; reopen this control')
        old=self.GetCatalog(context)[slot];values=dict(record)
        if set(values)!=set(FIELDS):raise ValueError('Invalid fields')
        if any(values[n]!=old[n] for n in FIELDS if n!='Value'):
            raise ValueError('Mapping metadata is read-only in this prototype')
        info=self.Info(context,slot)
        if not info or not info.get('valid') or not info.get('available'):raise ValueError('Target unavailable')
        if info.get('mode')=='pulse':raise ValueError('Pulse targets do not have an editable Value')
        value=self._number(values['Value'])
        if not old['Minimum']<=value<=old['Maximum']:raise ValueError('Value is outside the range')
        if value==old['Value']:return False
        self.adapter.Write(context,info,value)
        self.Sync()
        return True

    def _action_target(self,context,slot,token):
        self.Sync();context=self._context(context);slot=self._slot(slot)
        if token!=self.GetToken(context,slot):raise StaleDraft('Mapping changed; reopen this control')
        if context!=self.ActiveContext():raise ValueError('Browse only: activate this Device first')
        info=self.Info(context,slot)
        if not info or not info.get('id'):raise ValueError('No mapping at this control')
        return context,info

    def Ping(self,context,slot,token):
        context,info=self._action_target(context,slot,token)
        if not info.get('valid'):raise ValueError(info.get('error') or 'Target unavailable')
        if not info.get('connected') or not info.get('plugin'):raise ValueError('Connect to PLUGIN before Ping')
        if not self.Learn:raise ValueError('Open HW LEARN, select this control, then Ping')
        if not self.adapter.Ping(context,info):raise ValueError('Ping rejected; check hardware LEARN')
        self.Sync()
        return True

    def CheckClear(self,context,slot,token):
        context,info=self._action_target(context,slot,token)
        if self.Learn:raise ValueError('Exit LEARN before Clear')
        if info.get('touched'):raise ValueError('Release this control before Clear')
        return context,info

    def Clear(self,context,slot,token):
        context,info=self.CheckClear(context,slot,token)
        self.adapter.Clear(context,info)
        self.Sync()
        return True

    def Stats(self):return dict(super().Stats(),data_mode='controller',sync_calls=self._sync_count)

    def SetLearn(self,enabled):raise ValueError('Use the controller hardware to enter or exit LEARN')
    def UpdateValues(self,*args,**kwargs):raise ValueError('Live values belong to the controller')
    def Snapshot(self):raise ValueError('Use the demo model for synthetic tests')
    def Restore(self,*args):raise ValueError('Live controller data cannot be restored as a fixture')
    def ResetDemo(self):raise ValueError('Live controller data cannot be reset as a fixture')

class TDControllerAdapter:
    def __init__(self,owner):self.owner=owner
    @property
    def controller(self):return self.owner.par.Controller.eval()
    def ActiveContext(self):
        c=self.controller
        return tuple(c.GetLayoutContext().get('key') or EMPTY) if c else EMPTY
    def Session(self):
        c=self.controller
        if not c:return None
        ext=c.ext.RotoPythonExt;follow=getattr(ext,'_follow',None)
        return (id(ext),getattr(follow,'connection_generation',None))
    def Status(self):
        c=self.controller
        if not c:return dict(Connected=False,Learning=False,Label='Choose controller')
        state=c.State
        return dict(Connected=state['Connected'],Learning=state['Learning'],Label=c.GetLayoutContext()['label'],Active=self.ActiveContext())
    def Exists(self,key):
        c=self.controller
        if not c:return key==EMPTY
        try:c.ext.RotoPythonExt._layout_manager().plugin(*key);return True
        except ValueError:return False
    def Choices(self,name,key):
        c=self.controller
        if not c:return [('unconfigured','Choose controller')]
        records=c.GetLayouts() if name=='Layout' else c.GetTracks(key[0]) if name=='Track' else c.GetPlugins(key[0],key[1])
        return [(r['id'],r['name']) for r in records]
    def Read(self,key):
        c=self.controller
        if not c:return []
        if key==self.ActiveContext():return c.GetControlCatalog()
        record=c.ext.RotoPythonExt._layout_manager().plugin(*key)
        specs,missing=c.ext.RotoPythonExt._layout_manager().resolve(record)
        rows=[]
        for spec in specs:
            par=spec['parameter'];value=0 if spec['mode']=='pulse' else c.op('binding').module.parameter_value(par)
            menu_names=list(par.menuNames) if par.style=='Menu' else []
            menu_labels=list(par.menuLabels) if par.style=='Menu' else []
            rows.append(dict(spec,parameter=par.name,comp=par.owner.path,value=value,valid=par.owner.valid,binding_type='parameter',parameter_style=par.style,mapped=False,connected=False,plugin=False,value_label=(menu_labels[int(value)] if 0<=int(value)<len(menu_labels) else '') if menu_labels else '',menu_names=menu_names,menu_labels=menu_labels))
        rows.extend(dict(t,value=None,valid=False,error='Target unavailable') for t in missing)
        return rows
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

class InspectorModel(ControllerCatalog):
    def __init__(self,ownerComp):
        self.ownerComp=ownerComp;self._queued_run=None;self._sync_run=None
        super().__init__(TDControllerAdapter(ownerComp),schedule=self._schedule_flush)
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
        owners=[c.op('base_state'),c.op('inspector/title')]
        for key in {context for context,_ in self._subscribers.values()}:
            if not self.HasContext(key):continue
            for info in self._info.get(key,[]):
                target=op(info.get('comp','')) if info else None
                if target and target not in owners:owners.append(target)
        return [o for o in owners if o]
    def WatchPars(self):
        names={'Learning','Connected','Plugin','Targetid','text'}
        for key in {context for context,_ in self._subscribers.values()}:
            for info in self._info.get(key,[]):
                if info.get('parameter'):names.add(info['parameter'])
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
        self.Shutdown()
