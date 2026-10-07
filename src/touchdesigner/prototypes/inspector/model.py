"""Shared, bounded demo catalog. No MIDI or production-controller calls."""
from collections import OrderedDict, deque
from collections.abc import Mapping
from itertools import product
from types import MappingProxyType
import math
import weakref

CONTEXTS = tuple(product(('main','live'), ('track1','track2'), ('pixelsort','fractal')))
FIELDS = ('Label','Destination','Minimum','Maximum','Value')

class StaleDraft(ValueError):
    pass

class CatalogModel:
    def __init__(self, schedule=None, capacity=4):
        if not isinstance(capacity,int) or isinstance(capacity,bool) or capacity<1:
            raise ValueError('Cache capacity must be a positive integer')
        self._capacity=capacity
        self._schedule=schedule
        self._cache=OrderedDict()
        self._source={c:[self._fixture(c,i) for i in range(16)] for c in CONTEXTS}
        self._revisions={c:[0]*16 for c in CONTEXTS}
        self._generation=1
        self._learn=False
        self._subscribers={}
        self._pending={}
        self._learn_dirty=False
        self._scheduled=False
        self._closed=False
        self._errors=deque(maxlen=8)
        self._counts=dict(received=0,changed=0,flushes=0,notifications=0,hits=0,misses=0,rejected=0)

    @staticmethod
    def _fixture(context,slot):
        specs=[('Sort criterion','Sortcrit',0.,4.,4.),('Low threshold','Lowthresh',0.,1.,.45),('High threshold','Highthresh',0.,1.,.85),('Mix','Mix',0.,1.,1.)] if context[2]=='pixelsort' else [('Power','Power',0.,16.,8.16)]
        name,target,low,high,value=specs[slot] if slot<len(specs) else ('Unassigned','',0.,1.,0.)
        return dict(Label=name,Destination=target,Minimum=low,Maximum=high,Value=value)

    def _context(self,context):
        if not isinstance(context,(tuple,list)) or len(context)!=3 or not all(isinstance(v,str) for v in context):
            raise ValueError('Invalid context')
        key=tuple(context)
        if key not in self._source:raise ValueError('Unknown demo context')
        if self._closed:raise RuntimeError('Model is closed')
        return key

    @staticmethod
    def _slot(slot):
        if not isinstance(slot,int) or isinstance(slot,bool) or not 0<=slot<16:
            raise ValueError('Invalid slot')
        return slot

    @staticmethod
    def _number(value):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
            raise ValueError('Expected a finite number')
        return float(value)

    def _record(self,record):
        if not isinstance(record,Mapping) or set(record)!=set(FIELDS):raise ValueError('Invalid mapping fields')
        values=dict(record)
        for n in ('Label','Destination'):
            if not isinstance(values[n],str) or len(values[n])>128:raise ValueError('Invalid mapping text')
        for n in ('Minimum','Maximum','Value'):values[n]=self._number(values[n])
        if values['Minimum']>=values['Maximum']:raise ValueError('Minimum must be less than maximum')
        if not values['Minimum']<=values['Value']<=values['Maximum']:raise ValueError('Value is outside the range')
        return values

    @property
    def Generation(self):return self._generation
    @property
    def Learn(self):return self._learn

    def GetCatalog(self,context):
        context=self._context(context)
        entry=self._cache.get(context)
        if entry is None:
            rows=[dict(row) for row in self._source[context]]
            entry=(rows,tuple(MappingProxyType(row) for row in rows))
            self._cache[context]=entry;self._counts['misses']+=1
            if len(self._cache)>self._capacity:self._cache.popitem(last=False)
        else:
            self._cache.move_to_end(context);self._counts['hits']+=1
        return entry[1]

    def GetToken(self,context,slot):
        context=self._context(context);slot=self._slot(slot)
        return (self._generation,context,slot,self._revisions[context][slot])

    def Subscribe(self,identity,context,callback):
        context=self._context(context)
        if not callable(callback):raise ValueError('Invalid subscriber')
        reference=weakref.WeakMethod(callback) if getattr(callback,'__self__',None) is not None else callback
        self._subscribers[identity]=(context,reference)
        return self.GetCatalog(context)

    def Unsubscribe(self,identity,callback=None):
        current=self._subscribers.get(identity)
        if current is None:return
        reference=current[1]
        subscribed=reference() if isinstance(reference,weakref.WeakMethod) else reference
        # TD may destroy an old extension after its replacement has subscribed.
        if callback is None or subscribed==callback:self._subscribers.pop(identity,None)

    def _queue(self,context,slots=0,metadata=0):
        previous=self._pending.get(context,(0,0))
        self._pending[context]=(previous[0]|slots,previous[1]|metadata)
        self._request_flush()

    def _request_flush(self):
        if not self._scheduled:
            self._scheduled=True
            if self._schedule:self._schedule()

    def UpdateValues(self,context,updates,generation=None):
        try:
            context=self._context(context)
            if generation is not None and generation!=self._generation:raise StaleDraft('Stale update generation')
            if not isinstance(updates,Mapping) or len(updates)>16:raise ValueError('Invalid value batch')
            validated=[]
            for slot,value in updates.items():
                slot=self._slot(slot);value=self._number(value);row=self._source[context][slot]
                if not row['Minimum']<=value<=row['Maximum']:raise ValueError('Value is outside the range')
                validated.append((slot,value))
        except (ValueError,RuntimeError):
            self._counts['rejected']+=1;raise
        self._counts['received']+=len(validated)
        mask=0
        cached=self._cache.get(context)
        for slot,value in validated:
            if self._source[context][slot]['Value']!=value:
                self._source[context][slot]['Value']=value
                if cached:cached[0][slot]['Value']=value
                mask|=1<<slot
        if mask:
            self._counts['changed']+=mask.bit_count();self._queue(context,mask)
        return mask.bit_count()

    def Commit(self,context,slot,record,token):
        context=self._context(context);slot=self._slot(slot)
        if token!=self.GetToken(context,slot):raise StaleDraft('Mapping changed; reopen this control')
        values=self._record(record);old=self._source[context][slot]
        if old==values:return False
        metadata=any(old[n]!=values[n] for n in FIELDS if n!='Value')
        self._source[context][slot]=values
        if metadata:self._revisions[context][slot]+=1
        cached=self._cache.get(context)
        if cached:cached[0][slot].clear();cached[0][slot].update(values)
        self._queue(context,1<<slot,(1<<slot) if metadata else 0)
        return True

    def SetLearn(self,enabled):
        if not isinstance(enabled,bool):raise ValueError('Learn must be boolean')
        if self._closed:raise RuntimeError('Model is closed')
        if self._learn!=enabled:
            self._learn=enabled;self._learn_dirty=True;self._request_flush()

    def Invalidate(self,context=None):
        contexts=CONTEXTS if context is None else (self._context(context),)
        if context is None:self._generation+=1
        for key in contexts:
            self._cache.pop(key,None)
            self._revisions[key]=[v+1 for v in self._revisions[key]]
            self._queue(key,65535,65535)

    def Snapshot(self):
        return dict(rows={c:[dict(row) for row in rows] for c,rows in self._source.items()},learn=self._learn)

    def Restore(self,snapshot):
        if not isinstance(snapshot,dict) or set(snapshot)!= {'rows','learn'} or set(snapshot['rows'])!=set(CONTEXTS) or not isinstance(snapshot['learn'],bool):raise ValueError('Invalid snapshot')
        validated={}
        for context,rows in snapshot['rows'].items():
            if len(rows)!=16:raise ValueError('Invalid snapshot rows')
            validated[context]=[self._record(row) for row in rows]
        self._source=validated;self._learn=snapshot['learn'];self._learn_dirty=True
        self.Invalidate()

    def ResetDemo(self):
        self.Restore(dict(rows={c:[self._fixture(c,i) for i in range(16)] for c in CONTEXTS},learn=False))

    def Flush(self):
        pending,self._pending=self._pending,{}
        learn_dirty,self._learn_dirty=self._learn_dirty,False
        self._scheduled=False
        if not pending and not learn_dirty:return 0
        self._counts['flushes']+=1
        for identity,(context,reference) in list(self._subscribers.items()):
            if self._subscribers.get(identity)!=(context,reference):continue
            callback=reference() if isinstance(reference,weakref.WeakMethod) else reference
            if callback is None:self.Unsubscribe(identity);continue
            if context not in pending and not learn_dirty:continue
            slots,metadata=pending.get(context,(0,0))
            try:
                callback(context,slots,metadata,learn_dirty,self._generation)
                self._counts['notifications']+=1
            except Exception as error:
                self._errors.append(str(error));self.Unsubscribe(identity,callback)
        return len(pending)

    def Stats(self):
        return dict(self._counts,cache_contexts=len(self._cache),cache_capacity=self._capacity,source_contexts=len(self._source),subscribers=len(self._subscribers),pending_contexts=len(self._pending),pending_slots=sum(mask.bit_count() for mask,_ in self._pending.values()),scheduled=self._scheduled,subscriber_errors=list(self._errors),generation=self._generation)

    def Shutdown(self):
        self._closed=True;self._subscribers.clear();self._pending.clear();self._scheduled=False;self._cache.clear()

class InspectorModel(CatalogModel):
    def __init__(self,ownerComp):
        self.ownerComp=ownerComp
        self._queued_run=None
        self._demo_step=0
        super().__init__(schedule=self._schedule_flush,capacity=4)

    def _schedule_flush(self):
        self._queued_run=run('args[0].Dispatch()',self,endFrame=True)

    def Dispatch(self):
        self._queued_run=None
        return super().Flush()

    def Flush(self):
        if self._queued_run:
            self._queued_run.kill();self._queued_run=None
        return super().Flush()

    def StepDemo(self):
        self._demo_step=(self._demo_step+1)%100
        fraction=self._demo_step/100
        for context in CONTEXTS:
            values={i:row['Minimum']+fraction*(row['Maximum']-row['Minimum']) for i,row in enumerate(self.GetCatalog(context)) if row['Destination']}
            self.UpdateValues(context,values)

    def onDestroyTD(self):
        if self._queued_run:
            self._queued_run.kill();self._queued_run=None
        self.Shutdown()
