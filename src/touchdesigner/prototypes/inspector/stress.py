"""Live-TD inspector test harness; temporary Execute DAT, never exported.

Runs frame-paced synthetic traffic. No production controller calls. The dirty
path below is a measured alternative, not a production live-data adapter.
"""
import copy
import json
import math
import statistics
import time
import traceback
from pathlib import Path

roots = [op('/inspector_below'), op('/inspector_popup')]
modules = [c.op('ui').module for c in roots]
result = {'environment': {'project': project.name, 'build': str(app.build), 'rate': project.cookRate}, 'phases': [], 'checks': [], 'failures': []}
saved = []

def initialize():
    global saved
    saved=[]
    for c,u in zip(roots,modules):
        saved.append(dict(context={n:c.par[n].eval() for n in ('Layout','Track','Device')}, records=copy.deepcopy(u.records), selected=u.selected, learn=u.learn, scroll=c.op('container_scroll').panel.scrollv.val, draft={n:c.op('base_draft').par[n].eval() for n in ('Label','Destination','Minimum','Maximum','Value')}, main=c.op('window_main').isOpen, popup=c.op('window_editor').isOpen))

phases = [
 ('closed', [], 'idle', 240),
 ('below_idle', [0], 'idle', 240),
 ('popup_idle', [1], 'idle', 240),
 ('both_idle', [0,1], 'idle', 240),
 ('below_full_60hz', [0], 'full', 360),
 ('popup_full_60hz', [1], 'full', 360),
 ('both_full_60hz', [0,1], 'full', 360),
 ('below_dirty_60hz', [0], 'dirty', 360),
 ('popup_dirty_60hz', [1], 'dirty', 360),
 ('both_dirty_60hz', [0,1], 'dirty', 360),
 ('both_dirty_burst32', [0,1], 'burst', 360),
 ('both_shared_cached_60hz', [0,1], 'cached', 360),
 ('both_shared_cached_burst32', [0,1], 'cached_burst', 360),
 ('both_shared_cached_identical', [0,1], 'cached_same', 360),
 ('both_identical_feed', [0,1], 'same', 360),
 ('interactions', [0,1], 'stress', 600),
 ('both_idle_after', [0,1], 'idle', 240),
]
phase_index = -1
frame = 0
samples = []
previous_tick = None
counts_before = {}
phase_updates = 0
phase_writes = 0
ready = False
done = False
state = 'starting'
output_name = 'stress_results.json'
row_refs = [[u.content().op('slot'+str(i)+'/text_value') for i in range(16)] for u in modules]
last_display = [{},{}]

# Scope counts to exact OPs; ignore global TD caches/other networks.
def stats(c):
    nodes = [c]+c.findChildren()
    return dict(ops=len(nodes), cpu_bytes=sum(n.cpuMemory for n in nodes), gpu_bytes=sum(n.gpuMemory for n in nodes), cooks={n.path:n.totalCooks for n in nodes})

