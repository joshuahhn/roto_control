"""Test activation on a disconnected clone; no physical MIDI or production routing."""
from pathlib import Path
import copy,json
class ActivationProbe:
    def __init__(self):
        self.model=op('/inspector_model');self.production=self.model.par.Controller.eval()
        self.before=self.production.GetControlCatalog();self.registry=copy.deepcopy(self.production.fetch('layout_registry'))
        self.pid=self.production.ext.RotoPythonExt._process.pid;self.session=self.model.ext.InspectorModel.adapter.Session()
        self.views=[op('/inspector_below'),op('/inspector_popup')];self.styles=[v.ext.InspectorView.style for v in self.views]
        self.holder=self.clone=None;self.packets=[];self.result={}
    def sync(self):self.model.Sync();self.model.Flush()
    def activate(self,key):
        self.sync();return self.model.Activate(key,self.model.ActivationToken(key))
    def Start(self):
        assert not op('/base_activation_verification')
        for v in self.views:v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        self.holder=root.create(baseCOMP,'base_activation_verification');self.holder.nodeX=1085;self.holder.nodeY=0
        a=self.holder.create(baseCOMP,'effect_a');b=self.holder.create(baseCOMP,'effect_b')
        a.nodeX=0;b.nodeX=200
        pa=a.appendCustomPage('Fixture').appendFloat('Amount')[0];pa.val=.3
        pb=b.appendCustomPage('Fixture').appendFloat('Amount')[0];pb.val=.7
        self.clone=self.holder.copy(self.production,name='controller');c=self.clone;c.nodeX=400
        c.Disconnect();c.par.Followcomp=False;c.Applybinding();c.SelectLayout(c.CreateLayout('ACTIVATE'))
        self.a=tuple(c.GetLayoutContext()['key']);c.AssignParameter('knob',1,pa)
        c.SetPluginComp(*self.a,a)
        device=c.CreatePlugin(self.a[0],self.a[1],'BANK B')
        self.b=(self.a[0],self.a[1],device);c.SelectPlugin(*self.b);c.AssignParameter('knob',2,pb);c.SetPluginComp(*self.b,b)
        track=c.CreateTrack(self.a[0],'TRACK B');self.track=(self.a[0],track,c.GetPlugins(self.a[0],track)[0]['id'])
        layout=c.CreateLayout('LAYOUT B');self.layout=(layout,c.GetTracks(layout)[0]['id'],c.GetPlugins(layout)[0]['id'])
        c.SelectPlugin(*self.a)
        e=c.ext.RotoPythonExt;m=e._layout_manager();e._host.send=lambda packet:self.packets.append(tuple(packet))
        e._host.connected=e._host.plugin=True;e._host._sync();e._publish();assert e._process is None
        self.model.par.Controller=c;self.sync();self.values=(pa.eval(),pb.eval())
        self.model.GetCatalog(self.b);assert tuple(c.GetLayoutContext()['key'])==self.a
        self.activate(self.b);assert tuple(c.GetLayoutContext()['key'])==self.b
        self.activate(self.track);assert tuple(c.GetLayoutContext()['key'])==self.track
        self.activate(self.layout);assert tuple(c.GetLayoutContext()['key'])==self.layout
        self.activate(self.a)
        assert (pa.eval(),pb.eval())==self.values
        self.result['device_track_layout_activation_no_value_write']=True
        # Guard changes occur after the captured UI intent, not just at render time.
        for obj,name,value in [(e._host,'learning',True),(e._host,'touched',True),(m,'locked',True),
                              (e._follow,'backlog',True),(e._follow,'paused',True)]:
            self.sync();token=self.model.ActivationToken(self.b);old=getattr(obj,name);setattr(obj,name,value)
            try:
                self.model.Activate(self.b,token);raise AssertionError('Guard failed: '+name)
            except ValueError:pass
            finally:setattr(obj,name,old);self.sync()
            assert tuple(c.GetLayoutContext()['key'])==self.a
        self.result['fresh_learn_touch_lock_backlog_pause_guards']=True
        token=self.model.ActivationToken(self.b);e._follow.connection_generation+=1
        try:self.model.Activate(self.b,token);raise AssertionError('Session guard failed')
        except ValueError:pass
        self.result['stale_session_rejected']=True
        install=m.install
        def fail_destination(record,hardware=False):
            if record['group_id']==self.b[2]:raise ValueError('Fixture destination install failure')
            return install(record,hardware)
        m.install=fail_destination
        try:
            try:self.activate(self.b);raise AssertionError('Failure not reported')
            except ValueError as error:assert 'Fixture destination' in str(error)
        finally:m.install=install;e._follow.flush();self.sync()
        assert tuple(c.GetLayoutContext()['key'])==self.a and not e._follow.gated and not e._follow.paused
        self.result['native_install_rollback_no_false_success']=True
        # Follow remains enabled; unchanged selection does not undo manual intent.
        e._follow.sampler=lambda:(a,(a,));c.par.Followcomp=True
        e._follow.observe(force=True);e._follow.flush();self.sync()
        self.activate(self.b);e._follow.observe(force=True);e._follow.flush();self.sync()
        assert tuple(c.GetLayoutContext()['key'])==self.b and c.par.Followcomp.eval()
        self.result['follow_preference_and_unchanged_selection_preserved']=True
        c.par.Followcomp=False;self.activate(self.a)
        for v,style in zip(self.views,('below','popup')):
            u=v.ext.InspectorView;u.style=style;u._follow_routing=False;u.ConfigureMenus(self.b);u.Refresh()
            assert v.op('activate_device').par.display.eval() and v.op('activate_device').par.enable.eval()
            assert not v.op('clear_device').par.display.eval()
            assert v.Action('activate_device') is True
            assert u.Key()==self.b and u._follow_routing
            assert not v.op('activate_device').par.display.eval() and v.op('clear_device').par.display.eval()
            self.activate(self.a)
        self.result['fold_popup_footer_action']=True
        v=self.views[0];v.Show();u=v.ext.InspectorView;u._follow_routing=False;u.ConfigureMenus(self.b);u.Refresh()
        self.result['fixture_ready_for_native_click']=True
        print(json.dumps(self.result))
    def Finish(self):
        try:
            assert tuple(self.clone.GetLayoutContext()['key'])==self.b,'Native click has not activated the fixture'
            assert self.views[0].ext.InspectorView._follow_routing
            self.result['native_footer_click']=True
            assert not any(o.errors(recurse=True) for o in [self.clone,self.model]+self.views)
        finally:self.Stop()
        Path(project.folder+'/prototypes/inspector/activation_verification.json').write_text(json.dumps(self.result,indent=2)+'\n')
        print(json.dumps(self.result))
    def Stop(self):
        for v,style in zip(self.views,self.styles):v.CloseEditor();v.op('window_editor').par.winclose.pulse();v.ext.InspectorView.style=style
        self.model.par.Controller=self.production;self.sync()
        if self.clone:self.clone.Disconnect()
        if self.holder:self.holder.destroy()
        assert self.production.GetControlCatalog()==self.before and self.production.fetch('layout_registry')==self.registry
        assert self.production.ext.RotoPythonExt._process.pid==self.pid and self.model.ext.InspectorModel.adapter.Session()==self.session
        assert self.model.Stats()['subscribers']==2
        self.result.update(production_catalog_registry_process_session_preserved=True,fixture_removed=True,no_physical_midi=True,subscribers=2)
