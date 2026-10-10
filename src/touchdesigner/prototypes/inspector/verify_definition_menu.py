"""Staged disconnected-controller Menu integration/UI checks; no physical MIDI."""
from pathlib import Path
import copy,json

class MenuLabelsProbe:
    def __init__(self):
        self.model=op('/inspector_model');self.production=self.model.par.Controller.eval()
        self.before=self.production.GetControlCatalog();self.registry=copy.deepcopy(self.production.fetch('layout_registry'))
        self.pid=self.production.ext.RotoPythonExt._process.pid
        self.views=[op('/inspector_below'),op('/inspector_popup')];self.styles=[v.ext.InspectorView.style for v in self.views]
        self.holder=self.clone=None;self.packets=[];self.result={}

    def Start(self):
        for v in self.views:v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        self.holder=self.production.parent().create(baseCOMP,'base_definition_menu_verification')
        self.holder.viewer=True;self.holder.nodeX=1750;self.holder.nodeY=-1000
        page=self.holder.appendCustomPage('Test')
        for name,count in [('Choice',3),('Longmenu',24)]:
            p=page.appendMenu(name)[0];p.menuNames=['n'+str(i) for i in range(count)]
            p.menuLabels=['Choice '+str(i+1) for i in range(count)];p.default='n0';p.val='n1'
        self.clone=self.holder.copy(self.production,name='controller');c=self.clone
        c.Disconnect();c.par.Followcomp=False;c.Applybinding();c.SelectLayout(c.CreateLayout('Menu labels fixture'))
        key=tuple(c.GetLayoutContext()['key']);self.key=key
        self.id=c.AssignParameter('knob',1,self.holder.par.Choice)['id']
        self.longid=c.AssignParameter('button',1,self.holder.par.Longmenu)['id']
        self.other=c.CreatePlugin(key[0],key[1],'Other Device');c.SelectPlugin(key[0],key[1],self.other)
        self.otherid=c.AssignParameter('knob',2,self.holder.par.Choice)['id']
        c.SelectPlugin(*key);e=c.ext.RotoPythonExt
        # In-memory protocol simulation only, never a real transport.
        e._host.send=lambda p:self.packets.append(tuple(p));e._host.connected=e._host.plugin=True
        for t in e._host.controls.values():t.mapped=True
        e._host._sync();e._publish();assert e._process is None
        self.model.par.Controller=c;self.model.Sync();self.model.Flush()
        t=e._host.controls['knob',1];old_identity=t.target_id;old_index=t.index
        labels=['Renamed A','Renamed B','Renamed C'];p=self.holder.par.Choice
        token=self.model.GetToken(key,0);d=self.model.DefinitionDraft(key,0,token)
        assert self.model.ApplyDefinition(key,0,token,d,dict(menuLabels=labels))
        t=e._host.controls['knob',1]
        assert t.target_id!=old_identity and t.index==old_index
        state=c.GetControlState(self.id)
        assert state['valid'] and not state['mapped'] and state['requires_relearn'] and state['menu_labels']==labels
        assert p.val=='n1' and p.default=='n0' and list(p.menuNames)==list(d['menu_names'])
        # Unrelated B1 registration retains its target/hash and mapping.
        assert c.GetControlState(self.longid)['mapped']
        inactive=(key[0],key[1],self.other)
        row=next(r for r in self.model.ext.InspectorModel.adapter.Read(inactive) if r['id']==self.otherid)
        assert row['requires_relearn'] and row['menu_labels']==labels
        proto=c.op('protocol').module
        ack=lambda identity,slot:proto.sysex(11,11,(old_index>>7,old_index&127,*proto.digest(identity,6),0,slot-1,0))
        e._receive_midi(ack(old_identity,1));e._publish()
        assert not c.GetControlState(self.id)['mapped'],'Old label hash acknowledged'
        # Matching ACK clears Needs re-LEARN; no hardware assertion is inferred.
        e._receive_midi(ack(t.target_id,1));e._publish()
        assert c.GetControlState(self.id)['mapped'] and not c.GetControlState(self.id)['requires_relearn']
        c.SelectPlugin(*inactive);state=c.GetControlState(self.otherid)
        assert state['requires_relearn'] and not state['mapped'] and state['menu_labels']==labels
        c.SelectPlugin(*key);self.model.Sync();self.model.Flush()
        self.result.update(active_binding_rebuilt=True,stable_id_index_names_default_value=True,
            unrelated_registration_preserved=True,inactive_device_requires_relearn=True,old_ack_rejected=True,matching_ack_clears_prompt=True)
        for i,v in enumerate(self.views):
            v.CloseEditor();v.ext.InspectorView.style='below' if i==0 else 'popup'
            v.Action('slot8');v.Action('details_toggle')
            assert v.Action('definition_edit') is not False
            assert len(v.ext.InspectorView._definition_patch()['menuLabels'])==24
            assert v.ext.InspectorView._editors[v.ext.InspectorView.style=='popup'].height==402
            v.op('base_draft').par.Nativemenulabel1='Cancelled'
            v.Action('definition_cancel');assert self.holder.par.Longmenu.menuLabels[0]=='Choice 1'
            v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        self.result['both_views_native_menu_drafts']=True
        # Keep 24-choice native draft visible for window/scroll/manual inspection.
        v=self.views[0];u=v.ext.InspectorView;u.style='popup'
        # Explicit fixture base: source reload/closed Size From Window caches
        # are asynchronous. This check isolates Menu layout from that lifecycle.
        u._popup.par.winh=178;u._popup_host.par.h=178;u._popup_size_pending=True
        u._cancel_popup_geometry()
        v.Action('slot8');v.Action('details_toggle');assert v.Action('definition_edit') is not False
        assert len(u._definition_patch()['menuLabels'])==24
        print('Menu labels fixture staged; 24-choice Popup open')

    def CheckGeometry(self):
        v=self.views[0];u=v.ext.InspectorView;editor=u._editors[1]
        assert v.op('window_editor').par.winh.eval()==402 and editor.height==402
        form=editor.op('container_details/container_readout/container_info/container_native/container_edit')
        assert form.height==706 and sum(form.op('menu_label'+str(i)).par.display.eval() for i in range(24))==24
        viewport=editor.op('container_details/container_readout');content=viewport.op('container_info');native=content.op('container_native')
        viewport.panel.scrollv=(native.height-viewport.height)/max(1,content.height-viewport.height)
        assert editor.height==402
        self.result.update(all_24_choices_bounded_scroll=True,window_height=402)
        print(json.dumps(self.result))

    def Finish(self):
        v=self.views[0]
        try:
            # Native UI Apply changes last label too; then Cancel writes nothing.
            if v.ext.InspectorView._definition_draft:
                v.op('base_draft').par.Nativemenulabel24='Last native choice'
                assert v.Action('definition_apply') is not False
            assert self.holder.par.Longmenu.menuLabels[-1]=='Last native choice'
            assert self.clone.GetControlState(self.longid)['requires_relearn']
            assert v.Action('definition_edit') is not False
            v.op('base_draft').par.Nativemenulabel1='Cancelled'
            v.Action('definition_cancel');assert self.holder.par.Longmenu.menuLabels[0]=='Choice 1'
            assert not v.op('base_draft').par.Nativemenulabel24.eval()
            self.result.update(native_24th_label_ui_apply=True,cancel_scrubs_without_write=True)
        finally:
            for v,style in zip(self.views,self.styles):
                v.CloseEditor();v.op('window_editor').par.winclose.pulse();v.ext.InspectorView.style=style
            self.model.par.Controller=self.production;self.model.Sync();self.model.Flush()
            if self.clone:self.clone.Disconnect()
            if self.holder:self.holder.destroy()
        assert self.production.GetControlCatalog()==self.before and self.production.fetch('layout_registry')==self.registry
        assert self.production.ext.RotoPythonExt._process.pid==self.pid
        assert self.model.Stats()['subscribers']==2
        assert not any(o.errors(recurse=True) for o in [self.production,self.model]+self.views)
        self.result.update(production_catalog_registry_process_preserved=True,fixture_removed=True,no_physical_midi=True,subscribers=2)
        Path(project.folder+'/prototypes/inspector/definition_menu_verification.json').write_text(json.dumps(self.result,indent=2)+'\n')
        print(json.dumps(self.result))
