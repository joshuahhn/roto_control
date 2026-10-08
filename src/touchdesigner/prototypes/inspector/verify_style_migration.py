"""Consolidated native Style integration on a disconnected, disposable controller."""
from pathlib import Path
import copy,json

class StyleMigrationProbe:
    def __init__(self):
        self.model=op('/inspector_model');self.production=self.model.par.Controller.eval()
        self.before=self.production.GetControlCatalog();self.registry=copy.deepcopy(self.production.fetch('layout_registry'))
        self.pid=self.production.ext.RotoPythonExt._process.pid
        self.views=[op('/inspector_below'),op('/inspector_popup')];self.styles=[v.ext.InspectorView.style for v in self.views]
        self.holder=self.clone=None;self.packets=[];self.result={}

    def model_ready(self):self.model.RefreshDefinitions();self.model.Sync();self.model.Flush()

    def ack(self,id,kind='knob',slot=1,index=None,identity=None):
        c=self.clone;e=c.ext.RotoPythonExt;key=e._collection.key(id)
        t=e._host.controls[key];proto=c.op('protocol').module
        index=t.index if index is None else index;identity=t.target_id if identity is None else identity
        e._receive_midi(proto.sysex(11,11,(index>>7,index&127,*proto.digest(identity,6),int(kind=='button'),slot-1,0)))
        e._publish();self.model_ready()

    def migrate(self,style):
        key=tuple(self.clone.GetLayoutContext()['key']);token=self.model.GetToken(key,0)
        draft=self.model.DefinitionDraft(key,0,token);patch=dict(style=style)
        preview=self.model.PreviewStyle(key,0,token,draft,patch);patch['style_value']=preview['value']
        assert self.model.ApplyDefinition(key,0,token,draft,patch)
        self.model_ready();return draft

    def Start(self):
        for v in self.views:v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        assert not op('/base_style_migration_verification')
        self.holder=root.create(baseCOMP,'base_style_migration_verification');self.holder.viewer=True
        self.holder.nodeX=1085;self.holder.nodeY=0
        page=self.holder.appendCustomPage('Fixture');page.appendToggle('Enabled');self.holder.par.Enabled=True
        p=page.appendFloat('Amount',label='Fixture amount',order=1)[0]
        p.default=2;p.val=3;p.normMin=-2;p.normMax=7;p.min=-4;p.max=8;p.clampMin=p.clampMax=True
        p.startSection=True;p.enableExpr='me.par.Enabled';p.help='Preserved native help'
        p.expr='99';p.mode=ParMode.CONSTANT;p.val=3
        p.defaultExpr='4';p.defaultMode=ParMode.CONSTANT;p.default=2
        page.appendFloat('Tail',order=2)[0].expr='me.par.Amount * 2'
        other=page.appendFloat('Other',order=3)[0];other.val=.375
        self.clone=self.holder.copy(self.production,name='controller');c=self.clone
        c.Disconnect();c.par.Followcomp=False;c.Applybinding();c.SelectLayout(c.CreateLayout('Style fixture'))
        self.key=tuple(c.GetLayoutContext()['key']);self.id=c.AssignParameter('knob',1,p)['id']
        self.otherid=c.AssignParameter('knob',3,other)['id']
        self.other=c.CreatePlugin(self.key[0],self.key[1],'Other Device')
        c.SelectPlugin(self.key[0],self.key[1],self.other)
        self.inactiveid=c.AssignParameter('knob',2,p)['id'];c.SelectPlugin(*self.key)
        e=c.ext.RotoPythonExt;manager=e._layout_manager();manager.capture(force=True)
        # A valid off-page registration to the same native target, fixture only.
        record=copy.deepcopy(next(t for t in manager.plugin()['targets'] if t['id']==self.id))
        record['id']='fixture.page.amount';record['index']=256
        record['identity']=next(c.op('controls').module.Controls([dict(record,parameter=p)]).specs())['identity']
        pages=list(c.fetch('page_targets',[]));pages.append(record);c.store('page_targets',pages)
        e._layout_dirty=True;manager.capture(force=True)
        self.page=copy.deepcopy(record)
        e._host.send=lambda packet:self.packets.append(tuple(packet));e._host.connected=e._host.plugin=True
        for t in e._host.controls.values():t.mapped=True
        e._host._sync();e._publish();assert e._process is None
        self.model.par.Controller=c;self.model_ready()
        module=self.model.op('base_commands/style_migration').module
        original=module.begin(p);original_value=p.val;reference=p;page_order=[q.name for q in self.holder.customPars]
        t=e._host.controls['knob',1];old_identity=t.target_id;old_index=t.index
        unrelated=copy.deepcopy(c.GetControlState(self.otherid));unrelated_target=e._host.controls['knob',3]
        # Other-controller registration must block before any native replacement.
        foreign=self.holder.copy(c,name='foreign');foreign.Disconnect()
        try:
            token=self.model.GetToken(self.key,0);d=self.model.DefinitionDraft(self.key,0,token)
            try:self.model.PreviewStyle(self.key,0,token,d,dict(style='Int'));raise AssertionError('Foreign owner accepted')
            except ValueError as error:assert 'Another controller' in str(error)
            assert module.begin(p)==original
        finally:foreign.destroy()
        self.migrate('Int');state=c.GetControlState(self.id)
        assert p.style=='Int' and p.isSamePar(reference) and p.index==original['fingerprint']['index']
        assert [q.name for q in self.holder.customPars]==page_order
        assert p.val==original_value and self.holder.par.Tail.eval()==6
        for field,value in original['metadata'].items():
            assert (getattr(p,field) or '')==(value or '') if field in ('expr','bindExpr','defaultExpr','defaultBindExpr','enableExpr') else getattr(p,field)==value,field
        assert state['valid'] and not state['mapped'] and state['requires_relearn']
        assert e._host.controls['knob',1].index==old_index and e._host.controls['knob',1].target_id!=old_identity
        assert c.GetControlState(self.otherid)==unrelated and e._host.controls['knob',3] is unrelated_target
        new_page=next(t for t in c.fetch('page_targets',[]) if t['id']==self.page['id'])
        assert new_page['identity']!=self.page['identity'] and new_page['index']==256
        self.ack(self.id,index=old_index,identity=old_identity);assert not c.GetControlState(self.id)['mapped']
        self.ack(self.id,index=256,identity=self.page['identity']);assert c.GetControlState(self.id)['id']==self.id and not c.GetControlState(self.id)['mapped']
        self.ack(self.id);assert c.GetControlState(self.id)['mapped'] and not c.GetControlState(self.id)['requires_relearn']
        active_int_identity=e._host.controls['knob',1].target_id
        self.ack(self.id,index=256,identity=new_page['identity'])
        assert e._collection.bindings['knob',1].id==self.page['id'] and p.style=='Int'
        assert c.GetControlState(self.page['id'])['mapped']
        self.ack(self.page['id'],index=old_index,identity=active_int_identity)
        assert e._collection.bindings['knob',1].id==self.id and c.GetControlState(self.id)['mapped']
        inactive=(self.key[0],self.key[1],self.other)
        row=next(r for r in self.model.ext.InspectorModel.adapter.Read(inactive) if r['id']==self.inactiveid)
        assert row['requires_relearn'] and row['parameter_style']=='Int'
        c.SelectPlugin(*inactive);self.model_ready()
        assert c.GetControlState(self.inactiveid)['requires_relearn']
        assert c.GetControlState(self.inactiveid)['parameter_style']=='Int'
        c.SelectPlugin(*self.key);self.model_ready();self.ack(self.id)
        self.migrate('Float');assert p.style=='Float' and p.val==3 and self.holder.par.Tail.eval()==6
        assert module.begin(p)==original
        assert c.GetControlState(self.id)['requires_relearn'];self.ack(self.id)
        # Inject one registry save failure after native replacement and unmap.
        save=manager.save;calls=[]
        def fail_once():
            calls.append(1)
            if len(calls)==1:raise RuntimeError('fixture registry write failed')
            return save()
        manager.save=fail_once
        try:
            try:self.migrate('Int');raise AssertionError('Injected failure accepted')
            except RuntimeError as error:assert 'original definition restored' in str(error),str(error)
        finally:manager.save=save
        assert module.begin(p)==original and p.val==3 and self.holder.par.Tail.eval()==6
        assert c.GetControlState(self.id)['parameter_style']=='Float' and c.GetControlState(self.id)['requires_relearn']
        assert c.op('base_targets/watch_knob1').par.active.eval();self.ack(self.id)
        self.result.update(lossless_float_int_and_reverse=True,native_identity_page_order_metadata_preserved=True,
            expression_and_existing_par_reference_preserved=True,other_controller_blocked=True,unrelated_binding_preserved=True,
            inactive_and_page_identities_rewritten=True,new_page_ack_recall_and_return=True,old_active_and_page_ack_rejected=True,matching_ack_clears_prompt=True,
            registry_failure_restores_native_and_binding=True,watcher_restored=True)
        # Each presentation uses the same inline menu and draft; selecting Int
        # previews only. Native mutation remains on Apply.
        for i,v in enumerate(self.views):
            v.CloseEditor();u=v.ext.InspectorView;u.style='below' if i==0 else 'popup'
            if u.style=='popup':
                u._popup.par.winh=178;u._popup_host.par.h=178;u._popup_size_pending=True;u._cancel_popup_geometry()
            v.Action('slot0');v.Action('details_toggle');assert v.Action('definition_edit') is not False
            assert v.Action('definition_style') is not False
            assert u._context_menu.items==('Float','Int')
            assert u.SelectContextItem(1)
            assert v.op('base_draft').par.Nativestyle.eval()=='Int' and p.style=='Float'
            assert u._style_preview and not u._style_preview.get('reason')
            v.Action('definition_cancel');assert p.style=='Float'
            assert not v.op('base_draft').par.Nativestyle.eval()
            v.CloseEditor();v.op('window_editor').par.winclose.pulse()
        self.result['fold_popup_inline_style_preview_cancel']=True
        v=self.views[0];u=v.ext.InspectorView;u.style='popup'
        u._popup.par.winh=178;u._popup_host.par.h=178;u._popup_size_pending=True;u._cancel_popup_geometry()
        v.Action('slot0');v.Action('details_toggle');assert v.Action('definition_edit') is not False
        self.result['fixture_ready_for_native_click']=True
        print('Style fixture staged: Float3/default2, original live controller untouched')

    def Check(self):
        u=self.views[0].ext.InspectorView
        assert u._editors[1].height==402 and u._popup.par.winh.eval()==402
        assert not any(o.errors(recurse=True) for o in (self.clone,self.model)+tuple(self.views))
        self.result['fixed_details_window']=402
        print(json.dumps(self.result))

    def Finish(self):
        v=self.views[0]
        try:
            p=self.holder.par.Amount
            if p.style=='Float':
                if v.ext.InspectorView._definition_draft is None:v.Action('definition_edit')
                v.op('base_draft').par.Nativestyle='Int';v.OnDefinitionDraftChange()
                assert v.Action('definition_apply') is not False
            assert p.style=='Int' and p.val==3 and self.holder.par.Tail.eval()==6
            assert self.clone.GetControlState(self.id)['requires_relearn']
            self.result['native_ui_style_apply']=True
        finally:
            for v,style in zip(self.views,self.styles):
                v.CloseEditor();v.op('window_editor').par.winclose.pulse();v.ext.InspectorView.style=style
            self.model.par.Controller=self.production;self.model_ready()
            if self.clone:self.clone.Disconnect()
            if self.holder:self.holder.destroy()
        assert self.production.GetControlCatalog()==self.before and self.production.fetch('layout_registry')==self.registry
        assert self.production.ext.RotoPythonExt._process.pid==self.pid
        assert self.model.Stats()['subscribers']==2
        assert not any(o.errors(recurse=True) for o in [self.production,self.model]+self.views)
        self.result.update(production_catalog_registry_process_preserved=True,fixture_removed=True,no_physical_midi=True,subscribers=2)
        Path(project.folder+'/prototypes/inspector/style_migration_verification.json').write_text(json.dumps(self.result,indent=2)+'\n')
        print(json.dumps(self.result))
