"""Finite matched real-data frames plus isolated 16-slot soak; never save active.
Execute with duration=1800 (default). owner.fetch('runner').Stop() cancels and
restores real data. All temporary operators and frame callbacks are removed.
"""
from pathlib import Path
from time import perf_counter
from collections import deque
import os,json,copy
scope=dict(globals());exec(Path(project.folder+'/prototypes/inspector/acceptance_metrics.py').read_text(),scope)
Samples=scope['Samples'];bounded=scope['bounded']

class AcceptanceProbe:
    def __init__(self,owner,duration):
        self.owner=owner;self.duration=float(duration);self.started=perf_counter();self.phase='matched';self.index=-1
        self.case_seconds=globals().get('case_seconds',3)
        self.artifact_prefix=globals().get('artifact_prefix','replacement')
        self.m=op('/inspector_model');self.production=self.m.par.Controller.eval();self.views=(op('/inspector_below'),op('/inspector_popup'))
        self.saved=[dict(style=v.ext.InspectorView.style,key=v.ext.InspectorView.Key(),follow=v.ext.InspectorView._follow_routing,selected=v.ext.InspectorView.selected,main=v.op('window_main').isOpen,popup=v.op('window_editor').isOpen) for v in self.views]
        for v,s in zip(self.views,self.saved):
            p=v.op('window_editor');host=v.ext.InspectorView._popup_host
            s['popup_rect']=(p.contentWidth if p.isOpen else host.width,p.contentHeight if p.isOpen else host.height,p.x,p.y)
        self.before=self.production.GetControlCatalog();self.registry=copy.deepcopy(self.production.fetch('layout_registry'));self.session=self.m.ext.InspectorModel.adapter.Session();self.routing=self.production.GetLayoutContext()['key']
        self.output=Path(project.folder+'/prototypes/inspector');self.metrics=owner.op('null_frame');self.matched=[];self.buckets=[]
        self.frames=Samples();self.gaps=Samples();self.sync=Samples(1200);self.previous=None;self.last_action=-1;self.next_feed=0;self.next_status=0;self.feed_count=0
        self.clone=None;self.fixture=None;self.done=False;self.counts=None;self.errors=[];self.maxima={};self.stop_reason=None
        self.cases=[('closed','below',None,None),('fold_rows','below',None,None),('fold_editor','below',1,None),('fold_details','below',0,'details_toggle'),('fold_menu','below',0,'value_menu'),('fold_picker','below',2,'target_picker'),('popup_editor','popup',1,None),('popup_details','popup',0,'details_toggle'),('popup_menu','popup',0,'value_menu'),('popup_picker','popup',2,'target_picker')]
        self.cases=self.cases+list(reversed(self.cases));self.NextCase()
    def WriteStatus(self,extra=None):
        now=perf_counter();stats=self.m.Stats();targets=self.m.op('base_targets').Stats()
        data=dict(pid=os.getpid(),phase=self.phase,case=self.case,elapsed_s=now-self.started,soak_elapsed_s=max(0,now-getattr(self,'soak_start',now)),duration_s=self.duration,feeds=self.feed_count,stats=stats,targets=targets,maxima=self.maxima,errors=self.errors,done=self.done)
        if extra:data.update(extra)
        temporary=self.output/(self.artifact_prefix+'_progress.tmp');temporary.write_text(json.dumps(data,indent=2));temporary.replace(self.output/(self.artifact_prefix+'_progress.json'))
    def NextCase(self):
        if self.index>=0:self.matched.append(dict(case=self.case,frame_ms=self.frames.result(),wall_gap_ms=self.gaps.result()))
        self.index+=1
        if self.index>=len(self.cases):self.StartSoak();return
        name,style,slot,section=self.cases[self.index];self.case=name
        for v in self.views:v.CloseEditor();v.op('window_editor').par.winclose.pulse();v.op('window_main').par.winclose.pulse()
        v=self.views[0];u=v.ext.InspectorView;u.style=style;v.par.Presentation=style
        if name!='closed':
            v.Show()
            if slot is not None:v.Action('slot'+str(slot))
            if section:v.Action(section)
        self.frames=Samples();self.gaps=Samples();self.case_start=perf_counter();self.previous=None
        self.WriteStatus()
    def StartSoak(self):
        for v in self.views:
            v.CloseEditor();v.op('window_editor').par.winclose.pulse()
            v.op('window_editor').par.winh=178;v.ext.InspectorView._popup_host.par.h=178
            v.ext.InspectorView._popup_size_pending=True;v.ext.InspectorView._cancel_popup_geometry()
        self.fixture=self.owner.create(baseCOMP,'base_fixture');self.fixture.viewer=True;self.fixture.nodeX=600;self.fixture.nodeY=-40;self.fixture.nodeWidth=160;self.fixture.nodeHeight=130
        page=self.fixture.appendCustomPage('Fixture');self.parameters=[]
        for i in range(8):
            name='Knob'+str(i+1)
            par=(page.appendFloat(name) if i<4 else page.appendInt(name) if i<6 else page.appendMenu(name))[0]
            if i>=6:par.menuNames=['v'+str(n) for n in range(8)];par.menuLabels=['Choice '+str(n) for n in range(8)]
            elif i>=4:par.normMax=7
            self.parameters.append(par)
        for i in range(8):
            name='Button'+str(i+1)
            par=(page.appendToggle(name) if i<4 else page.appendPulse(name) if i<6 else page.appendMenu(name))[0]
            if i>=6:par.menuNames=['v'+str(n) for n in range(8)];par.menuLabels=['Choice '+str(n) for n in range(8)]
            self.parameters.append(par)
        page.appendFloat('Alternate');self.fixture.par.Alternate=.5
        self.clone=self.fixture.copy(self.production,name='controller');self.clone.Disconnect();self.clone.par.Followcomp=False;self.clone.Applybinding()
        self.clone.SelectLayout(self.clone.CreateLayout('Acceptance fixture'))
        for i,p in enumerate(self.parameters):self.clone.AssignParameter('knob' if i<8 else 'button',i%8+1,p)
        assert self.clone.ext.RotoPythonExt._process is None
        self.m.par.Controller=self.clone;self.m.Sync();self.m.Flush()
        self.phase='soak';self.soak_start=perf_counter();self.bucket_start=self.soak_start;self.case='fold';self.frames=Samples();self.gaps=Samples();self.sync=Samples(1200);self.previous=None
        self.SetStyle('below');self.counts=[len(v.findChildren()) for v in self.views]
        self.last_action=-1;self.next_feed=self.soak_start;self.next_status=self.soak_start+10
        self.WriteStatus()
    def SetStyle(self,style):
        v=self.views[0];u=v.ext.InspectorView
        v.CloseEditor();v.op('window_editor').par.winclose.pulse();u.style=style;v.par.Presentation=style;v.Show()
    def Feed(self,now):
        self.feed_count+=1;n=self.feed_count
        for i,p in enumerate(self.parameters):
            if p.style=='Float':p.val=((n+i*13)%101)/100
            elif p.style=='Int':p.val=(n+i)%8
            elif p.style=='Menu':p.val=p.menuNames[(n+i)%8]
            elif p.style=='Toggle':p.val=(n+i)%2
            # Pulse is intentionally never fired by synthetic display traffic.
        start=perf_counter();self.m.Sync();self.m.Flush();self.sync.add((perf_counter()-start)*1000)
        self.next_feed=now+.1
    def Action(self,now):
        elapsed=now-self.soak_start;step=int(elapsed//5)
        if step==self.last_action:return
        self.last_action=step;v=self.views[0];u=v.ext.InspectorView
        if step%12==0:
            style='below' if int(elapsed//60)%2==0 else 'popup';self.case='fold' if style=='below' else 'popup';self.SetStyle(style)
        # Selecting the same row toggles it closed. Explicitly reset selection
        # so repeated-slot scenarios really open Details/Picker as intended.
        v.CloseEditor();v.Action('slot'+str((step//2)%16))
        section=step%6
        if section==1:v.Action('details_toggle')
        elif section==2:v.Action('mapping_toggle')
        elif section==3:
            v.Action('target_picker');v.op('base_draft').par.Pickscope=self.fixture.path;u.SearchTargets()
        elif section==4:
            v.Action('slot6');v.Action('value_menu')
        elif section==5:v.CloseEditor()
        if step%12==6:
            ext=self.clone.ext.RotoPythonExt;ext._host.learning=True;ext._host._sync();ext._publish();self.m.Sync();self.m.Flush()
        elif step%12==7:
            ext=self.clone.ext.RotoPythonExt;ext._host.learning=False;ext._host._sync();ext._publish();self.m.Sync();self.m.Flush()
        elif step%12==8:
            target=self.clone.ext.RotoPythonExt._host.controls[('knob',1)];target.touched=True;self.clone.ext.RotoPythonExt._host._sync();self.clone.ext.RotoPythonExt._publish();self.m.Sync();self.m.Flush()
        elif step%12==9:
            target=self.clone.ext.RotoPythonExt._host.controls[('knob',1)];target.touched=False;self.clone.ext.RotoPythonExt._host._sync();self.clone.ext.RotoPythonExt._publish();self.m.Sync();self.m.Flush()
        elif step%12==10:
            p=self.parameters[3] if (step//12)%2 else self.fixture.par.Alternate
            self.clone.AssignParameter('knob',4,p);self.m.Sync();self.m.Flush()
    def Check(self):
        stats=self.m.Stats();targets=self.m.op('base_targets').Stats()
        assert bounded(stats,targets),(stats,targets)
        assert self.counts==[len(v.findChildren()) for v in self.views],'View operators grew'
        assert self.clone.ext.RotoPythonExt._process is None,'Fixture opened MIDI process'
        assert len(self.clone.ext.RotoPythonExt._pending)<=262144,'Fixture MIDI queue exceeded bound'
        assert len(self.m.ext.InspectorModel.adapter._definitions_cache)<=4,'Definition cache exceeded bound'
        for v in self.views:
            u=v.ext.InspectorView;p=u._popup
            expected=178+u._popup_extra
            assert p.par.winh.eval()==expected,('Popup opening height drifted',p.par.winh.eval(),expected)
            if p.isOpen and not getattr(u,'_popup_geometry',None):
                assert p.contentHeight==expected,('Popup actual height drifted',p.contentHeight,expected)
        self.maxima['fixture_midi_pending_bytes']=max(self.maxima.get('fixture_midi_pending_bytes',0),len(self.clone.ext.RotoPythonExt._pending))
        self.maxima['definition_contexts']=max(self.maxima.get('definition_contexts',0),len(self.m.ext.InspectorModel.adapter._definitions_cache))
        for name in ('cache_contexts','source_contexts','pending_contexts','pending_slots','subscribers'):
            self.maxima[name]=max(self.maxima.get(name,0),stats[name])
        for name in ('pages','entries','jobs','pending'):self.maxima['targets_'+name]=max(self.maxima.get('targets_'+name,0),targets[name])
        assert not any(v.errors(recurse=True) for v in self.views)
    def Bucket(self,now):
        self.buckets.append(dict(elapsed_s=now-self.soak_start,case=self.case,frame_ms=self.frames.result(),wall_gap_ms=self.gaps.result(),sync_ms=self.sync.result(),metrics={c.name:float(c[0]) for c in self.metrics.chans()},maxima=dict(self.maxima)))
        self.frames=Samples();self.gaps=Samples();self.sync=Samples(1200);self.bucket_start=now
        self.WriteStatus()
    def Tick(self,frame):
        if self.done:return
        try:
            now=perf_counter();self.metrics.cook(force=True)
            channels={c.name:float(c[0]) for c in self.metrics.chans()}
            if self.phase!='matched' or now-self.case_start>.5:
                self.frames.add(channels['msec'])
                if self.previous is not None:self.gaps.add((now-self.previous)*1000)
            self.previous=now
            if self.phase=='matched':
                if now-self.case_start>=self.case_seconds:self.NextCase()
                return
            if now>=self.next_feed:self.Feed(now)
            self.Action(now)
            if now>=self.next_status:self.Check();self.WriteStatus();self.next_status=now+10
            if now-self.bucket_start>=60:self.Bucket(now)
            if now-self.soak_start>=self.duration:self.Bucket(now);self.Stop('complete')
        except Exception as error:
            self.errors.append(str(error));self.Stop('failure');raise
    def Stop(self,reason='cancelled'):
        if self.done:return
        self.done=True;self.stop_reason=reason;self.owner.op('sample_frame').par.active=False
        elapsed=perf_counter()-getattr(self,'soak_start',perf_counter())
        try:
            for v in self.views:v.CloseEditor();v.op('window_editor').par.winclose.pulse();v.op('window_main').par.winclose.pulse()
            self.m.par.Controller=self.production;self.m.Sync();self.m.Flush()
            for v,s in zip(self.views,self.saved):
                u=v.ext.InspectorView;u.style=s['style'];v.par.Presentation=s['style'];u._follow_routing=s['follow']
                p=v.op('window_editor');width,height,x,y=s['popup_rect']
                p.par.winw=width;p.par.winh=height;u._popup_host.par.w=width;u._popup_host.par.h=height
                u._popup_size_pending=True;u._cancel_popup_geometry()
                if not s['follow']:u.ConfigureMenus(s['key']);u.OnContext()
                if s['main']:v.Show()
                if s['selected'] is not None:v.Action('slot'+str(s['selected']))
                if not s['popup']:v.op('window_editor').par.winclose.pulse()
                else:p.par.winoffsetx=x;p.par.winoffsety=y
            if self.fixture:self.fixture.destroy();self.fixture=None
            preserved=(self.production.GetControlCatalog()==self.before and self.production.fetch('layout_registry')==self.registry and self.production.GetLayoutContext()['key']==self.routing and self.m.ext.InspectorModel.adapter.Session()==self.session and self.production.State['Connected'])
            self.result=dict(reason=reason,complete=reason=='complete',soak_elapsed_s=elapsed,feeds=self.feed_count,matched=self.matched,buckets=self.buckets,maxima=self.maxima,errors=self.errors,production_preserved=preserved,subscribers=self.m.Stats()['subscribers'],physical_relearn_verified=False,native_resize_issue_6_deferred=True)
            self.result['duration_s']=self.duration
            (self.output/(self.artifact_prefix+'_acceptance.json')).write_text(json.dumps(self.result,indent=2))
            self.phase='done';self.WriteStatus(dict(production_preserved=preserved,reason=reason))
            print('Replacement probe finished',reason,'soak seconds',round(elapsed,2),'production preserved',preserved)
        finally:
            if self.owner.valid:self.owner.destroy()

assert not op('/base_inspector_acceptance'),'Acceptance probe already running'
probe=op('/').create(baseCOMP,'base_inspector_acceptance');probe.viewer=probe.display=True;probe.par.parentshortcut='AcceptanceProbe';probe.nodeX=1500;probe.nodeY=-1100
perform=probe.create(performCHOP,'perform_frame');perform.viewer=True
for par in perform.pars():
    if par.name in ('fps','msec','droppedframes','cpumemused','gpumemused','activeops','totalops'):par.val=True
    elif par.style=='Toggle' and par.name not in ('timeslice',):par.val=False
output=probe.create(nullCHOP,'null_frame');output.viewer=True;output.nodeX=175;output.inputConnectors[0].connect(perform.outputConnectors[0])
callback=probe.create(executeDAT,'sample_frame');callback.viewer=True;callback.par.language='python';callback.nodeX=350
callback.par.framestart=False;callback.par.frameend=True;callback.par.active=False
callback.text="def onFrameEnd(frame):\n    parent.AcceptanceProbe.fetch('runner').Tick(frame)\n"
try:
    runner=AcceptanceProbe(probe,globals().get('duration',1800));probe.store('runner',runner)
    callback.par.active=True
    print('Finite acceptance started',os.getpid(),'soak seconds',runner.duration,'CHOP channels',[c.name for c in output.chans()])
except Exception:
    if probe.valid:probe.destroy()
    raise
