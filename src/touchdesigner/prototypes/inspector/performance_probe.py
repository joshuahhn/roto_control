"""Finite callback/visibility ablations on the disconnected acceptance fixture.

No production monkeypatches. Only the shared Inspector read model and existing
view are timed; every wrapper is removed before real data is restored. Do not
save a project while this probe is active. Stop via owner.fetch('runner').Stop().
"""
from pathlib import Path
from time import perf_counter
import json

scope=dict(globals(),define_only=True,case_seconds=globals().get('cost_seconds',6),
           artifact_prefix=globals().get('cost_prefix','callback_cost'))
exec(Path(project.folder+'/prototypes/inspector/acceptance_probe.py').read_text(),scope)
AcceptanceProbe=scope['AcceptanceProbe'];Samples=scope['Samples']

class CostProbe(AcceptanceProbe):
    def __init__(self,owner):
        owner.store('runner',self)
        self.hooks=[];self.timings={};self.callback_depth=0;self.deferred=False
        self.results=[];self.case_index=-1;self.coalesce=False;self.active=False
        self.case_seconds=globals().get('cost_seconds',6)
        self.prefix=globals().get('cost_prefix','callback_cost')
        self.configs=[('closed_idle','below',0,None,False,False),
                      ('fold_idle','below',0,'rows',False,False),
                      ('popup_idle','popup',0,'editor',False,False),
                      ('closed_14','below',14,None,False,False),
                      ('fold_14','below',14,'rows',False,False),
                      ('popup_14','popup',14,'editor',False,False),
                      ('details_14','popup',14,'details',False,False),
                      ('closed_1','below',1,None,False,False),
                      ('popup_1','popup',1,'editor',False,False),
                      ('popup_frozen_14','popup',14,'editor',True,False),
                      ('closed_coalesced_14','below',14,None,False,True),
                      ('popup_coalesced_14','popup',14,'editor',False,True)]
        self.configs+=list(reversed(self.configs))
        super().__init__(owner,0)
        self.artifact_prefix=self.prefix

    def Wrap(self,obj,name,label):
        original=getattr(obj,name);own=name in obj.__dict__
        self.hooks.append((obj,name,original,own))
        def timed(*args,**kwargs):
            if label=='controller._publish' and self.coalesce and self.callback_depth:
                self.deferred=True;return
            start=perf_counter()
            if label=='controller.onControlChange':self.callback_depth+=1
            try:return original(*args,**kwargs)
            finally:
                if label=='controller.onControlChange':self.callback_depth-=1
                if self.active and start-self.case_start>=1:
                    self.timings.setdefault(label,Samples(2400)).add((perf_counter()-start)*1000)
        setattr(obj,name,timed)

    def NextCase(self):
        self.active=False
        if self.clone is None:
            super().StartSoak()
            self.sections=[dict(mapping=v.ext.InspectorView._mapping.open) for v in self.views]
            # Use the pre-probe section states, captured by the builder below.
            self.sections=original_sections
            ext=self.clone.ext.RotoPythonExt
            if globals().get('use_cached_projection',False):
                # Reuse the disconnected fixture's live state; install only the
                # two compatible methods under test, without a MIDI reconnect.
                self.clone.op('inspector/inspector_data').text=Path(project.folder+'/code/py/roto_python/inspector/inspector_data.py').read_text()
                source=self.clone.op('RotoPythonExt')
                ext._layouts.capture(force=True)
                source.text=Path(project.folder+'/code/py/roto_python/RotoPythonExt.py').read_text()
                self.clone.initializeExtensions(0);self.clone.Applybinding()
                ext=self.clone.ext.RotoPythonExt
                assert ext._process is None and len(self.clone.GetControlCatalog())==16
                self.m.Sync();self.m.Flush()
            self.Wrap(self.clone.op('inspector/inspector_data').module,'refresh','legacy.refresh')
            for name in ('onControlChange','_publish','_update_catalog','_publish_controls','_publish_inspector'):
                self.Wrap(ext,name,'controller.'+name)
            self.Wrap(ext._layouts,'capture','registry.capture')
            for name in ('Sync','Flush'):self.Wrap(self.m.ext.InspectorModel,name,'model.'+name)
            u=self.views[0].ext.InspectorView
            for name in ('_refresh_rows','_update_editor','_update_mapping','_update_details'):
                self.Wrap(u,name,'view.'+name)
            self.original_visible=u._visible
        elif self.case_index>=0:
            self.results.append(dict(case=self.case,frame_ms=self.frames.result(),
                wall_gap_ms=self.gaps.result(),feed_ms=self.feed_times.result(),
                methods={k:v.result() for k,v in self.timings.items()},
                feeds=self.feed_count-self.feeds_before,dropped_frames=self.dropped,
                frame_samples=self.frames.total,stats=self.m.Stats()))
        self.case_index+=1
        if self.case_index>=len(self.configs):self.Stop('complete');return
        name,style,count,section,frozen,coalesce=self.configs[self.case_index]
        for v in self.views:v.CloseEditor();v.op('window_editor').par.winclose.pulse();v.op('window_main').par.winclose.pulse()
        v=self.views[0];u=v.ext.InspectorView;u._visible=self.original_visible
        u.style=style;v.par.Presentation=style
        if section:
            v.Show()
            if section!='rows':v.Action('slot0')
            if section=='details':v.Action('details_toggle')
        if frozen:u._visible=lambda:False
        self.case=name;self.count=count;self.coalesce=coalesce
        self.frames=Samples();self.gaps=Samples();self.feed_times=Samples();self.timings={}
        self.dropped=0;self.feeds_before=self.feed_count;self.previous=None
        self.case_start=perf_counter();self.next_feed=self.case_start+1;self.active=True
        self.WriteStatus()

    def Feed(self,now):
        start=perf_counter();self.feed_count+=1;n=self.feed_count
        parameters=[p for p in self.parameters if p.style!='Pulse'][:self.count]
        for i,p in enumerate(parameters):
            if p.style=='Float':p.val=((n+i*13)%101)/100
            elif p.style=='Int':p.val=(n+i)%8
            elif p.style=='Menu':p.val=p.menuNames[(n+i)%8]
            elif p.style=='Toggle':p.val=(n+i)%2
        self.m.Sync();self.m.Flush()
        self.feed_times.add((perf_counter()-start)*1000);self.next_feed=now+.1

    def Tick(self,frame):
        if self.done:return
        try:
            now=perf_counter()
            if self.deferred:
                self.deferred=False;self.clone.ext.RotoPythonExt._publish()
            self.metrics.cook(force=True);channels={c.name:float(c[0]) for c in self.metrics.chans()}
            if now-self.case_start>=1:
                self.frames.add(channels['msec']);self.dropped+=channels['dropped_frames']
                if self.previous is not None:self.gaps.add((now-self.previous)*1000)
            self.previous=now
            if self.count and now>=self.next_feed:self.Feed(now)
            if now-self.case_start>=self.case_seconds:self.NextCase()
        except Exception as error:
            self.errors.append(str(error));self.Stop('failure');raise

    def Stop(self,reason='cancelled'):
        if self.done:return
        self.active=False
        if self.deferred:self.deferred=False;self.clone.ext.RotoPythonExt._publish()
        if hasattr(self,'original_visible'):self.views[0].ext.InspectorView._visible=self.original_visible
        for obj,name,original,own in reversed(self.hooks):
            if own:setattr(obj,name,original)
            else:delattr(obj,name)
        self.hooks=[]
        (self.output/(self.prefix+'_timings.json')).write_text(json.dumps(dict(
            cases=self.results,errors=self.errors,reason=reason,
            method_times='inclusive; nested timings must not be added',
            coalescing='fixture-only publication proof; not a production change',
            visibility='matched window/frozen-projection ablations; not isolated GPU timing'),indent=2))
        super().Stop(reason)
        for v,s,section in zip(self.views,self.saved,self.sections):
            if not section['mapping']:continue
            u=v.ext.InspectorView;p=v.op('window_editor');width,height,x,y=s['popup_rect']
            v.CloseEditor();p.par.winclose.pulse();p.par.winw=width;p.par.winh=height-134
            u._popup_host.par.w=width;u._popup_host.par.h=height-134;u._popup_size_pending=True;u._cancel_popup_geometry()
            v.Action('slot'+str(s['selected']));v.Action('mapping_toggle')
            u._mapping.message=section['message'];u._update_mapping();p.par.winoffsetx=x;p.par.winoffsety=y

