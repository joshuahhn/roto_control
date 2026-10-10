"""Finite fixed-deadline ablations; disconnected fixture, existing UI only.

native_profile=False measures cadence with no native monitor overhead. True
adds sparse native Perform DAT snapshots, which are reported separately.
Stop through /base_inspector_acceptance.fetch('runner').Stop(). Never save active.
"""
from pathlib import Path
from time import perf_counter
import json

profile=bool(globals().get('native_profile',False))
configs=[('closed_idle','below',0,None,False,False),
         ('closed_14','below',14,None,False,False),
         ('fold_14','below',14,'rows',False,False),
         ('popup_14','popup',14,'editor',False,False),
         ('popup_frozen_14','popup',14,'editor',True,False),
         ('popup_no_legacy_14','popup',14,'editor',False,False),
         ('popup_no_main_redraw_14','popup',14,'editor',False,False),
         ('closed_no_main_redraw_14','below',14,None,False,False),
         ('closed_no_publication_14','below',14,None,False,False)]
if globals().get('cadence_configs') is not None:configs=globals()['cadence_configs']
elif profile:configs=[configs[i] for i in (0,1,3,5,6)]
scope=dict(globals(),cost_define_only=True,cost_configs=configs,
           cost_seconds=globals().get('cadence_seconds',8),
           cost_prefix=globals().get('cadence_prefix','cadence_native' if profile else 'cadence_ablation'))
exec(Path(project.folder+'/prototypes/inspector/performance_probe.py').read_text(),scope)
CostProbe=scope['CostProbe'];Samples=scope['Samples']
scope['original_sections']=[dict(mapping=op(p).ext.InspectorView._mapping.open,
    message=op(p).ext.InspectorView._mapping.message) for p in ('/inspector_below','/inspector_popup')]

class CadenceProbe(CostProbe):
    def __init__(self,owner):
        self.redraw_before=ui.redrawMainWindow
        self.feed_period=1/float(globals().get('feed_hz',10))
        self.skip_legacy=False;self.skip_publication=False
        self.native_results=[];self.native_samples={};self.native_worst=None
        self.native_count=0;self.native_armed=False;self.native_next=0
        self.native_remaining=0
        self.lag=Samples();self.feed_intervals=Samples();self.missed_deadlines=0
        self.last_feed_time=None;self.feed_index=0
        self.start_gaps=Samples();self.start_to_end=Samples();self.previous_start=None;self.current_start=None
        super().__init__(owner)

    def Wrap(self,obj,name,label):
        original=getattr(obj,name);own=name in obj.__dict__
        self.hooks.append((obj,name,original,own))
        def timed(*args,**kwargs):
            if label=='controller._publish_inspector' and self.skip_legacy:return
            if label=='controller._publish' and self.skip_publication:return
            start=perf_counter()
            try:return original(*args,**kwargs)
            finally:
                if self.active and start-self.case_start>=1:
                    self.timings.setdefault(label,Samples(2400)).add((perf_counter()-start)*1000)
        setattr(obj,name,timed)

    def NextCase(self):
        previous=None
        if getattr(self,'case_index',-1)>=0:
            previous=dict(case=self.case,deadline_lag_ms=self.lag.result(),
                requested_hz=1/self.feed_period,measurement_seconds=perf_counter()-self.case_start-1,
                feed_interval_ms=self.feed_intervals.result(),missed_deadlines=self.missed_deadlines,
                frame_start_gap_ms=self.start_gaps.result(),start_to_end_ms=self.start_to_end.result(),
                native_samples=self.native_count,native_ms={k:v.result() for k,v in self.native_samples.items()},
                worst_native_frame=self.native_worst)
            self.native_results.append(previous)
        # Stop any last native snapshot before swapping visibility/flags.
        self.owner.op('perform_native').par.active=False
        ui.redrawMainWindow=self.redraw_before
        self.skip_legacy=False;self.skip_publication=False
        super().NextCase()
        if self.done:return
        self.skip_legacy='no_legacy' in self.case
        self.skip_publication='no_publication' in self.case
        ui.redrawMainWindow=False if 'no_main_redraw' in self.case else self.redraw_before
        self.lag=Samples();self.feed_intervals=Samples();self.missed_deadlines=0
        self.last_feed_time=None;self.feed_index=0;self.feed_anchor=self.case_start+1
        self.next_feed=self.feed_anchor
        self.native_samples={};self.native_worst=None;self.native_count=0
        self.native_armed=False;self.native_next=self.feed_anchor+.15
        self.native_remaining=0
        self.start_gaps=Samples();self.start_to_end=Samples();self.previous_start=None;self.current_start=None

    def Feed(self,now):
        # Anchor to the original 10Hz clock; don't move its phase on late frames.
        due=max(0,int((now-self.feed_anchor)/self.feed_period))+1
        self.missed_deadlines+=max(0,due-self.feed_index-1)
        self.lag.add((now-(self.feed_anchor+(due-1)*self.feed_period))*1000)
        if self.last_feed_time is not None:self.feed_intervals.add((now-self.last_feed_time)*1000)
        self.last_feed_time=now;self.feed_index=due
        super().Feed(now)
        self.next_feed=self.feed_anchor+due*self.feed_period
        if profile and due%5==1:
            # Capture the feed frame and following callback/flush frames,
            # rather than sparse snapshots between 10Hz updates.
            self.native_remaining=3
            self.owner.op('perform_native').par.active=True

    def Native(self,dat):
        if not self.active or perf_counter()-self.case_start<1:return
        headers=[str(c) for c in dat.row(0)]
        rows=[dict(zip(headers,(str(c) for c in row))) for row in dat.rows()[1:]]
        metrics={r['info']:float(r['time']) for r in rows if r['category']=='frame' and r['time']}
        for name,value in metrics.items():self.native_samples.setdefault(name,Samples(128)).add(value)
        self.native_count+=1
        frame=metrics.get('Total Frame Time',0)
        if self.native_worst is None or frame>self.native_worst['frame_ms']:
            self.native_worst=dict(frame_ms=frame,rows=rows[:1600],truncated=len(rows)>1600,
                capture_kind='feed_burst' if self.native_remaining else 'idle')
        if self.native_remaining:
            self.native_remaining-=1
            if not self.native_remaining:dat.par.active=False

    def FrameStart(self,frame):
        now=perf_counter();self.current_start=now
        if self.active and now-self.case_start>=1 and self.previous_start is not None:
            self.start_gaps.add((now-self.previous_start)*1000)
        self.previous_start=now

    def Tick(self,frame):
        if self.done:return
        if self.current_start is not None and self.active and perf_counter()-self.case_start>=1:
            self.start_to_end.add((perf_counter()-self.current_start)*1000)
        if profile:
            now=perf_counter()
            # Sparse half-second captures; callback runs on the next frame.
            if not self.count and now>=self.native_next:
                self.native_next=now+.5
                self.owner.op('perform_native').par.activepulse.pulse()
        super().Tick(frame)

    def Stop(self,reason='cancelled'):
        if self.done:return
        ui.redrawMainWindow=self.redraw_before
        self.owner.op('perform_native').par.active=False
        (self.output/(self.prefix+'_native.json')).write_text(json.dumps(dict(
            cases=self.native_results,reason=reason,native_monitor_enabled=profile,
            redraw_restored=ui.redrawMainWindow==self.redraw_before,
            notes=['Native monitor samples include monitor overhead; compare cadence against the unmonitored run.',
                   'Native redraw measures CPU/driver Window work, not isolated GPU execution.',
                   'no_publication is a fixture-only ablation; not a runtime change.']),indent=2))
        self.skip_legacy=False;self.skip_publication=False
        super().Stop(reason)

