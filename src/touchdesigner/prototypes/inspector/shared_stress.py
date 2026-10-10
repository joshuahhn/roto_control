"""Actual shared-model path, frame-paced by temporary TD instrumentation."""
import json
import statistics
import time
import traceback
from pathlib import Path

roots=[op('/inspector_below'),op('/inspector_popup')]
views=[c.ext.InspectorView for c in roots]
model=op('/inspector_model').ext.InspectorModel
key=('main','track1','pixelsort')
phases=[('both_idle','idle',240),('both_16_values_60hz','values',360),('both_burst32','burst',360),('both_identical','same',240),('both_8_contexts_60hz','contexts',360),('edit_apply_cancel_reuse','edit',360),('both_idle_after','idle',600)]
result={'environment':{'project':project.name,'build':str(app.build),'rate':project.cookRate},'phases':[],'failures':[]}
phase=-1;frame=0;done=False;state='starting';samples=[];dispatch_samples=[];last=None;original_dispatch=None
output_name='shared_stress_results.json'

def summary(values):
    if not values:return {}
    ordered=sorted(values)
    return dict(mean=statistics.fmean(ordered),p95=ordered[int((len(ordered)-1)*.95)],p99=ordered[int((len(ordered)-1)*.99)],maximum=ordered[-1])

def measured_dispatch():
    start=time.perf_counter()
    try:return original_dispatch()
    finally:dispatch_samples.append((frame,(time.perf_counter()-start)*1000))

def initialize():
    global snapshot,saved,original_dispatch
    snapshot=model.Snapshot()
    saved=[dict(context=v.Key(),selected=v.selected,draft={n:v._draft.par[n].eval() for n in ('Label','Destination','Minimum','Maximum','Value')},scroll=v._viewport.panel.scrollv.val) for v in views]
    for context in model._source:
        for i in range(16):
            row=dict(model.GetCatalog(context)[i]);row.update(Destination='Demo',Minimum=0.,Maximum=1.,Value=0.)
            model.Commit(context,i,row,model.GetToken(context,i))
    model.Flush()
    for v in views:
        v.CloseEditor()
        for n,x in zip(('Layout','Track','Device'),key):v.ownerComp.par[n]=x
        v.OnContext()
        if not v._main.isOpen:v._main.par.winopen.pulse()
    views[1].Action('slot1');views[1].Action('cancel')
    original_dispatch=model.Dispatch;model.Dispatch=measured_dispatch

def setup_phase():
    global phase,frame,state,samples,dispatch_samples,last,before
    phase+=1
    if phase==len(phases):finish();return
    state=phases[phase][0];frame=0;samples=[];dispatch_samples=[];last=None
    for v in views:v.CloseEditor()
    model.Flush()
    before=dict(model=model.Stats(),views=[v.Stats() for v in views],ops=[len(c.findChildren())+1 for c in roots],cpu_bytes=[sum(n.cpuMemory for n in [c]+c.findChildren()) for c in roots])

def end_phase():
    name,mode,length=phases[phase];measured=samples[60:]
    after=dict(model=model.Stats(),views=[v.Stats() for v in views],ops=[len(c.findChildren())+1 for c in roots],cpu_bytes=[sum(n.cpuMemory for n in [c]+c.findChildren()) for c in roots])
    result['phases'].append(dict(name=name,frames=length,warmup=60,producer_ms=summary([s['producer'] for s in measured]),dispatch_ms=summary([ms for f,ms in dispatch_samples if f>=60]),frame_interval_ms=summary([s['interval'] for s in measured if s['interval']]),process_cpu_mb_first=measured[0]['memory'],process_cpu_mb_last=measured[-1]['memory'],process_cpu_mb_range=[min(s['memory'] for s in measured),max(s['memory'] for s in measured)],model_received=after['model']['received']-before['model']['received'],model_flushes=after['model']['flushes']-before['model']['flushes'],notifications=after['model']['notifications']-before['model']['notifications'],text_writes=[a['text_writes']-b['text_writes'] for a,b in zip(after['views'],before['views'])],window_opens=[a['window_opens']-b['window_opens'] for a,b in zip(after['views'],before['views'])],before=before,after=after))
    assert after['model']['subscribers']==2
    assert after['model']['cache_contexts']<=4
    assert not after['model']['subscriber_errors']
    assert after['ops']==before['ops']
    assert all(v.Stats()['window_opens']==s['window_opens'] for v,s in zip(views,before['views']))
    write();setup_phase()

def tick():
    global frame,last
    if done:return
    try:
        if phase<0:setup_phase();return
        now=time.perf_counter();interval=(now-last)*1000 if last else None;last=now
        name,mode,length=phases[phase];start=time.perf_counter()
        if mode in ('values','burst','same','contexts','edit'):
            batches=32 if mode=='burst' else 1
            contexts=list(model._source) if mode=='contexts' else [key]
            for context in contexts:
                for b in range(batches):
                    value=.25 if mode=='same' else (frame%97+b/32)/100
                    model.UpdateValues(context,{i:(value+i/17)%1 for i in range(16)},generation=model.Generation)
            assert model.Stats()['pending_contexts']<=8
            assert model.Stats()['pending_slots']<=128
        if mode=='edit':
            for v in views:
                v.Action('slot'+str(frame%16));v._draft.par.Label='session '+str(frame%16)
                assert v.Action('apply' if frame%3==0 else 'cancel')
                v.ScrollWheel(-1 if frame%2 else 1)
            if frame%30==0:model.SetLearn(not model.Learn)
        producer=(time.perf_counter()-start)*1000
        perf=op('/inspector_shared_stress/null_performance')
        samples.append(dict(producer=producer,interval=interval,memory=perf['cpu_mem_used'].eval()))
        frame+=1
        if frame>=length:end_phase()
    except Exception:
        result['failures'].append(traceback.format_exc());finish()

def write():Path(project.folder+'/prototypes/inspector/'+output_name).write_text(json.dumps(result,indent=2))

def finish():
    global done,state
    done=True;state='complete'
    if original_dispatch:model.Dispatch=original_dispatch
    model.Restore(snapshot);model.Flush()
    for v,s in zip(views,saved):
        v.CloseEditor()
        for n,x in zip(('Layout','Track','Device'),s['context']):v.ownerComp.par[n]=x
        v.OnContext();v.Refresh()
        if s['selected'] is not None:
            v.Action('slot'+str(s['selected']))
            for n,x in s['draft'].items():v._draft.par[n]=x
        v._viewport.panel.scrollv=s['scroll']
    write();op('/inspector_shared_stress/execute_frames').par.active=False
