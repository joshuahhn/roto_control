"""Staged native metadata/UI fixture. No production mapping or MIDI writes.

Run start, then inspect/open each native dialog explicitly, then finish. State
lives on the Inspector extension temporarily, never serialized TD storage.
"""
from pathlib import Path
import copy,json

class AdvancedProbe:
    def __init__(self):
        self.model=op('/inspector_model');self.production=self.model.par.Controller.eval()
        self.before=self.production.GetControlCatalog();self.registry=copy.deepcopy(self.production.fetch('layout_registry'))
        self.pid=self.production.ext.RotoPythonExt._process.pid;self.session=self.model.ext.InspectorModel.adapter.Session()
        self.routing=self.production.GetLayoutContext()['key'];self.pane=ui.panes.current;self.pane_owner=self.pane.owner
        self.views=[op('/inspector_below'),op('/inspector_popup')];self.styles=[v.ext.InspectorView.style for v in self.views]
        self.holder=None;self.clone=None;self.callback=None;self.result={};self.packets=[]

    def Start(self):
        for v in self.views:v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        holder=self.holder=self.production.parent().create(baseCOMP,'base_inspector_advanced_verification')
        holder.viewer=True;holder.nodeX=1300;holder.nodeY=-750
        page=holder.appendCustomPage('Fixture')
        for method,name in (('appendFloat','Amount'),('appendInt','Count'),('appendMenu','Choice'),('appendToggle','Enabled'),
                            ('appendPulse','Trigger'),('appendFloat','Alias'),('appendFloat','Driven')):getattr(page,method)(name)
        holder.par.Amount=.375;holder.par.Amount.default=.25;holder.par.Amount.normMin=0;holder.par.Amount.normMax=1
        holder.par.Amount.min=-2;holder.par.Amount.max=3;holder.par.Amount.clampMax=True
        holder.par.Count.normMax=7;holder.par.Count=3
        holder.par.Choice.menuNames=['n'+str(i) for i in range(20)];holder.par.Choice.menuLabels=['Choice '+str(i) for i in range(20)]
        holder.par.Choice='n2';holder.par.Enabled=True
        clone=self.clone=holder.copy(self.production,name='controller');clone.Disconnect();clone.par.Followcomp=False;clone.Applybinding()
        clone.SelectLayout(clone.CreateLayout('Native definition fixture'))
        self.ids={}
        for kind,slot,name in [('knob',1,'Amount'),('knob',2,'Count'),('knob',3,'Alias'),('knob',4,'Driven'),
                               ('button',1,'Choice'),('button',2,'Enabled'),('button',3,'Trigger')]:
            self.ids[name]=clone.AssignParameter(kind,slot,holder.par[name])['id']
        holder.par.Alias.bindExpr="op('.').par.Amount";holder.par.Alias.bindRange=True
        holder.par.Driven.expr='0.5';holder.par.Driven.defaultMode=ParMode.EXPRESSION;holder.par.Driven.defaultExpr='0.25'
        ext=clone.ext.RotoPythonExt;host=ext._host;host.send=lambda p:self.packets.append(tuple(p))
        host.connected=host.plugin=True
        for control in host.controls.values():control.mapped=True
        host._sync();ext._publish();assert ext._process is None
        self.model.par.Controller=clone;self.model.Sync();self.model.Flush();key=self.model.ActiveContext();self.key=key
        v=self.views[0];u=v.ext.InspectorView
        adapter=self.model.ext.InspectorModel.adapter
        count=adapter.ParameterDefinition;reads=[]
        def counted(*args):reads.append(args[0].get('id'));return count(*args)
        adapter.ParameterDefinition=counted
        try:
            for style in ('below','popup'):
                u.style=style
                for slot,expected in [(0,'Float'),(1,'Int'),(2,'Float'),(3,'Float'),(8,'Menu'),(9,'Toggle'),(10,'Pulse')]:
                    v.CloseEditor();v.Action('slot'+str(slot));v.Action('details_toggle')
                    native=u._native_definition
                    assert native['native']['style']==expected,(slot,native)
                    editor=u._editors[style=='popup'];section=editor.op('container_details')
                    assert editor.height==402 and section.height==218
                    assert section.op('container_readout').height==178
                    assert section.op('native_values').width==24 and section.op('native_definition').width==24
                    assert len(native['rows'])<=8
                    if slot==0:
                        assert native['native']['slider_range']==('0','1') and native['native']['clamp_limits']==('-2','3')
                        prior=len(reads);snapshot=u._native_definition
                        for _ in range(20):self.model.Sync();self.model.Flush();u._update_details()
                        assert len(reads)==prior and u._native_definition is snapshot
                        holder.par.Amount.default=.5
                        assert u._native_definition['native']['default']=='0.25'
                        assert v.Action('details_refresh') and u._native_definition['native']['default']=='0.5'
                        holder.par.Amount.default=.25;v.Action('details_refresh')
                    if slot==2:
                        assert native['native']['bind_master']==holder.path+'.Amount'
                        assert native['native']['bind_range'] and native['target']['comp']==holder.path
                    if slot==3:
                        assert native['native']['mode']=='EXPRESSION' and native['native']['expression']=='0.5'
                        assert native['native']['default_mode']=='EXPRESSION'
                    if slot==8:assert native['native']['menu_count']==20 and len(native['native']['menu_preview'])==8
                    v.Action('mapping_toggle');assert editor.height==312 and not u._details_open
                    v.Action('mapping_cancel');assert editor.height==178
            u.style='popup';v.CloseEditor();v.Action('slot0');v.Action('details_toggle')
            host.controls[('knob',1)].mapped=False  # This Value-traffic fixture has no hardware motor recipient.
            holder.par.Amount=.5;ext.onTargetValueChange(holder.par.Amount,.375);self.model.Sync();self.model.Flush()
            snapshot=u._native_definition;prior=len(reads)
            holder.par.Amount=.375;ext.onTargetValueChange(holder.par.Amount,.5);self.model.Sync();self.model.Flush()
            assert u._native_definition is snapshot and len(reads)==prior
            host.controls[('knob',1)].mapped=True;host._sync();ext._publish();self.model.Sync();self.model.Flush()
            viewport=u._editors[1].op('container_details/container_readout');u.DetailsScrollWheel(-1)
            assert viewport.panel.scrollv.val>0
            # Guards update displayed action enable state without metadata reads.
            for attr,target in [('learning',host),('touched',host.controls[('knob',1)])]:
                setattr(target,attr,True);host._sync();ext._publish();self.model.Sync();self.model.Flush()
                assert not u._editors[1].op('container_details/native_definition').par.enable.eval()
                assert not v.Action('native_definition')
                setattr(target,attr,False);host._sync();ext._publish();self.model.Sync();self.model.Flush()
            # Empty and callback states have no native action or business dispatch.
            v.CloseEditor();v.Action('slot15');v.Action('details_toggle')
            assert 'Unassigned' in u._native_definition['reason'] and not v.Action('native_values')
            self.callback=holder.copy(self.production,name='callback_controller');cb=self.callback;cb.Disconnect();cb.par.Followcomp=False
            cb.op('registration').text="def onRegister(controller):\n    return controller.BindControls([dict(kind='button',slot=1,id='fixture.native.callback',label='Callback',mode='toggle',button_type='toggle',on_change=lambda event:controller.store('fixture_event',True))],group_id='native.fixture.callback')\n"
            cb.par.Setupmode='callback';cb.Applybinding();self.model.par.Controller=cb;self.model.Sync();self.model.Flush()
            v.CloseEditor();v.Action('slot8');v.Action('details_toggle')
            assert 'Python callback' in u._native_definition['reason'] and not v.Action('native_definition')
            assert not cb.fetch('fixture_event',False)
        finally:adapter.ParameterDefinition=count
        self.model.par.Controller=clone;self.model.Sync();self.model.Flush()
        u.style='popup';v.CloseEditor();v.Action('slot0');v.Action('details_toggle')
        self.fixture_values={n:holder.par[n].eval() for n in ('Amount','Count','Choice','Enabled','Trigger','Alias','Driven')}
        self.result.update(type_readout_and_separate_native_mapping_ranges=True,bounded_menu_preview=True,
            default_edit_refresh_without_value_write=True,bind_assigned_owner_and_master=True,expression_default_modes_visible=True,
            snapshot_reads_on_open_refresh_not_value_traffic=True,learn_touch_actions_guarded=True,callback_empty_disabled=True,
            fixed_section_viewport_and_icons_both_styles=True,internal_wheel_scroll=True,no_callback_or_pulse_dispatch=True)
        assert not self.packets
        self.definition_dialog=op('/sys/TDDialogs/CompEditor');self.definition_was_open=self.definition_dialog.op('window').isOpen
        assert not self.definition_was_open,'Close the existing TD Definition dialog before testing'
        self.result['native_dialog_tests']=[]
        print('Native Advanced fixture passed; ready for one Values and one Definition dialog test')

    def Dialog(self,kind):
        assert kind in ('values','definition')
        v=self.views[0];u=v.ext.InspectorView
        assert self.model.par.Controller.eval()==self.clone
        self.clone.par.Followcomp=True;self.model.Sync();self.model.Flush()
        before=self.clone.GetLayoutContext()['key'];pane=self.pane.owner
        assert v.Action('native_'+kind)
        assert v.Action('native_'+kind)  # Native same-owner reuse is checked via OS inventory.
        self.result['native_dialog_tests'].append(dict(kind=kind,follow_on=True,two_dispatches=True,
            routing_preserved=self.clone.GetLayoutContext()['key']==before,pane_preserved=self.pane.owner==pane))
        print('Opened '+kind+' twice on the same fixture owner; inspect native window reuse then close it')

    def Finish(self):
        try:
            u=self.views[0].ext.InspectorView
            assert u._popup.contentHeight==402 and u._popup_host.height==402
            assert u._editors[1].y==0
            assert not self.definition_dialog.op('window').isOpen
            assert len(self.result['native_dialog_tests'])==2
            assert all(t['routing_preserved'] and t['pane_preserved'] for t in self.result['native_dialog_tests'])
            assert {n:self.holder.par[n].eval() for n in self.fixture_values}==self.fixture_values
            assert not self.packets
            self.result.update(native_programmatic_root_height_matches_window=True,fixture_values_no_midi_preserved=True)
        finally:self.Cleanup()
        assert self.production.GetControlCatalog()==self.before and self.production.fetch('layout_registry')==self.registry
        assert self.production.ext.RotoPythonExt._process.pid==self.pid and self.production.GetLayoutContext()['key']==self.routing
        assert self.model.ext.InspectorModel.adapter.Session()==self.session and self.model.Stats()['subscribers']==2
        assert not any(c.errors(recurse=True) for c in [self.production,self.model]+self.views)
        self.result.update(production_catalog_registry_routing_process_session_preserved=True,subscribers=2,errors=[])
        Path(project.folder+'/prototypes/inspector/advanced_verification.json').write_text(json.dumps(self.result,indent=2)+'\n')
        print(json.dumps(self.result))

    def Cleanup(self):
        for v,style in zip(self.views,self.styles):
            v.CloseEditor();v.op('window_editor').par.winclose.pulse();v.ext.InspectorView.style=style
        self.model.par.Controller=self.production;self.model.Sync();self.model.Flush()
        self.pane.owner=self.pane_owner
        if self.clone:self.clone.Disconnect()
        if self.callback:self.callback.Disconnect()
        if self.holder and self.holder.valid:self.holder.destroy()
        if hasattr(self.model.ext.InspectorModel,'_advanced_verification'):del self.model.ext.InspectorModel._advanced_verification

model=op('/inspector_model');phase=globals().get('phase','start')
if phase=='start':
    assert not hasattr(model.ext.InspectorModel,'_advanced_verification')
    probe=AdvancedProbe();model.ext.InspectorModel._advanced_verification=probe
    try:probe.Start()
    except Exception:probe.Cleanup();raise
elif phase=='finish':model.ext.InspectorModel._advanced_verification.Finish()
elif phase in ('values','definition'):model.ext.InspectorModel._advanced_verification.Dialog(phase)
elif phase=='stop':model.ext.InspectorModel._advanced_verification.Cleanup()
else:raise ValueError(phase)