assert not op('/base_inspector_acceptance'),'Another probe is running'
original_sections=[dict(mapping=op(p).ext.InspectorView._mapping.open,
                        message=op(p).ext.InspectorView._mapping.message)
                   for p in ('/inspector_below','/inspector_popup')]
probe=op('/').create(baseCOMP,'base_inspector_acceptance');probe.viewer=True
probe.par.parentshortcut='AcceptanceProbe';probe.nodeX=1500;probe.nodeY=-1100
perform=probe.create(performCHOP,'perform_frame');perform.viewer=True
for p in perform.pars():
    if p.style=='Toggle' and p.name!='timeslice':p.val=p.name in ('msec','fps','droppedframes')
output=probe.create(nullCHOP,'null_frame');output.viewer=True;output.nodeX=175
output.inputConnectors[0].connect(perform.outputConnectors[0])
callback=probe.create(executeDAT,'sample_frame');callback.viewer=True;callback.nodeX=350
callback.par.language='python';callback.par.active=False;callback.par.framestart=False;callback.par.frameend=True
callback.text="def onFrameEnd(frame):\n    parent.AcceptanceProbe.fetch('runner').Tick(frame)\n"
try:
    runner=CostProbe(probe);probe.store('runner',runner);callback.par.active=True
    print('Finite callback cost probe started:',len(runner.configs),'cases x',runner.case_seconds,'seconds')
except Exception:
    if probe.valid:
        pending=probe.fetch('runner',None)
        if pending and getattr(pending,'clone',None):pending.Stop('initialization_failure')
        elif probe.valid:probe.destroy()
    raise