assert not op('/base_inspector_acceptance'),'Another probe is running'
probe=op('/').create(baseCOMP,'base_inspector_acceptance');probe.viewer=True
probe.par.parentshortcut='AcceptanceProbe';probe.nodeX=1500;probe.nodeY=-1100
perform=probe.create(performCHOP,'perform_frame');perform.viewer=True
for p in perform.pars():
    if p.style=='Toggle' and p.name!='timeslice':p.val=p.name in ('msec','fps','droppedframes')
output=probe.create(nullCHOP,'null_frame');output.viewer=True;output.nodeX=175
output.inputConnectors[0].connect(perform.outputConnectors[0])
native=probe.create(performDAT,'perform_native');native.viewer=True;native.nodeX=0;native.nodeY=-125
native.par.active=False;native.par.triggermode='threshold';native.par.triggerthreshold=0
for p in native.pars('log*'):p.val=True
native.par.callbacks.eval().par.language='python'
native.par.callbacks.eval().text="def onTrigger(performOp):\n    runner=parent.AcceptanceProbe.fetch('runner',None)\n    if runner:runner.Native(performOp)\n"
callback=probe.create(executeDAT,'sample_frame');callback.viewer=True;callback.nodeX=350
callback.par.language='python';callback.par.active=False;callback.par.framestart=True;callback.par.frameend=True
callback.text="def onFrameStart(frame):\n    parent.AcceptanceProbe.fetch('runner').FrameStart(frame)\ndef onFrameEnd(frame):\n    parent.AcceptanceProbe.fetch('runner').Tick(frame)\n"
try:
    runner=CadenceProbe(probe);probe.store('runner',runner);callback.par.active=True
    print('Finite cadence ablation started:',len(runner.configs),'cases x',runner.case_seconds,'seconds; native monitor',profile)
except Exception:
    pending=probe.fetch('runner',None)
    if pending and getattr(pending,'clone',None):pending.Stop('initialization_failure')
    elif probe.valid:probe.destroy()
    raise