def summary(values):
    if not values: return {}
    v=sorted(values)
    return dict(mean=statistics.fmean(v),p50=v[len(v)//2],p95=v[int((len(v)-1)*.95)],p99=v[int((len(v)-1)*.99)],maximum=v[-1])

def check(label, fn):
    try:
        fn(); result['checks'].append({'name':label,'pass':True})
    except Exception:
        result['checks'].append({'name':label,'pass':False,'error':traceback.format_exc()})

def assert_equal(actual, expected):
    assert actual==expected, (actual,expected)

def correctness():
    for ix,(c,u) in enumerate(zip(roots,modules)):
        prefix=u.style+' / '
        u.close();u.records.clear()
        # Commit and cancel across all 8 contexts and all 16 slots.
        for layout in c.par.Layout.menuNames:
            for track in c.par.Track.menuNames:
                for device in c.par.Device.menuNames:
                    c.par.Layout=layout;c.par.Track=track;c.par.Device=device;u.context()
                    for slot in range(16):
                        u.action('slot'+str(slot));d=c.op('base_draft')
                        d.par.Label='test-'+layout+'-'+track+'-'+device+'-'+str(slot)
                        d.par.Destination='Demo';d.par.Minimum=0;d.par.Maximum=1;d.par.Value=slot/16
                        expected=d.par.Label.eval();u.action('apply')
                        assert_equal(u.records[(u.key(),slot)]['Label'],expected)
                        u.action('slot'+str(slot));d.par.Label='discard';u.action('cancel')
                        assert_equal(u.records[(u.key(),slot)]['Label'],expected)
        assert len(u.records)==128
        result['checks'].append({'name':prefix+'128 mapping/context Apply+Cancel cases','pass':True})
        # Bad input must keep editor open and preserve the old committed row.
        u.action('slot0');d=c.op('base_draft');old=copy.deepcopy(u.records[(u.key(),0)])
        for minimum,maximum in [(1,0),(1,1)]:
            d.par.Minimum=minimum;d.par.Maximum=maximum;u.action('apply')
            assert u.selected==0;assert_equal(u.records[(u.key(),0)],old)
        u.action('cancel')
        result['checks'].append({'name':prefix+'reversed/equal ranges rejected (non-finite input sanitized by TD Par)','pass':True})
        # Failure probe: invalid slot should not corrupt selected state.
        old_selected=u.selected
        try: u.action('slot16')
        except Exception: pass
        result['checks'].append({'name':prefix+'out-of-range action leaves state intact','pass':u.selected==old_selected,'actual':u.selected})
        u.selected=None;u.render()
        # Is there already a continuous row refresh? (Expected limitation today.)
        u.records[(u.key(),1)]['Value']=.314159
        row=row_refs[ix][1]
        observed=row.par.text.eval()
        result['checks'].append({'name':prefix+'record mutation refreshes row without render','pass':observed==format(.314159,'.3g'),'actual':observed,'expected':format(.314159,'.3g'),'classification':'prototype live-feed limitation'})
        u.render()
        # A live display update must not overwrite an unfinished editor draft.
        u.action('slot1');d.par.Label='draft-in-progress';d.par.Value=.777
        incremental(ix,{1:.123})
        assert_equal(d.par.Label.eval(),'draft-in-progress');assert_equal(d.par.Value.eval(),.777)
        assert_equal(row.par.text.eval(),'0.123')
        result['checks'].append({'name':prefix+'dirty value update preserves unfinished draft','pass':True})
        u.close()

# Synthetic path: update fixture values at current context, preserving edit data.
def feed(ix, values):
    u=modules[ix]
    for i,value in values.items():
        k=(u.key(),i)
        if k not in u.records:
            u.records[k]=u.fixture(i);u.records[k]['Destination']='Demo'
        u.records[k]['Value']=value

shared_values = {}

def cached_incremental(ix, values):
    global phase_writes
    for i,value in values.items():
        display=format(value,'.3g')
        if display != last_display[ix].get(i):
            row_refs[ix][i].par.text=display;last_display[ix][i]=display;phase_writes+=1

def incremental(ix, values):
    global phase_writes
    feed(ix,values)
    for i,value in values.items():
        display=format(value,'.3g')
        if display != row_refs[ix][i].par.text.eval():
            row_refs[ix][i].par.text=display;phase_writes+=1

def setup_phase():
    global phase_index,frame,samples,previous_tick,counts_before,phase_updates,phase_writes,ready,state
    phase_index+=1
    if phase_index>=len(phases): finish();return
    name,visible,mode,length=phases[phase_index]
    for ix,(c,u) in enumerate(zip(roots,modules)):
        if u.learn: u.action('learn')
        u.close();c.op('window_main').par.winclose.pulse()
        for n,value in [('Layout','main'),('Track','track1'),('Device','pixelsort')]:c.par[n]=value
        u.records.clear()
        feed(ix,{i:i/16 for i in range(16)})
        u.render()
        last_display[ix]={i:row.par.text.eval() for i,row in enumerate(row_refs[ix])}
        if ix in visible:
            c.op('window_main').par.winopen.pulse();u.action('slot1')
    frame=0;samples=[];previous_tick=None;phase_updates=0;phase_writes=0;ready=False
    counts_before={c.path:stats(c) for c in roots}
    state=name

def end_phase():
    name,visible,mode,length=phases[phase_index]
    measured=samples[60:] # warm-up: one second at nominal 60 Hz
    times=[s['update_ms'] for s in measured]
    frame_times=[s['interval_ms'] for s in measured if s['interval_ms'] is not None]
    memory={}
    for c in roots:
        after=stats(c);before=counts_before[c.path]
        memory[c.path]=dict(ops_before=before['ops'],ops_after=after['ops'],cpu_bytes_before=before['cpu_bytes'],cpu_bytes_after=after['cpu_bytes'],gpu_bytes_before=before['gpu_bytes'],gpu_bytes_after=after['gpu_bytes'],total_cook_delta=sum(after['cooks'].get(k,0)-v for k,v in before['cooks'].items()),changed_ops=sum(after['cooks'].get(k,0)!=v for k,v in before['cooks'].items()))
    result['phases'].append(dict(name=name,frames=length,warmup=60,update_ms=summary(times),frame_interval_ms=summary(frame_times),frames_over_20ms=sum(v>20 for v in frame_times),frames_over_33ms=sum(v>33.333 for v in frame_times),perform_cook_flag=summary([s['perform_cook_flag'] for s in measured]),td_frame_ms=summary([s['td_frame_ms'] for s in measured]),process_cpu_mb=summary([s['process_cpu_mb'] for s in measured]),process_cpu_mb_first=measured[0]['process_cpu_mb'],process_cpu_mb_last=measured[-1]['process_cpu_mb'],below_children_cpu_ms=summary([s['below_ms'] for s in measured]),popup_children_cpu_ms=summary([s['popup_ms'] for s in measured]),input_value_updates=phase_updates,value_label_writes=phase_writes,memory=memory))
    write_result()
    setup_phase()

def tick():
    global frame,previous_tick,phase_updates,phase_writes,ready
    if done:return
    try:
        if phase_index<0:setup_phase();return
        now=time.perf_counter();interval=(now-previous_tick)*1000 if previous_tick else None;previous_tick=now
        name,visible,mode,length=phases[phase_index]
        if frame==0:
            # Allow context callbacks to settle before opening a new edit session.
            for ix in visible:modules[ix].action('slot1') if modules[ix].selected is None else None
        start=time.perf_counter()
        if mode in ('full','dirty','burst','same','cached','cached_burst','cached_same'):
            for ix in visible:
                value=.25 if mode in ('same','cached_same') else (frame%997)/997
                values={i:(value+i/17)%1 for i in range(16)}
                if mode.startswith('cached'):
                    if mode=='cached_burst':
                        for b in range(32 if ix==visible[0] else 0):shared_values.update({i:(value+i/17+b/1000)%1 for i in range(16)})
                        phase_updates+=32*16
                    else:
                        if ix==visible[0]:shared_values.update(values)
                        phase_updates+=16
                    cached_incremental(ix,shared_values)
                elif mode=='burst':
                    # Receive 32 batches per frame; latest values win before one paint.
                    latest={}
                    for b in range(32):latest.update({i:(value+i/17+b/1000)%1 for i in range(16)})
                    phase_updates+=32*16;incremental(ix,latest)
                elif mode=='full':feed(ix,values);modules[ix].render();phase_updates+=16;phase_writes+=16
                else:incremental(ix,values);phase_updates+=16
        elif mode in ('stress','stress_10hz','rowswitch'):
            for ix in visible:
                if mode=='stress_10hz' and frame%6: continue
                c,u=roots[ix],modules[ix]
                if mode=='rowswitch':
                    u.action('slot'+str(frame%16));continue
                # Repeatedly toggle and edit across all controls; fixed frame pacing.
                slot=frame%16
                u.action('slot'+str(slot))
                if u.selected is not None:
                    c.op('base_draft').par.Value=(frame%100)/100
                    u.action('apply' if frame%3==0 else 'cancel')
                u.scroll_wheel(-100 if frame%2 else 100)
                assert 0<=c.op('container_scroll').panel.scrollv.val<=1
                if frame%10==0:u.action('learn')
                if frame%30==0:u.action('context_Device')
        elapsed=(time.perf_counter()-start)*1000
        perf=op('/inspector_stress/null_performance')
        samples.append(dict(update_ms=elapsed,interval_ms=interval,perform_cook_flag=perf['cook'].eval(),td_frame_ms=perf['msec'].eval(),process_cpu_mb=perf['cpu_mem_used'].eval(),below_ms=roots[0].childrenCPUCookTime,popup_ms=roots[1].childrenCPUCookTime))
        frame+=1
        if frame>=length:end_phase()
    except Exception:
        result['failures'].append(traceback.format_exc());finish()

def write_result():
    Path(project.folder+'/prototypes/inspector/'+output_name).write_text(json.dumps(result,indent=2))

def finish():
    global done,state
    done=True;state='complete'
    for c,u,s in zip(roots,modules,saved):
        u.close();u.records=copy.deepcopy(s['records']);u.learn=s['learn']
        for n,v in s['context'].items():c.par[n]=v
        u.render()
        if s['main']:c.op('window_main').par.winopen.pulse()
        else:c.op('window_main').par.winclose.pulse()
        if s['selected'] is not None:
            u.action('slot'+str(s['selected']))
            for n,v in s['draft'].items():c.op('base_draft').par[n]=v
        c.op('container_scroll').panel.scrollv=s['scroll']
    write_result()
    op('/inspector_stress/execute_frames').par.active=False
